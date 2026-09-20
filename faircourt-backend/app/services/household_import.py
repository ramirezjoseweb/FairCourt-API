from __future__ import annotations

import csv
import io
import unicodedata
from collections import Counter
from pathlib import PurePath

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session, joinedload

from app.models import Household, User, UserRole, normalize_household_code
from app.services.audit import log_admin_event


MAX_ROWS = 2_000
ALLOWED_HEADERS = {"codigo_vivienda", "correo", "activa"}
TRUE_VALUES = {"1", "si", "true", "activa", "activo"}
FALSE_VALUES = {"0", "no", "false", "inactiva", "inactivo"}
EMAIL_ADAPTER = TypeAdapter(EmailStr)


class HouseholdCsvError(ValueError):
    pass


def _normalize_header(value: str) -> str:
    value = unicodedata.normalize("NFD", value.strip().lstrip("\ufeff").lower())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return value.replace(" ", "_")


def _parse_active(value: str) -> tuple[bool, str | None]:
    normalized = unicodedata.normalize("NFD", value.strip().lower())
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    if not normalized:
        return True, None
    if normalized in TRUE_VALUES:
        return True, None
    if normalized in FALSE_VALUES:
        return False, None
    return True, "El valor de activa debe ser sí/no, true/false o 1/0."


def preview_household_csv(
    db: Session,
    community_id: int,
    csv_text: str,
) -> dict:
    text = csv_text.lstrip("\ufeff")
    try:
        dialect = csv.Sniffer().sniff(text[:4_096], delimiters=",;")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise HouseholdCsvError("El archivo no contiene una cabecera.")

    headers = [_normalize_header(header or "") for header in reader.fieldnames]
    if len(headers) != len(set(headers)):
        raise HouseholdCsvError("La cabecera contiene columnas repetidas.")
    unknown_headers = set(headers) - ALLOWED_HEADERS
    if unknown_headers:
        raise HouseholdCsvError(
            "Columnas no reconocidas: " + ", ".join(sorted(unknown_headers)) + "."
        )
    if "codigo_vivienda" not in headers:
        raise HouseholdCsvError("Falta la columna obligatoria codigo_vivienda.")

    header_map = dict(zip(reader.fieldnames, headers, strict=True))
    parsed_rows: list[dict] = []
    for line, source_row in enumerate(reader, start=2):
        if source_row.get(None):
            raise HouseholdCsvError(
                f"La línea {line} contiene más columnas de las indicadas en la cabecera."
            )
        row = {
            header_map[key]: (value or "").strip()
            for key, value in source_row.items()
            if key is not None
        }
        if not any(row.values()):
            continue
        if len(parsed_rows) >= MAX_ROWS:
            raise HouseholdCsvError(f"El archivo no puede superar {MAX_ROWS} viviendas.")

        code = " ".join(row.get("codigo_vivienda", "").split())
        email = row.get("correo", "").strip().lower() or None
        is_active, active_error = _parse_active(row.get("activa", ""))
        errors: list[str] = []
        if not code:
            errors.append("El código de vivienda está vacío.")
        elif len(code) > 50:
            errors.append("El código de vivienda supera 50 caracteres.")
        if email:
            try:
                email = str(EMAIL_ADAPTER.validate_python(email)).lower()
            except ValidationError:
                errors.append("El correo no es válido.")
        if active_error:
            errors.append(active_error)
        parsed_rows.append(
            {
                "line": line,
                "code": code,
                "code_normalized": normalize_household_code(code) if code else "",
                "email": email,
                "is_active": is_active,
                "errors": errors,
            }
        )

    if not parsed_rows:
        raise HouseholdCsvError("El archivo no contiene viviendas.")

    code_counts = Counter(row["code_normalized"] for row in parsed_rows if row["code_normalized"])
    email_counts = Counter(row["email"] for row in parsed_rows if row["email"])
    for row in parsed_rows:
        if row["code_normalized"] and code_counts[row["code_normalized"]] > 1:
            row["errors"].append("El código está repetido dentro del archivo.")
        if row["email"] and email_counts[row["email"]] > 1:
            row["errors"].append("El correo está repetido dentro del archivo.")

    normalized_codes = {row["code_normalized"] for row in parsed_rows if row["code_normalized"]}
    existing_codes = {
        value
        for (value,) in (
            db.query(Household.code_normalized)
            .filter(Household.community_id == community_id)
            .filter(Household.code_normalized.in_(normalized_codes))
            .all()
        )
    }
    emails = {row["email"] for row in parsed_rows if row["email"]}
    existing_emails = {
        value.lower()
        for (value,) in db.query(User.email).filter(User.email.in_(emails)).all()
    }

    output_rows = []
    for row in parsed_rows:
        if row["errors"]:
            status = "error"
            message = " ".join(row["errors"])
        elif row["code_normalized"] in existing_codes:
            status = "existing"
            message = "Ya existe y no se modificará."
        elif row["email"] in existing_emails:
            status = "error"
            message = "El correo ya está asociado a otra cuenta."
        else:
            status = "new"
            message = None
        output_rows.append(
            {
                "line": row["line"],
                "code": row["code"],
                "email": row["email"],
                "is_active": row["is_active"],
                "status": status,
                "message": message,
            }
        )

    new_count = sum(row["status"] == "new" for row in output_rows)
    existing_count = sum(row["status"] == "existing" for row in output_rows)
    error_count = sum(row["status"] == "error" for row in output_rows)
    return {
        "rows": output_rows,
        "total_rows": len(output_rows),
        "new_count": new_count,
        "existing_count": existing_count,
        "error_count": error_count,
        "can_import": error_count == 0 and new_count > 0,
    }


def import_household_csv(
    db: Session,
    community_id: int,
    admin_user_id: int,
    file_name: str,
    csv_text: str,
) -> dict:
    preview = preview_household_csv(db, community_id, csv_text)
    if preview["error_count"]:
        raise HouseholdCsvError("Corrige los errores del archivo antes de importarlo.")
    rows_to_create = [row for row in preview["rows"] if row["status"] == "new"]
    if not rows_to_create:
        raise HouseholdCsvError("El archivo no contiene viviendas nuevas.")

    created_ids: list[int] = []
    for row in rows_to_create:
        household = Household(
            community_id=community_id,
            code=row["code"],
            is_active=row["is_active"],
        )
        db.add(household)
        db.flush()
        created_ids.append(household.id)
        if row["email"]:
            db.add(
                User(
                    email=row["email"],
                    role=UserRole.RESIDENT.value,
                    is_active=True,
                    community_id=community_id,
                    household_id=household.id,
                )
            )

    db.flush()
    safe_file_name = PurePath(file_name).name[:255]
    log_admin_event(
        db,
        event="ADMIN_HOUSEHOLDS_CSV_IMPORTED",
        admin_user_id=admin_user_id,
        community_id=community_id,
        metadata={
            "file_name": safe_file_name,
            "created_count": len(created_ids),
            "existing_ignored_count": preview["existing_count"],
        },
    )
    db.commit()
    households = (
        db.query(Household)
        .options(joinedload(Household.user))
        .filter(Household.id.in_(created_ids))
        .order_by(Household.code_normalized.asc())
        .all()
    )
    return {"created_count": len(households), "households": households}
