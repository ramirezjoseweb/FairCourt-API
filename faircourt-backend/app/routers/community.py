from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_resident
from app.models import User
from app.schemas import CommunityPolicyOut
from app.services.policies import get_community_policy


router = APIRouter(prefix="/community", tags=["community"])


@router.get("/policy", response_model=CommunityPolicyOut)
def read_community_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_resident),
):
    """Devuelve únicamente la política de la comunidad autenticada."""
    return get_community_policy(db, current_user.community_id)
