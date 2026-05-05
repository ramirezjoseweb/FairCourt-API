from dns.rdataset import from_rdata_list
from app.models import Household
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field # EmailStr es para validar que el email sea correcto, field es para validar que el campo sea correcto 

# Clase de la petición de OTP 
class RequestOTPIn(BaseModel):
    house_code: str = Field(min_length=1, max_length=50)
    email: EmailStr

# Clase de la verificación de OTP 
class VerifyOTPIn(BaseModel):
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

# Clase de la petición de reserva 
class CreateReservationIn(BaseModel): 
    start_at: datetime 

# Clase de la respuesta de reserva 
class ReservationOut(BaseModel): 
    id: int
    household_id: int 
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
    start_at: datetime

# Clase de la respuesta de lista de espera 
class WaitlistOut(BaseModel): 
    id: int
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
    start_at: datetime
    status:str

    class Config: 
        from_attributes = True

class MeOut(BaseModel): 
    id: int
    email: str 
    Household_id: int
    strikes: int 
    suspended_until: datetime | None = None
    active_waitlist_count: int 
    active_waitlists: list[WaitlistSummaryOut]

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