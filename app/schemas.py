from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class RequestOTPIn(BaseModel):
    house_code: str = Field(min_length=1, max_length=50)
    email: EmailStr

class VerifyOTPIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class MessageOut(BaseModel):
    message: str