"""
seed.py

Script de inicialización de datos ("seed") para cargar la lista blanca de viviendas.

Uso típico:
- Se ejecuta manualmente por el mantenedor del sistema.
- Inserta códigos de vivienda en la tabla households si no existen.
- No crea usuarios ni reservas.

Ejemplos:
    python seed.py --codes A1 A2 A3
    python seed.py --file households.txt
"""

from __future__ import annotations

import argparse
import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Community, Household, normalize_household_code

# Función para leer los códigos del fichero
def parse_codes_file(path: str) -> list[str]: 
    """Lee un fichero con un código por línea, ignorando líneas vacías y comentarios (#)."""
    codes: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            codes.append(s)
    return codes

# Función para insertar las viviendas en la base de datos
def get_or_create_community(
    db: Session,
    slug: str,
    name: str | None = None,
) -> Community:
    normalized_slug = slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized_slug):
        raise SystemExit(
            "El identificador de comunidad solo admite minúsculas, números y guiones."
        )

    community = (
        db.query(Community)
        .filter(Community.slug == normalized_slug)
        .first()
    )
    if community:
        return community
    if not name:
        raise SystemExit(
            f"La comunidad '{normalized_slug}' no existe. "
            "Usa --community-name para crearla explícitamente."
        )

    community = Community(slug=normalized_slug, name=name.strip())
    db.add(community)
    db.commit()
    db.refresh(community)
    return community


def upsert_households(
    db: Session,
    community: Community,
    codes: Iterable[str],
) -> tuple[int, int]:
    """
    Inserta viviendas nuevas si el código no existe.

    Returns:
        (created, skipped)
    """
    created = 0
    skipped = 0

    for code in codes:
        code = code.strip()
        if not code:
            continue

        exists = (
            db.query(Household)
            .filter(Household.community_id == community.id)
            .filter(Household.code_normalized == normalize_household_code(code))
            .first()
        )
        if exists:
            skipped += 1
            continue

        db.add(Household(community_id=community.id, code=code))
        created += 1

    db.commit()
    return created, skipped


# Función principal
def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de viviendas (lista blanca).") # Crea el parser de argumentos
    parser.add_argument("--codes", nargs="*", help="Lista de códigos de vivienda (separados por espacio).") # Permite pasarle los codigos por linea de comandos
    parser.add_argument("--file", help="Ruta a un fichero con un código por línea.") # Permite pasarle un fichero con los codigos
    parser.add_argument(
        "--community",
        default="faircourt",
        help="Identificador de la comunidad propietaria de las viviendas.",
    )
    parser.add_argument(
        "--community-name",
        help="Nombre visible; crea la comunidad si aún no existe.",
    )
    args = parser.parse_args()

    codes: list[str] = []

    if args.file:
        codes.extend(parse_codes_file(args.file)) # Añade los codigos del fichero a la lista

    if args.codes:
        codes.extend(args.codes) # Añade los codigos de la linea de comandos a la lista


    # Eliminar duplicados manteniendo orden
    seen = set()
    unique_codes = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            unique_codes.append(c) # Si el codigo no esta en seen, se añade a seen y a unique_codes

    if not unique_codes:
        raise SystemExit("No has proporcionado códigos. Usa --codes o --file.") # Si no se han proporcionado codigos, se lanza una excepcion

    db = SessionLocal() # Crea una sesion de base de datos
    try:
        community = get_or_create_community(
            db,
            args.community,
            args.community_name,
        )
        created, skipped = upsert_households(
            db,
            community,
            unique_codes,
        ) # Inserta las viviendas en la base de datos
    finally:
        db.close() # Cierra la sesion de base de datos

    print(
        f"Seed completado para {community.name} ({community.slug}). "
        f"Creadas: {created}. Ya existían: {skipped}."
    )

if __name__ == "__main__": 
    main()
