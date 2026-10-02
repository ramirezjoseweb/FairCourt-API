"""Provision the two real communities on a newly migrated production database."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Community, CommunityPolicy, Household, User


COMMUNITIES = (
    ("gran-parque", "Gran Parque"),
    ("parque-venecia", "Parque Venecia"),
)


def provision_communities(db: Session) -> None:
    if settings.APP_ENV != "production":
        raise RuntimeError("This bootstrap runs only with APP_ENV=production.")

    legacy = db.query(Community).filter(Community.slug == "faircourt").one_or_none()
    if legacy and legacy.is_active:
        has_households = db.query(Household.id).filter(Household.community_id == legacy.id).first()
        has_users = db.query(User.id).filter(User.community_id == legacy.id).first()
        if has_households or has_users:
            raise RuntimeError("The legacy FairCourt community contains users or households; review it manually.")
        legacy.is_active = False

    for slug, name in COMMUNITIES:
        existing = db.query(Community).filter(Community.slug == slug).one_or_none()
        if existing:
            if existing.name != name:
                raise RuntimeError(f"Community {slug} has an unexpected name; review it manually.")
            continue
        db.add(Community(slug=slug, name=name, policy=CommunityPolicy()))

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        provision_communities(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print("Gran Parque and Parque Venecia are ready; the empty legacy demo is inactive.")


if __name__ == "__main__":
    main()
