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