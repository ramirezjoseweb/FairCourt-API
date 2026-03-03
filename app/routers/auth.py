from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Household, User, AuthOTP
from app.schemas import RequestOTPIn, VerifyOTPIn, TokenOut, MessageOut
from app.security import gen_otp, hash_secret, verify_secret, utcnow, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-otp", response_model=MessageOut)
def request_otp(payload: RequestOTPIn, db: Session = Depends(get_db)):
    # 1) Validar vivienda (lista blanca)
    household = db.query(Household).filter(Household.code == payload.house_code).first()
    if not household or not household.is_active:
        raise HTTPException(status_code=404, detail="Código de vivienda no válido o inactivo.")

    # 2) Regla: 1 usuario por vivienda
    existing_user_for_house = db.query(User).filter(User.household_id == household.id).first()

    if existing_user_for_house:
        # Si ya hay usuario, solo permitimos re-login con el mismo email
        if existing_user_for_house.email.lower() != payload.email.lower():
            raise HTTPException(
                status_code=409,
                detail="Esta vivienda ya tiene un usuario registrado con otro email."
            )
        user = existing_user_for_house
    else:
        # Crear usuario por primera vez
        user = User(email=str(payload.email).lower(), household_id=household.id)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3) Generar OTP y guardarlo hasheado
    otp = gen_otp(settings.OTP_LENGTH)
    otp_hash = hash_secret(otp)

    expires_at = utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)
    record = AuthOTP(email=user.email, otp_hash=otp_hash, expires_at=expires_at)
    db.add(record)
    db.commit()

    # 4) DEV: imprimir OTP en consola (en prod, enviar por email/telegram)
    if settings.DEV_PRINT_OTP:
        print(f"[DEV OTP] Email={user.email} OTP={otp} (expira {expires_at.isoformat()})")

    return {"message": "OTP generado. Revisa tu email (modo dev: mira la consola del servidor)."}


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: VerifyOTPIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()

    # Buscar el OTP más reciente no usado de ese email
    otp_row = (
        db.query(AuthOTP)
        .filter(AuthOTP.email == email)
        .filter(AuthOTP.used_at.is_(None))
        .order_by(AuthOTP.created_at.desc())
        .first()
    )

    if not otp_row:
        raise HTTPException(status_code=400, detail="No hay un OTP pendiente para este email.")

    now = utcnow()
    if otp_row.expires_at < now:
        raise HTTPException(status_code=400, detail="OTP expirado. Solicita uno nuevo.")

    if not verify_secret(payload.otp, otp_row.otp_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP incorrecto.")

    # Marcar OTP como usado
    otp_row.used_at = now
    db.commit()

    # Emitir token
    token, expires_at = create_access_token(subject=email)
    return {"access_token": token, "expires_at": expires_at}