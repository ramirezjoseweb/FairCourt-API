from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.config import Settings


class ProductionSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        database = (Path(self.directory.name) / "faircourt.sqlite3").as_posix()
        self.values = {
            "APP_ENV": "production",
            "SECRET_KEY": "x" * 40,
            "DATABASE_URL": f"sqlite:///{database}",
            "CHECKIN_BASE_URL": "https://faircourt.es/api",
            "OTP_DELIVERY_MODE": "smtp",
            "DEV_PRINT_OTP": False,
            "SMTP_HOST": "smtp.example.com",
            "SMTP_USERNAME": "account",
            "SMTP_PASSWORD": "secret",
            "SMTP_FROM_EMAIL": "access@example.com",
            "SMTP_STARTTLS": True,
            "SMTP_USE_SSL": False,
        }

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_accepts_hardened_configuration(self) -> None:
        self.assertEqual(Settings(**self.values).APP_ENV, "production")

    def test_rejects_local_database_and_console_otp(self) -> None:
        repository_database = Path(__file__).resolve().parents[2] / "faircourt.db"
        for override in (
            {"DATABASE_URL": "sqlite:///./faircourt.db"},
            {"DATABASE_URL": f"sqlite:///{repository_database.as_posix()}"},
            {"OTP_DELIVERY_MODE": "console"},
            {"DEV_PRINT_OTP": True},
            {"CHECKIN_BASE_URL": "http://faircourt.es/api"},
            {"SECRET_KEY": "dev-change-me-to-a-long-random-secret"},
            {"SMTP_STARTTLS": False, "SMTP_USE_SSL": False},
        ):
            with self.subTest(override=override), self.assertRaises(ValidationError):
                Settings(**(self.values | override))

    def test_configuration_errors_do_not_log_smtp_secret(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            Settings(**(self.values | {"CHECKIN_BASE_URL": "http://faircourt.es/api"}))
        self.assertNotIn("secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
