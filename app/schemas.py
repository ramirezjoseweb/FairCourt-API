from datetime import datetime
from pydantic import BaseModel, EmailStr, Field 

# Esquema de entrada para solicitar codigo OTP 
class RequestOTPIn(BaseModel):
    house_code: str = Field(min_length=1, max_length=50)
    email: EmailStr

# Esquema de entrada para modificación OTPs 
class VerifyOTPIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)

# Esquema de salida que representa el Token 
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

# Esquema del mensaje de salida
class MessageOut(BaseModel):
    message: str