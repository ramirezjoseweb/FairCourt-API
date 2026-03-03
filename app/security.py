from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def gen_otp(length: int) -> str:
    # OTP numérico
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))

def hash_secret(value: str) -> str:
    return pwd_context.hash(value)

def verify_secret(value: str, hashed: str) -> bool:
    return pwd_context.verify(value, hashed)

def create_access_token(subject: str) -> tuple[str, datetime]:
    """
    Crea un JWT donde 'sub' identifica al usuario (aquí usamos el email).
    """
    expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return token, expire