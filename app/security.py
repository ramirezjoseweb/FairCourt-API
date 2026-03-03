from __future__ import annotations

import secrets # Módulo para generar números aleatorios criptográficamente seguros
from datetime import datetime, timedelta, timezone

from jose import jwt # Módulo para generar tokens JWT
from passlib.context import CryptContext # Módulo para hashear contraseñas

from .config import settings

# Configuración de passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para obtener la fecha y hora actual en UTC
def utcnow() -> datetime: 
    return datetime.now(timezone.utc) 

# Generación de OTPq
def gen_otp(length: int) -> str: 
    # OTP numérico
    digits = "0123456789" 
    return "".join(secrets.choice(digits) for _ in range(length)) # Genera un OTP de la longitud especificada

# Generación de hash de secretos usando Bcrypt
def hash_secret(value: str) -> str: 
    return pwd_context.hash(value)

# Verificación de secretos
def verify_secret(value: str, hashed: str) -> bool: 
    return pwd_context.verify(value, hashed)

# Creación de tokens JWT  
def create_access_token(subject: str) -> tuple[str, datetime]: 
    """
    Genera un token de acceso JWT (JSON Web Token) para autenticación.

    Este token incluye:
    - "sub" (subject): identificador del usuario (en este proyecto, el email).
    - "exp" (expiration): fecha y hora de expiración del token.

    El token se firma utilizando la clave secreta definida en la configuración
    de la aplicación y el algoritmo especificado en `settings.JWT_ALG`.

    Args:
        subject (str): Identificador único del usuario (normalmente el email).

    Returns:
        tuple[str, datetime]: 
            - El token JWT generado en formato string.
            - La fecha y hora exacta en la que el token expirará.
    """
    expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return token, expire


