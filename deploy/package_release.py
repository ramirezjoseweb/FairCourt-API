"""Build an allowlisted release archive; never ship the tracked local database."""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = (
    "faircourt-backend/app",
    "faircourt-backend/alembic",
    "faircourt-frontend/dist",
)
REQUIRED_FILES = (
    "faircourt-backend/alembic.ini",
    "faircourt-backend/requirements.txt",
    "faircourt-backend/seed.py",
    "faircourt-backend/scripts/bootstrap_platform_admin.py",
    "faircourt-backend/scripts/bootstrap_production_communities.py",
    "deploy/Caddyfile.example",
    "deploy/faircourt.service",
    "deploy/faircourt-backup.service",
    "deploy/faircourt-backup.timer",
    "deploy/app.env.example",
    "deploy/backup.env.example",
    "deploy/backup_sqlite.py",
)


def release_files() -> list[Path]:
    files = [ROOT / name for name in REQUIRED_FILES]
    for name in REQUIRED_DIRS:
        directory = ROOT / name
        if not directory.is_dir():
            raise FileNotFoundError(f"Missing release directory: {name}")
        files.extend(
            path for path in directory.rglob("*")
            if path.is_file() and not path.is_symlink()
            and (name == "faircourt-frontend/dist" or path.suffix in {".py", ".mako"})
        )
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"Missing release file: {path.relative_to(ROOT)}")
    return sorted(
        path for path in files
        if not any(part in {"__pycache__", ".venv"} for part in path.parts)
        and path.suffix not in {".pyc", ".db", ".sqlite3"}
        and not path.name.endswith((".env", ".local"))
    )


def validate_frontend_bundle() -> None:
    assets = list((ROOT / "faircourt-frontend/dist/assets").glob("*.js"))
    if not assets:
        raise RuntimeError("Build the production frontend before packaging.")
    if any(
        b"127.0.0.1:8000" in asset.read_bytes()
        or b"localhost:8000" in asset.read_bytes()
        for asset in assets
    ):
        raise RuntimeError("The frontend bundle points to a local API; rebuild with /api.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Package FairCourt for a clean server.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        raise SystemExit("Write the release archive outside the repository.")
    if output.exists():
        raise SystemExit("The release archive already exists; choose a new output path.")
    files = release_files()
    validate_frontend_bundle()
    with tarfile.open(output, "x:gz") as archive:
        for path in files:
            archive.add(path, arcname=path.relative_to(ROOT).as_posix())
    print(f"Release archive created: {output}")


if __name__ == "__main__":
    main()
