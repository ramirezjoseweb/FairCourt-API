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
from typing import Iterable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Household

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
def upsert_households(db: Session, codes: Iterable[str]) -> tuple[int, int]:
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

        exists = db.query(Household).filter(Household.code == code).first() # busca en la tabla Households una fila con el mismo codigo
        if exists:
            skipped += 1
            continue

        db.add(Household(code=code))
        created += 1

    db.commit()
    return created, skipped


# Función principal
def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de viviendas (lista blanca).") # Crea el parser de argumentos
    parser.add_argument("--codes", nargs="*", help="Lista de códigos de vivienda (separados por espacio).") # Permite pasarle los codigos por linea de comandos
    parser.add_argument("--file", help="Ruta a un fichero con un código por línea.") # Permite pasarle un fichero con los codigos
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
        created, skipped = upsert_households(db, unique_codes) # Inserta las viviendas en la base de datos
    finally:
        db.close() # Cierra la sesion de base de datos

    print(f"Seed completado. Creadas: {created}. Ya existían: {skipped}.") 

if __name__ == "__main__": 
    main()