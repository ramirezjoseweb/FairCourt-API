import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy.engine import make_url


_configured_env_file = os.getenv("FAIRCOURT_ENV_FILE")
if _configured_env_file:
    if not Path(_configured_env_file).is_file():
        raise RuntimeError("FAIRCOURT_ENV_FILE no existe.")
    load_dotenv(_configured_env_file)
else:
    load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "si", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} debe ser true o false.")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


class Settings(BaseModel):
    model_config = ConfigDict(validate_default=True, hide_input_in_errors=True)

    APP_ENV: Literal["development", "production"] = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development").strip().lower()
    )

    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY",
            "dev-change-me-to-a-long-random-secret",
        )
    )
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite:///./faircourt.db",
        ),
        min_length=1,
    )
    JWT_ALG: str = Field(default_factory=lambda: os.getenv("JWT_ALG", "HS256"))
    ACCESS_TOKEN_MINUTES: int = Field(
        default_factory=lambda: _env_int("ACCESS_TOKEN_MINUTES", 60 * 24),
        ge=1,
    )

    OTP_TTL_MINUTES: int = Field(
        default_factory=lambda: _env_int("OTP_TTL_MINUTES", 10),
        ge=1,
        le=60,
    )
    OTP_LENGTH: int = Field(
        default_factory=lambda: _env_int("OTP_LENGTH", 6),
        ge=4,
        le=12,
    )
    OTP_RESEND_COOLDOWN_SECONDS: int = Field(
        default_factory=lambda: _env_int("OTP_RESEND_COOLDOWN_SECONDS", 60),
        ge=0,
        le=3_600,
    )
    OTP_DELIVERY_MODE: Literal["console", "smtp"] = Field(
        default_factory=lambda: os.getenv("OTP_DELIVERY_MODE", "console").strip().lower()
    )
    DEV_PRINT_OTP: bool = Field(
        default_factory=lambda: _env_bool("DEV_PRINT_OTP", True)
    )

    SMTP_HOST: str | None = Field(default_factory=lambda: os.getenv("SMTP_HOST"))
    SMTP_PORT: int = Field(
        default_factory=lambda: _env_int("SMTP_PORT", 587),
        ge=1,
        le=65_535,
    )
    SMTP_USERNAME: str | None = Field(
        default_factory=lambda: os.getenv("SMTP_USERNAME")
    )
    SMTP_PASSWORD: str | None = Field(
        default_factory=lambda: os.getenv("SMTP_PASSWORD")
    )
    SMTP_FROM_EMAIL: EmailStr | None = Field(
        default_factory=lambda: os.getenv("SMTP_FROM_EMAIL")
    )
    SMTP_FROM_NAME: str = Field(
        default_factory=lambda: os.getenv("SMTP_FROM_NAME", "FairCourt"),
        min_length=1,
        max_length=100,
    )
    SMTP_STARTTLS: bool = Field(
        default_factory=lambda: _env_bool("SMTP_STARTTLS", True)
    )
    SMTP_USE_SSL: bool = Field(
        default_factory=lambda: _env_bool("SMTP_USE_SSL", False)
    )
    SMTP_TIMEOUT_SECONDS: int = Field(
        default_factory=lambda: _env_int("SMTP_TIMEOUT_SECONDS", 10),
        ge=1,
        le=60,
    )

    SLOT_DURATION_HOURS: int = Field(
        default_factory=lambda: _env_int("SLOT_DURATION_HOURS", 1),
        ge=1,
    )
    OPENING_HOUR: int = Field(
        default_factory=lambda: _env_int("OPENING_HOUR", 9),
        ge=0,
        le=23,
    )
    CLOSING_HOUR: int = Field(
        default_factory=lambda: _env_int("CLOSING_HOUR", 22),
        ge=1,
        le=24,
    )
    CHECKIN_BASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "CHECKIN_BASE_URL",
            "http://127.0.0.1:8000",
        )
    )

    @model_validator(mode="after")
    def validate_smtp(self):
        if self.SMTP_STARTTLS and self.SMTP_USE_SSL:
            raise ValueError("SMTP_STARTTLS y SMTP_USE_SSL no pueden estar activos a la vez.")
        if bool(self.SMTP_USERNAME) != bool(self.SMTP_PASSWORD):
            raise ValueError("SMTP_USERNAME y SMTP_PASSWORD deben configurarse juntos.")
        if self.OTP_DELIVERY_MODE == "smtp":
            if (
                not self.SMTP_HOST
                or not self.SMTP_USERNAME
                or not self.SMTP_PASSWORD
                or not self.SMTP_FROM_EMAIL
            ):
                raise ValueError(
                    "El modo SMTP requiere host, usuario, contraseña y remitente."
                )
        if self.APP_ENV == "production":
            database_url = make_url(self.DATABASE_URL)
            database_path = Path(database_url.database or "")
            repository_dir = Path(__file__).resolve().parents[2]
            if (
                database_url.get_backend_name() != "sqlite"
                or not database_path.is_absolute()
                or database_path.resolve().is_relative_to(repository_dir)
            ):
                raise ValueError(
                    "Producción requiere una base SQLite con ruta absoluta fuera del repositorio."
                )
            if (
                len(self.SECRET_KEY) < 32
                or self.SECRET_KEY == "dev-change-me-to-a-long-random-secret"
            ):
                raise ValueError("Producción requiere una SECRET_KEY aleatoria de al menos 32 caracteres.")
            if self.OTP_DELIVERY_MODE != "smtp" or self.DEV_PRINT_OTP:
                raise ValueError("Producción requiere OTP por SMTP y DEV_PRINT_OTP=false.")
            if not (self.SMTP_STARTTLS or self.SMTP_USE_SSL):
                raise ValueError("Producción requiere cifrado TLS para SMTP.")
            if not self.CHECKIN_BASE_URL.startswith("https://"):
                raise ValueError("Producción requiere CHECKIN_BASE_URL con HTTPS.")
        return self


settings = Settings()
