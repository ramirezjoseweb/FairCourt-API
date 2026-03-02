"""
Modelos ORM del dominio FairCourt.

Este módulo define las entidades principales del sistema y su
mapeo relacional mediante SQLAlchemy.

Se modelan:

- Household (vivienda / unidad principal del sistema)
- User (usuario asociado a una vivienda)
- AuthOTP (autenticación basada en código OTP)
- Reservation (reserva de franja horaria)
- WaitlistEntry (entrada en lista de espera)

Las restricciones a nivel de base de datos garantizan integridad
incluso en escenarios de concurrencia.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .db import Base

class ReservationStatus(str, enum.Enum):
    """
    Enumeración de estados posibles de una reserva.

    ACTIVE:
        Reserva confirmada y vigente.

    CANCELLED:
        Reserva cancelada manualmente por el usuario.

    NO_SHOW:
        Usuario no se presentó en el horario reservado.

    RELEASED:
        Reserva liberada automáticamente por el sistema.
    """
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RELEASED = "RELEASED"

class Household(Base):
    """
    Representa una vivienda o unidad principal dentro del sistema.

    Es la entidad central del modelo de negocio:
    - Cada vivienda puede tener exactamente un usuario.
    - Puede realizar múltiples reservas.
    - Puede acumular penalizaciones (strikes).
    - Puede ser suspendida temporalmente.
    """ 
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    strikes = Column(Integer, default=0, nullable=False)
    suspended_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="household", uselist=False)
    reservations = relationship("Reservation", back_populates="household")

class User(Base):
    """
    Usuario del sistema.

    Restricción clave:
    - Existe una relación 1:1 con Household.
    (Una vivienda solo puede tener un usuario asociado.)

    El email es único dentro del sistema.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("household_id", name="uq_users_household_id"),  # 1 usuario por vivienda
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)

    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    household = relationship("Household", back_populates="user")

class AuthOTP(Base):
    """
    Modelo para autenticación basada en One-Time Password (OTP).

    El sistema almacena únicamente el hash del OTP, nunca el código en claro,
    mejorando la seguridad.

    Permite:
    - Controlar expiración del código.
    - Marcarlo como usado para evitar reutilización.
    """
    __tablename__ = "auth_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)

    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Reservation(Base):
    """
    Reserva de una franja horaria para una única pista.

    Reglas de negocio importantes:

    - start_at es UNIQUE:
      Evita dobles reservas incluso bajo concurrencia.
      Esta restricción se aplica a nivel de base de datos para
      garantizar consistencia fuerte.

    - Cada reserva pertenece a un único Household.

    - Se almacenan marcas temporales para:
        * cancelación
        * check-in
        * control de prime time
        * agrupación de cooldown
    """
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("start_at", name="uq_reservations_start_at"),
        Index("ix_reservations_household_start", "household_id", "start_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    status = Column(String, default=ReservationStatus.ACTIVE.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    checkin_at = Column(DateTime, nullable=True)
    prime_time = Column(Boolean, default=False, nullable=False)
    cooldown_group = Column(String, nullable=True)

    household = relationship("Household", back_populates="reservations")

class WaitlistEntry(Base):
    """
    Entrada en la lista de espera para una franja horaria concreta.

    Se utiliza cuando un slot ya está reservado y otros hogares
    desean optar a él en caso de liberación.

    El índice (start_at, created_at) permite:
    - Priorizar por orden cronológico.
    - Resolver la lista de espera de forma eficiente.
    """
    __tablename__ = "waitlist_entries"
    __table_args__ = (
        Index("ix_waitlist_start_created", "start_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    start_at = Column(DateTime, nullable=False)

    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="WAITING", nullable=False)