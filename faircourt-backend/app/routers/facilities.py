from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Facility, User
from app.schemas import FacilityOut


router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityOut])
def list_facilities(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Devuelve el catálogo activo, con Pádel y Tenis en primer lugar."""
    return (
        db.query(Facility)
        .filter(Facility.community_id == _current_user.community_id)
        .filter(Facility.is_active.is_(True))
        .order_by(Facility.priority.asc(), Facility.name.asc())
        .all()
    )
