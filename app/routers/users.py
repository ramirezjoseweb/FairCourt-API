from __future__ import annotations 

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models import User

router = APIRouter(tags=["users"]) # APIRouter hace que los endpoints tengan un tag

@router.get("/me") 
def read_me(current_user: User = Depends(get_current_user)):
    """ Devuelve información básica del usuario autenticado
        Sirve para comprobar que el JWT funciona correctamente """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "household_id": current_user.household_id
    }
