from dns.rdataset import from_rdata_list
from app.models import Household
from typing import Optional
from datetime import datetime
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator # EmailStr es para validar que el email sea correcto, field es para validar que el campo sea correcto

# Clase de la petición de OTP 
class RequestOTPIn(BaseModel):
    community_slug: str = Field(default="faircourt", min_length=1, max_length=80)
    house_code: str = Field(min_length=1, max_length=50)
    email: EmailStr

# Clase de la verificación de OTP 
class VerifyOTPIn(BaseModel):
    community_slug: str = Field(default="faircourt", min_length=1, max_length=80)
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)


class AdminRequestOTPIn(BaseModel):
    email: EmailStr


class AdminVerifyOTPIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)

# Clase del token de autenticación 
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

# Clase del mensaje de respuesta 
class MessageOut(BaseModel):
    message: str


class AdminMeOut(BaseModel):
    id: int
    email: str
    role: str


class CommunitySummaryOut(BaseModel):
    id: int
    slug: str
    name: str
    timezone: str
    is_active: bool
    household_count: int
    facility_count: int


class AdminHouseholdCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)

    @field_validator("code")
    @classmethod
    def normalize_code_spacing(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("El código de vivienda no puede estar vacío.")
        return normalized


class AdminHouseholdOut(BaseModel):
    id: int
    community_id: int
    code: str
    is_active: bool
    strikes: int
    suspended_until: datetime | None = None
    resident_email: str | None = None
    created_at: datetime


class FacilityOut(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str | None = None
    icon: str
    priority: int
    is_reservable: bool
    opening_hour: int
    closing_hour: int
    slot_duration_minutes: int

    class Config:
        from_attributes = True


class AdminFacilityWriteIn(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    icon: str = Field(default="court", min_length=1, max_length=50)
    priority: int = Field(default=100, ge=0, le=9999)
    is_active: bool = True
    is_reservable: bool = True
    opening_hour: int = Field(default=9, ge=0, le=23)
    closing_hour: int = Field(default=22, ge=1, le=24)
    slot_duration_minutes: int = Field(default=60, ge=15, le=240)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            raise ValueError(
                "El código solo puede contener letras minúsculas, números y guiones."
            )
        return normalized

    @field_validator("name", "category", "icon")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Este campo no puede estar vacío.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.opening_hour >= self.closing_hour:
            raise ValueError("La hora de cierre debe ser posterior a la apertura.")
        return self


class AdminFacilityOut(FacilityOut):
    community_id: int
    is_active: bool


class CommunityPolicyOut(BaseModel):
    community_id: int
    booking_window_days: int
    max_active_reservations_per_day: int
    max_active_reservations_per_week: int
    cancellation_limit_hours: int
    checkin_window_minutes: int
    max_strikes: int
    suspension_days: int
    max_active_waitlists_per_week: int
    prime_time_start_hour: int
    prime_time_end_hour: int
    cooldown_days: int
    unlock_voting_enabled: bool
    unlock_voting_hours: int
    unlock_min_yes_votes: int

    class Config:
        from_attributes = True


class AdminBasicPolicyUpdateIn(BaseModel):
    booking_window_days: int = Field(ge=0, le=365)
    max_active_reservations_per_day: int = Field(ge=0, le=50)
    max_active_reservations_per_week: int = Field(ge=0, le=100)
    cancellation_limit_hours: int = Field(ge=0, le=336)

# Clase de la petición de reserva 
class CreateReservationIn(BaseModel): 
    facility_id: int
    start_at: datetime 

# Clase de la respuesta de reserva 
class ReservationOut(BaseModel): 
    id: int
    household_id: int 
    facility_id: int
    facility: FacilityOut
    start_at: datetime
    end_at: datetime
    status: str
    created_at: datetime
    class Config: 
        from_attributes = True # esto es para que pydantic pueda leer los atributos del modelo. Con esto Pydantic puede convertir objetos SQLAlchemy en JSON

# Clase de la respuesta de franja horaria 
class SlotOut(BaseModel): 
    start_at: datetime # Fecha de inicio de la franja horaria 
    end_at: datetime # Fecha de fin de la franja horaria
    reservation_id: int | None = None # ID de la reserva si existe 
    is_mine: bool = False # Si la reserva es del usuario autenticado 
    can_book: bool # Si el usuario autenticado puede reservar en esta franja horaria 
    can_join_waitlist: bool # Si el usuario autenticado puede apuntarse a la lista de espera en esta franja horaria
    waitlist_count: int # Número de personas en la lista de espera en esta franja horaria
    in_waitlist: bool # Si el usuario autenticado ya está en la lista de espera en esta franja horaria
    status: str # Estado de la franja horaria 
    book_reason: str | None = None 
    waitlist_reason: str | None = None

# Clase de la petición de lista de espera 
class WaitlistIn(BaseModel): 
    facility_id: int
    start_at: datetime

# Clase de la respuesta de lista de espera 
class WaitlistOut(BaseModel): 
    id: int
    facility_id: int
    facility: FacilityOut
    start_at: datetime
    household_id: int 
    created_at: datetime
    status: str
   
    # class config para que pydantic pueda leer los atributos del modelo. Con esto Pydantic puede convertir objetos SQLAlchemy en JSON 
    class Config: 
        from_attributes = True 

# Clase de la respuesta de QR de check-in 
class CheckinQRout(BaseModel): 
    reservation_id: int 
    checkin_url: str
    expires_at: datetime

# Clase de la respuesta del proceso de no-show 
class NoShowProcessOut(BaseModel): 
    processed_reservations: int 
    no_show_reservations: int 
    promoted_from_waitlist: int

class WaitlistSummaryOut(BaseModel): 
    id: int 
    facility_id: int
    facility: FacilityOut
    start_at: datetime
    status:str

    class Config: 
        from_attributes = True

class MeOut(BaseModel): 
    id: int
    email: str 
    household_id: int
    household_code: str | None = None
    strikes: int 
    suspended_until: datetime | None = None
    active_waitlist_count: int 
    active_waitlists: list[WaitlistSummaryOut]
    community_id: int
    community_slug: str
    community_name: str

# Clase de la respuesta de auditoría 
class AuditLogOut(BaseModel): 
    id: int
    event:str
    household_id: int | None = None
    user_id: int | None = None
    reservation_id: int | None = None
    metadata_json: str | None = None
    created_at: datetime

    class Config: 
        from_attributes = True 

# Clase para la petición de desbloqueo de cuenta 
class UnlockProposalIn(BaseModel): 
    reason: str = Field(min_length=1, max_length=500) # razón para desbloquear la cuenta

# Clase para el voto de desbloqueo de cuenta 
class UnlockVoteIn(BaseModel): 
    vote: str 

# Clase para la respuesta de desbloqueo de cuenta 
class UnlockProposalOut(BaseModel): 
    id: int 
    target_household_id: int 
    created_by_user_id: int 
    reason: str 
    status: str 
    created_at: datetime
    closes_at: datetime
    resolved_at: datetime | None = None
    target_household_code: str | None = None

    class Config: 
        from_attributes = True 

# Clase para la salida de los votos
class UnlockVoteOut(BaseModel): 
    id: int
    proposal_id: int 
    voter_household_id: int
    vote: str
    created_at: datetime

    class Config: 
        from_attributes = True

class NotificationOut(BaseModel): 
    id: int 
    user_id: int
    household_id: int 
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config: 
        from_attributes = True
