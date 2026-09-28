from __future__ import annotations

import html
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from app.config import settings
from app.models import AuthOTP

from sqlalchemy.orm import Session


class OtpDeliveryError(RuntimeError):
    pass


def otp_delivery_message() -> str:
    if settings.OTP_DELIVERY_MODE == "smtp":
        return "Código generado. Revisa tu correo electrónico."
    return "OTP generado. Modo desarrollo: consulta la consola del servidor."


def otp_resend_is_blocked(
    db: Session,
    recipient: str,
    purpose: str,
    community_id: int | None,
) -> bool:
    if settings.OTP_RESEND_COOLDOWN_SECONDS == 0:
        return False
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    )
    query = (
        db.query(AuthOTP.id)
        .filter(AuthOTP.email == recipient)
        .filter(AuthOTP.purpose == purpose)
        .filter(AuthOTP.used_at.is_(None))
        .filter(AuthOTP.created_at >= cutoff)
    )
    if community_id is None:
        query = query.filter(AuthOTP.community_id.is_(None))
    else:
        query = query.filter(AuthOTP.community_id == community_id)
    return query.first() is not None


def deliver_otp(
    recipient: str,
    otp: str,
    expires_at: datetime,
    purpose: str,
) -> None:
    if settings.OTP_DELIVERY_MODE == "console":
        if settings.DEV_PRINT_OTP:
            label = "DEV ADMIN OTP" if purpose == "PLATFORM_ADMIN" else "DEV OTP"
            print(
                f"[{label}] Email={recipient} OTP={otp} "
                f"(expira {expires_at.isoformat()})"
            )
        return

    message = _build_message(recipient, otp, purpose)
    try:
        _send_smtp(message)
    except (OSError, smtplib.SMTPException) as error:
        raise OtpDeliveryError("No se pudo entregar el OTP por correo.") from error


def _build_message(recipient: str, otp: str, purpose: str) -> EmailMessage:
    is_admin = purpose == "PLATFORM_ADMIN"
    access_name = "panel de administración" if is_admin else "FairCourt"
    subject = (
        "Código de acceso administrativo de FairCourt"
        if is_admin
        else "Tu código de acceso a FairCourt"
    )
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(
        (settings.SMTP_FROM_NAME, str(settings.SMTP_FROM_EMAIL))
    )
    message["To"] = recipient
    message["Auto-Submitted"] = "auto-generated"
    message["X-Auto-Response-Suppress"] = "All"
    message.set_content(
        f"Tu código para acceder a {access_name} es: {otp}\n\n"
        f"Caduca en {settings.OTP_TTL_MINUTES} minutos. "
        "Si no lo has solicitado, puedes ignorar este mensaje.\n"
    )
    safe_otp = html.escape(otp)
    safe_access_name = html.escape(access_name)
    message.add_alternative(
        "<!doctype html><html><body>"
        f"<p>Tu código para acceder a {safe_access_name} es:</p>"
        f"<p style=\"font-size:28px;font-weight:700;letter-spacing:6px\">{safe_otp}</p>"
        f"<p>Caduca en {settings.OTP_TTL_MINUTES} minutos.</p>"
        "<p>Si no lo has solicitado, puedes ignorar este mensaje.</p>"
        "</body></html>",
        subtype="html",
    )
    return message


def _send_smtp(message: EmailMessage) -> None:
    context = ssl.create_default_context()
    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
            context=context,
        ) as client:
            _authenticate_and_send(client, message)
        return

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=settings.SMTP_TIMEOUT_SECONDS,
    ) as client:
        client.ehlo()
        if settings.SMTP_STARTTLS:
            client.starttls(context=context)
            client.ehlo()
        _authenticate_and_send(client, message)


def _authenticate_and_send(client: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    client.send_message(message)
