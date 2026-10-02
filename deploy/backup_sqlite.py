"""Create a consistent SQLite snapshot and send it to encrypted off-site storage."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

from sqlalchemy.engine import make_url


def database_path_from_environment() -> Path:
    if os.getenv("APP_ENV") != "production":
        raise RuntimeError("Backups of the live service require APP_ENV=production.")
    url = make_url(os.environ["DATABASE_URL"])
    database_path = Path(url.database or "")
    if url.get_backend_name() != "sqlite" or not database_path.is_absolute():
        raise RuntimeError("A production SQLite database with an absolute path is required.")
    if not database_path.is_file():
        raise RuntimeError("The production SQLite database does not exist.")
    return database_path


def validate_restic_environment() -> None:
    repository = os.environ["RESTIC_REPOSITORY"]
    if ":" not in repository or repository.startswith(("/", "local:", "file:")):
        raise RuntimeError("The backup repository must be off-site.")
    password_file = Path(os.environ["RESTIC_PASSWORD_FILE"])
    if not password_file.is_file():
        raise RuntimeError("The Restic password file does not exist.")


def create_snapshot(source_path: Path, snapshot_path: Path) -> None:
    with closing(sqlite3.connect(f"{source_path.as_uri()}?mode=ro", uri=True, timeout=30)) as source:
        with closing(sqlite3.connect(snapshot_path)) as snapshot:
            source.backup(snapshot)
    os.chmod(snapshot_path, 0o600)
    with closing(sqlite3.connect(f"{snapshot_path.as_uri()}?mode=ro", uri=True)) as snapshot:
        result = snapshot.execute("PRAGMA quick_check").fetchone()
    if result != ("ok",):
        raise RuntimeError("The SQLite snapshot failed its integrity check.")


def main() -> None:
    source_path = database_path_from_environment()
    validate_restic_environment()
    with tempfile.TemporaryDirectory(prefix="backup-", dir=source_path.parent) as directory:
        snapshot_path = Path(directory) / "faircourt.sqlite3"
        create_snapshot(source_path, snapshot_path)
        with snapshot_path.open("rb") as snapshot_stream:
            subprocess.run(
                [
                    "restic",
                    "backup",
                    "--tag",
                    "faircourt",
                    "--stdin",
                    "--stdin-filename",
                    "faircourt.sqlite3",
                ],
                stdin=snapshot_stream,
                check=True,
            )
    print("FairCourt backup completed.")


if __name__ == "__main__":
    main()
