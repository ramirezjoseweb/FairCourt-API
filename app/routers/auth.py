from __future__ import annotations  # Permite usar anotaciones de tipos modernas sin evaluarlas inmediatamente

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db  # Dependencia que proporciona una sesión de base de datos
from app.models import Household, User, AuthOTP  # Modelos ORM de la base de datos
from app.schemas import RequestOTPIn, VerifyOTPIn, TokenOut, MessageOut  # Esquemas Pydantic para validar entradas/salidas
from app.security import gen_otp, hash_secret, verify_secret, utcnow, create_access_token  # Utilidades de seguridad
from app.config import settings  # Configuración centralizada de la aplicación

# Router de FastAPI para agrupar endpoints de autenticación
router = APIRouter(prefix="/auth", tags=["auth"])


# Endpoint que genera un OTP para iniciar sesión o registrarse
@router.post("/request-otp", response_model=MessageOut)
# La ruta final será: POST /auth/request-otp
def request_otp(payload: RequestOTPIn, db: Session = Depends(get_db)):
    
    # 1) Validar vivienda (lista blanca)
    # Se comprueba que el código de vivienda existe en la tabla households
    # y que está activo.
    household = db.query(Household).filter(Household.code == payload.house_code).first()
    
    if not household or not household.is_active:
        raise HTTPException(
            status_code=404,
            detail="Código de vivienda no válido o inactivo."
        )

    # 2) Regla del sistema: solo puede existir un usuario por vivienda
    existing_user_for_house = db.query(User).filter(
        User.household_id == household.id
    ).first()

    if existing_user_for_house:
        # Si la vivienda ya tiene usuario, solo permitimos login con ese mismo email
        # Esto evita que otra persona registre la misma vivienda.
        if existing_user_for_house.email.lower() != payload.email.lower():
            raise HTTPException(
                status_code=409,
                detail="Esta vivienda ya tiene un usuario registrado con otro email."
            )
        
        # Re-login del usuario existente
        user = existing_user_for_house

    else:
        # Si la vivienda no tiene usuario todavía,
        # se crea el usuario asociado a esa vivienda.
        user = User(
            email=str(payload.email).lower(),
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
        email=user.email,
        otp_hash=otp_hash,
        expires_at=expires_at
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

    # Buscar el OTP más reciente de ese email que aún no haya sido usado
    otp_row = (
        db.query(AuthOTP)
        .filter(AuthOTP.email == email)
        .filter(AuthOTP.used_at.is_(None))  # OTP no utilizado
        .order_by(AuthOTP.created_at.desc())  # Obtener el más reciente
        .first()
    )

    if not otp_row:
        raise HTTPException(
            status_code=400,
            detail="No hay un OTP pendiente para este email."
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

    # Marcar el OTP como usado para evitar reutilización
    otp_row.used_at = now
    db.commit()

    # Generar token JWT de acceso para el usuario
    token, expires_at = create_access_token(subject=email)

    # Respuesta con el token de autenticación
    return {
        "access_token": token,
        "expires_at": expires_at
    }