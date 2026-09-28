from __future__ import annotations

import smtplib
import unittest
from datetime import datetime
from unittest.mock import patch

from pydantic import ValidationError

from app.config import Settings, settings
from app.services.otp_delivery import OtpDeliveryError, deliver_otp


class OtpDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = {
            name: getattr(settings, name)
            for name in (
                "OTP_DELIVERY_MODE",
                "DEV_PRINT_OTP",
                "SMTP_HOST",
                "SMTP_PORT",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "SMTP_FROM_EMAIL",
                "SMTP_FROM_NAME",
                "SMTP_STARTTLS",
                "SMTP_USE_SSL",
                "SMTP_TIMEOUT_SECONDS",
            )
        }

    def tearDown(self) -> None:
        for name, value in self.original.items():
            setattr(settings, name, value)

    def configure_smtp(self) -> None:
        settings.OTP_DELIVERY_MODE = "smtp"
        settings.SMTP_HOST = "smtp.example.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USERNAME = "faircourt-user"
        settings.SMTP_PASSWORD = "secret-password"
        settings.SMTP_FROM_EMAIL = "no-reply@example.com"
        settings.SMTP_FROM_NAME = "FairCourt"
        settings.SMTP_STARTTLS = True
        settings.SMTP_USE_SSL = False
        settings.SMTP_TIMEOUT_SECONDS = 8

    def test_console_mode_prints_otp_only_when_enabled(self) -> None:
        settings.OTP_DELIVERY_MODE = "console"
        settings.DEV_PRINT_OTP = True
        with patch("builtins.print") as print_mock:
            deliver_otp(
                "resident@example.com",
                "123456",
                datetime(2026, 9, 20, 12, 0),
                "RESIDENT",
            )
        self.assertIn("123456", print_mock.call_args.args[0])

        settings.DEV_PRINT_OTP = False
        with patch("builtins.print") as print_mock:
            deliver_otp(
                "resident@example.com",
                "654321",
                datetime(2026, 9, 20, 12, 0),
                "RESIDENT",
            )
        print_mock.assert_not_called()

    def test_smtp_mode_requires_authentication_credentials(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                OTP_DELIVERY_MODE="smtp",
                SMTP_HOST="smtp-relay.brevo.com",
                SMTP_USERNAME=None,
                SMTP_PASSWORD=None,
                SMTP_FROM_EMAIL="acceso@faircourt.es",
            )

    @patch("app.services.otp_delivery.smtplib.SMTP")
    def test_smtp_mode_uses_starttls_authentication_and_multipart_email(
        self,
        smtp_class,
    ) -> None:
        self.configure_smtp()
        client = smtp_class.return_value.__enter__.return_value

        deliver_otp(
            "resident@example.com",
            "123456",
            datetime(2026, 9, 20, 12, 0),
            "RESIDENT",
        )

        smtp_class.assert_called_once_with(
            "smtp.example.com",
            587,
            timeout=8,
        )
        self.assertEqual(client.ehlo.call_count, 2)
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("faircourt-user", "secret-password")
        message = client.send_message.call_args.args[0]
        self.assertEqual(message["To"], "resident@example.com")
        self.assertEqual(message["From"], "FairCourt <no-reply@example.com>")
        self.assertTrue(message.is_multipart())
        self.assertIn("123456", message.get_body(preferencelist=("plain",)).get_content())

    @patch("app.services.otp_delivery.smtplib.SMTP")
    def test_smtp_error_is_exposed_as_delivery_error(self, smtp_class) -> None:
        self.configure_smtp()
        client = smtp_class.return_value.__enter__.return_value
        client.send_message.side_effect = smtplib.SMTPException("provider down")

        with self.assertRaises(OtpDeliveryError):
            deliver_otp(
                "resident@example.com",
                "123456",
                datetime(2026, 9, 20, 12, 0),
                "RESIDENT",
            )


if __name__ == "__main__":
    unittest.main()
