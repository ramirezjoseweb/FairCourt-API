from __future__ import annotations

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer 
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User, UserRole

# Esquema Bearer para que FastAPI/Swagger sepan que usamos Authorization: Bearer <token>
bearer_scheme = HTTPBearer() # crea el boton Authorize en Swagger/OpenAPI

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), # Dependencia que proporciona las credenciales del header Authorization: Bearer <token>
    db: Session = Depends(get_db), # Dependencia que proporciona una sesión de base de datos
) -> User: 
    """ Valida el JWT enviado en la cabecera de Authorizatation y devuelve el usuario autenticado asociado al claim 'sub' (email) 
        Flujo: 
        1. Extrae el token del header Authorization: Bearer <token> 
        2. Decodifica el JWT usando la clave secreta de la aplicación 
        3. Valida que el token sea válido
        4. Busca el usuario en la base de datos usando el email del claim 'sub'
        5. Devuelve el usuario si existe, si no lanza una excepción """

    token = credentials.credentials # token coge las credenciales del header Authorization: Bearer <token>

    # Excepción que se lanza si el token es inválido
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,  # status.HTTP_401_UNAUTHORIZED es una constante que representa el código de estado 401 Unauthorized
        detail="Credenciales de autorización no válidas.", 
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    
    try: # este try-except se encarga de capturar los errores que puedan ocurrir al decodificar el token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, # esta es la clave secreta que se usa para firmar el token
            algorithms=[settings.JWT_ALG], # este es el algoritmo que se usa para firmar el token
        ) 
        email = payload.get("sub") # el claim 'sub' es el email del usuario
        token_community_id = payload.get("community_id")
        token_role = payload.get("role", UserRole.RESIDENT.value)
        if not email: # si no hay email en el claim 'sub' se lanza una excepción
            raise unauthorized
    except JWTError: # si hay un error al decodificar el token se lanza una excepción
        raise unauthorized
    
    user = db.query(User).filter(User.email == email).first()
    if not user: 
        raise unauthorized
    if not user.is_active or user.role != token_role:
        raise unauthorized

    if user.role == UserRole.PLATFORM_ADMIN.value:
        if (
            token_community_id is not None
            or user.community_id is not None
            or user.household_id is not None
        ):
            raise unauthorized
        return user

    if user.role != UserRole.RESIDENT.value:
        raise unauthorized
    if token_community_id != user.community_id:
        raise unauthorized
    if not user.community or not user.community.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La comunidad no está activa.",
        )
    if not user.household or user.household.community_id != user.community_id:
        raise unauthorized
    return user


def require_resident(current_user: User = Depends(get_current_user)) -> User:
    """Impide que una identidad administrativa use operaciones residenciales."""
    if current_user.role != UserRole.RESIDENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere una cuenta residencial.",
        )
    return current_user


def require_platform_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Autoriza exclusivamente al administrador global de FairCourt."""
    if current_user.role != UserRole.PLATFORM_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere permisos de administrador de plataforma.",
        )
    return current_user
