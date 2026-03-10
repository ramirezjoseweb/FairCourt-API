from pydantic import BaseModel

class Settings(BaseModel):
    # En producción: cambiar esto por una clave larga y guardarla en variables de entorno
    SECRET_KEY: str = "dev-change-me-to-a-long-random-secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 24 # 7 días (tiempo de expiración del token JWT)

    OTP_TTL_MINUTES: int = 10 # El OTP expirará en 10 minutos
    OTP_LENGTH: int = 6 # 6 dígitos

    # Dev mode: imprime OTP en logs 
    DEV_PRINT_OTP: bool = True 

    # Reglas de reserva
    BOOKING_WINDOW_DAYS: int = 7 # 7 son los dias de margen para reservar
    MAX_ACTIVE_RESERVATIONS_PER_WEEK: int = 2 # limite de reservas por usuario
    SLOT_DURATION_HOURS: int = 1 # duracion de cada reserva en horas

settings = Settings() # Crea una instancia de Settings
