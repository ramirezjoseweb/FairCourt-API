from __future__ import annotations 
from app.models import WaitlistEntry


from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_db
from app.models import User, Household
from sqlalchemy.orm import Session

router = APIRouter(tags=["users"]) # APIRouter hace que los endpoints tengan un tag

@router.get("/me") 
def read_me(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    ):
    """ Devuelve información básica del usuario autenticado
        Sirve para comprobar que el JWT funciona correctamente """

    household = db.query(Household).filter(Household.id == current_user.household_id).first() 

    active_waitlists = (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.household_id == current_user.household_id)
        .filter(WaitlistEntry.status == "WAITING")
        .all()
    )

    return {
        "id": current_user.id,
        "email": current_user.email,
        "household_id": current_user.household_id,
        "household_code": household.code if household else None,
        "strikes": household.strikes if household else None, 
        "suspended_until": household.suspended_until if household else None,
        "active_waitlists_count": len(active_waitlists),
        "active_waitlists": active_waitlists,   
    }
