import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .db import Base

class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RELEASED = "RELEASED"

class Household(Base):
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
    __tablename__ = "auth_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)

    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Reservation(Base):
    """
    Reserva de una franja horaria de una única pista.

    Restricción clave:
    - start_at es UNIQUE: evita dobles reservas incluso bajo concurrencia.
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
    __tablename__ = "waitlist_entries"
    __table_args__ = (
        Index("ix_waitlist_start_created", "start_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    start_at = Column(DateTime, nullable=False)

    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="WAITING", nullable=False)