from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CommunityPolicy


def get_community_policy(db: Session, community_id: int) -> CommunityPolicy:
    """Devuelve la política obligatoria de una comunidad."""
    policy = (
        db.query(CommunityPolicy)
        .filter(CommunityPolicy.community_id == community_id)
        .first()
    )
    if not policy:
        raise RuntimeError(
            f"La comunidad {community_id} no tiene una política configurada."
        )
    return policy
