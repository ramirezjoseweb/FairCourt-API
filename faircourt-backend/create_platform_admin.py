"""Crea de forma explícita la identidad global del administrador de FairCourt."""

from __future__ import annotations

import argparse

from pydantic import EmailStr, TypeAdapter

from app.db import SessionLocal
from app.models import User, UserRole


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()

    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            if existing.role == UserRole.PLATFORM_ADMIN.value:
                print(f"El administrador {email} ya existe.")
                return
            raise SystemExit(
                "Ese correo ya pertenece a una vivienda. Usa un correo "
                "administrativo diferente."
            )
        db.add(
            User(
                email=email,
                role=UserRole.PLATFORM_ADMIN.value,
                is_active=True,
                community_id=None,
                household_id=None,
            )
        )
        db.commit()
    print(f"Administrador de plataforma creado: {email}")


if __name__ == "__main__":
    main()
