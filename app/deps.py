from __future__ import annotations

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

# Esquema Bearer para que FastAPI/Swagger sepan que usamos Authorization: Bearer <token>
bearer_scheme = HTTPBearer() 

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
    db: Session = Depends(get_db),
) -> User: 
    """ Valida el JWT enviado en la cabecera de Authorizatation y devuelve el usuario autenticado asociado al claim 'sub' (email) 
        Flujo: 
        1. Extrae el token del header Authorization: Bearer <token> 
        2. Decodifica el JWT usando la clave secreta de la aplicación 
        3. Valida que el token sea válido
        4. Busca el usuario en la base de datos usando el email del claim 'sub'
        5. Devuelve el usuario si existe, si no lanza una excepción """

    token = credentials.credentials

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Credenciales de autorización no válidas.", 
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try: 
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALG], 
        ) 
        email = payload.get("sub") 
        if not email: 
            raise unauthorized
    except JWTError: 
        raise unauthorized
    
    user = db.query(User).filter(User.email == email).first() 
    if not user: 
        raise unauthorized
    return user  