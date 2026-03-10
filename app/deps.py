from __future__ import annotations

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer 
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

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
        if not email: # si no hay email en el claim 'sub' se lanza una excepción
            raise unauthorized
    except JWTError: # si hay un error al decodificar el token se lanza una excepción
        raise unauthorized
    
    user = db.query(User).filter(User.email == email).first() # esto busca el usuario en la base de datos usando el email del claim 'sub'
    if not user: 
        raise unauthorized
    return user  