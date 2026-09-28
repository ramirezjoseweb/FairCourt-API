import argparse

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, UserRole


def normalize_email(value: str) -> str:
    try:
        return validate_email(value, check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


def create_platform_admin(db: Session, email: str) -> bool:
    normalized_email = normalize_email(email)
    existing = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email.lower())
        .one_or_none()
    )

    if existing is not None:
        if existing.role != UserRole.PLATFORM_ADMIN.value:
            raise ValueError(
                "Ya existe una cuenta con ese correo y no es administradora. "
                "No se ha modificado su rol."
            )
        if not existing.is_active:
            raise ValueError("La cuenta administradora existe, pero esta desactivada.")
        return False

    db.add(
        User(
            email=normalized_email,
            role=UserRole.PLATFORM_ADMIN.value,
            is_active=True,
            community_id=None,
            household_id=None,
        )
    )
    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea un administrador de plataforma sin elevar cuentas existentes."
    )
    parser.add_argument("--email", required=True, help="Correo del administrador")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        created = create_platform_admin(db, args.email)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if created:
        print("Administrador de plataforma creado.")
    else:
        print("El administrador de plataforma ya existia y esta activo.")


if __name__ == "__main__":
    main()
