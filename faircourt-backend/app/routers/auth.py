from __future__ import annotations  # Permite usar anotaciones de tipos modernas sin evaluarlas inmediatamente


from sqlalchemy.sql.functions import current_user
from app.services.audit import log_event

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db  # Dependencia que proporciona una sesión de base de datos
from app.models import (
    AuthOTP,
    Community,
    Household,
    User,
    UserRole,
    normalize_household_code,
)
from app.schemas import RequestOTPIn, VerifyOTPIn, TokenOut, MessageOut  # Esquemas Pydantic para validar entradas/salidas
from app.security import gen_otp, hash_secret, verify_secret, utcnow, create_access_token  # Utilidades de seguridad
from app.config import settings  # Configuración centralizada de la aplicación

# Router de FastAPI para agrupar endpoints de autenticación
router = APIRouter(prefix="/auth", tags=["auth"])


# Endpoint que genera un OTP para iniciar sesión o registrarse
@router.post("/request-otp", response_model=MessageOut)
# La ruta final será: POST /auth/request-otp
def request_otp(payload: RequestOTPIn, db: Session = Depends(get_db)):
    community = (
        db.query(Community)
        .filter(Community.slug == payload.community_slug.strip().lower())
        .filter(Community.is_active.is_(True))
        .first()
    )
    if not community:
        raise HTTPException(status_code=404, detail="Comunidad no válida o inactiva.")

    # 1) Validar vivienda (lista blanca)
    # Se comprueba que el código de vivienda existe en la tabla households
    # y que está activo.
    household = (
        db.query(Household)
        .filter(Household.community_id == community.id)
        .filter(Household.code_normalized == normalize_household_code(payload.house_code))
        .first()
    )
    
    if not household or not household.is_active:
        raise HTTPException(
            status_code=404,
            detail=f"Código de vivienda: {payload.house_code} no válido o inactivo."
        )

    # 2) Regla del sistema: solo puede existir un usuario por vivienda
    existing_user_for_house = db.query(User).filter(
        User.household_id == household.id,
        User.community_id == community.id,
        User.role == UserRole.RESIDENT.value,
    ).first()

    if existing_user_for_house:
        if not existing_user_for_house.is_active:
            raise HTTPException(status_code=403, detail="La cuenta está desactivada.")
        # Si la vivienda ya tiene usuario, solo permitimos login con ese mismo email
        # Esto evita que otra persona registre la misma vivienda.
        if existing_user_for_house.email.lower() != payload.email.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Esta vivienda: {payload.house_code} ya tiene un usuario registrado con otro email: {existing_user_for_house.email}."
            )
        
        # Re-login del usuario existente
        user = existing_user_for_house

    else:
        existing_user_for_email = (
            db.query(User)
            .filter(User.email == str(payload.email).lower())
            .first()
        )
        if existing_user_for_email:
            raise HTTPException(
                status_code=409,
                detail="El correo ya está asociado a otra cuenta.",
            )

        # Si la vivienda no tiene usuario todavía,
        # se crea el usuario asociado a esa vivienda.
        user = User(
            email=str(payload.email).lower(),
            role=UserRole.RESIDENT.value,
            is_active=True,
            community_id=community.id,
            household_id=household.id
        )

        db.add(user)
        db.commit()
        db.refresh(user)  # Recarga el objeto para obtener el ID generado por la BD

    # 3) Generar OTP y guardarlo en base de datos de forma segura
    # Se genera el código OTP (por ejemplo 6 dígitos)
    otp = gen_otp(settings.OTP_LENGTH)

    # El OTP no se guarda en texto plano, se guarda su hash
    otp_hash = hash_secret(otp)

    # Tiempo de expiración del OTP
    expires_at = utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)

    # Se crea el registro de autenticación
    record = AuthOTP(
        community_id=community.id,
        email=user.email,
        purpose="RESIDENT",
        otp_hash=otp_hash,
        expires_at=expires_at
    )

    # Registrar el evento de solicitud de OTP
    log_event(
        db, 
        event="OTP_REQUESTED",
        household_id=household.id,
        user_id=user.id if user else None, 
        metadata={"email": user.email},
    )

    db.add(record)
    db.commit()

    # 4) Modo desarrollo:
    # El OTP se imprime en consola para poder probar el sistema
    # En producción se enviaría por email, SMS o Telegram.
    if settings.DEV_PRINT_OTP:
        print(f"[DEV OTP] Email={user.email} OTP={otp} (expira {expires_at.isoformat()})")

    # Respuesta del endpoint
    return {
        "message": "OTP generado. Revisa tu email (modo dev: mira la consola del servidor)."
    }

    


# Endpoint que verifica el OTP y devuelve el token de autenticación
@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: VerifyOTPIn, db: Session = Depends(get_db)):

    # Normalizar el email para evitar problemas de mayúsculas/minúsculas
    email = str(payload.email).lower()
    community = (
        db.query(Community)
        .filter(Community.slug == payload.community_slug.strip().lower())
        .filter(Community.is_active.is_(True))
        .first()
    )
    if not community:
        raise HTTPException(status_code=404, detail="Comunidad no válida o inactiva.")

    # Buscar el OTP más reciente de ese email que aún no haya sido usado
    otp_row = (
        db.query(AuthOTP)
        .filter(AuthOTP.email == email)
        .filter(AuthOTP.community_id == community.id)
        .filter(AuthOTP.purpose == "RESIDENT")
        #.filter(AuthOTP.used_at.is_(None))  # OTP no utilizado
        .order_by(AuthOTP.created_at.desc())  # Obtener el más reciente
        .first()
    )

    if not otp_row:
        raise HTTPException(
            status_code=400,
            detail="No hay un OTP pendiente para este email."
        )

    # Si se reutiliza el otp se bloquea la cuenta
    if otp_row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP ya utilizado."
        )

    # Comprobar si el OTP ha expirado
    now = utcnow()
    if otp_row.expires_at < now:
        raise HTTPException(
            status_code=400,
            detail="OTP expirado. Solicita uno nuevo."
        )

    # Verificar que el OTP introducido coincide con el hash almacenado
    if not verify_secret(payload.otp, otp_row.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP incorrecto."
        )

    # Obtener el usuario asociado al email
    user = (
        db.query(User)
        .filter(User.email == email)
        .filter(User.community_id == community.id)
        .filter(User.role == UserRole.RESIDENT.value)
        .filter(User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Cuenta no válida para esta comunidad.")
    
    # Registrar el evento de verificación de OTP
    log_event(
        db, 
        event="OTP_VERIFIED", 
        user_id=user.id,
        household_id=user.household_id, 
        metadata={"email": user.email}
    )
    db.commit()

    # Marcar el OTP como usado para evitar reutilización
    otp_row.used_at = now
    db.commit()

    # Generar token JWT de acceso para el usuario
    token, expires_at = create_access_token(
        subject=email,
        community_id=community.id,
        role=UserRole.RESIDENT.value,
    )

    # Respuesta con el token de autenticación
    return {
        "access_token": token,
        "expires_at": expires_at
    }

