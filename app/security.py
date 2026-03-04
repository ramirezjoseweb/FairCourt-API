from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from jose import jwt # jwt es una librería para crear tokens
from passlib.context import CryptContext # passlib es una librería para hashear contraseñas 

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # bcrypt es un algoritmo de hashing de contraseñas 

def utcnow() -> datetime:
    # UTC "naive" para compatibilidad con SQLite
    return datetime.utcnow()

def gen_otp(length: int) -> str: # gen_otp es una función que genera un código OTP de una longitud determinada
    # OTP numérico
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length)) # secrets.choice es una función que elige un elemento aleatorio de una secuencia 

def hash_secret(value: str) -> str: # hash_secret es una función que hashea una contraseña
    return pwd_context.hash(value)

def verify_secret(value: str, hashed: str) -> bool: # verify_secret es una función que verifica si una contraseña es correcta
    return pwd_context.verify(value, hashed)

def create_access_token(subject: str) -> tuple[str, datetime]: # create_access_token es una función que crea un token de acceso
    """
    Crea un JWT donde 'sub' identifica al usuario (aquí usamos el email).
    """
    expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES) # timedelta es una función que crea una diferencia de tiempo
    payload = {"sub": subject, "exp": expire} # payload es un diccionario que contiene la información del token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG) # jwt.encode es una función que codifica el payload en un token
    return token, expire