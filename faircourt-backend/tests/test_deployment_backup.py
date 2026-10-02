from __future__ import annotations

import importlib.util
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch


BACKUP_SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "backup_sqlite.py"
SPEC = importlib.util.spec_from_file_location("faircourt_backup_sqlite", BACKUP_SCRIPT)
assert SPEC and SPEC.loader
backup_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_module)


class DeploymentBackupTests(unittest.TestCase):
    def test_online_backup_contains_committed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "live.sqlite3"
            snapshot = Path(directory) / "snapshot.sqlite3"
            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE pilot (name TEXT NOT NULL)")
                connection.execute("INSERT INTO pilot VALUES ('Gran Parque')")
                connection.commit()

            backup_module.create_snapshot(source, snapshot)

            with closing(sqlite3.connect(snapshot)) as connection:
                self.assertEqual(
                    connection.execute("SELECT name FROM pilot").fetchone(),
                    ("Gran Parque",),
                )
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))

    def test_backup_uses_a_stable_restic_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "live.sqlite3"
            password_file = root / "restic-password"
            password_file.write_text("test-only-password", encoding="utf-8")
            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE pilot (name TEXT NOT NULL)")
                connection.execute("INSERT INTO pilot VALUES ('Parque Venecia')")
                connection.commit()

            commands: list[list[str]] = []

            def capture_backup(command: list[str], *, stdin, check: bool) -> None:
                self.assertTrue(check)
                self.assertEqual(stdin.read(16), b"SQLite format 3\x00")
                commands.append(command)

            environment = {
                "APP_ENV": "production",
                "DATABASE_URL": f"sqlite:///{source.as_posix()}",
                "RESTIC_REPOSITORY": "s3:https://s3.fr-par.scw.cloud/test-bucket",
                "RESTIC_PASSWORD_FILE": str(password_file),
            }
            with patch.dict(os.environ, environment), patch.object(
                backup_module.subprocess, "run", side_effect=capture_backup
            ):
                backup_module.main()

            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0][-3:], ["--stdin", "--stdin-filename", "faircourt.sqlite3"])


if __name__ == "__main__":
    unittest.main()
