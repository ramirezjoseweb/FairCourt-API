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

    # Reglas de cancelacion 
    CANCELLATION_LIMIT_HOURS: int = 4 # 4 o más horas antes de la reserva se puede cancelar

    # Horario de la pista
    OPENING_HOUR: int = 9 # 9 de la mañana
    CLOSING_HOUR: int = 22 # 10 de la noche

    # Reglas de check-in
    CHECKIN_WINDOW_MINUTES: int = 15 # 15 minutos despues de la reserva se puede hacer check-in
    CHECKIN_BASE_URL: str = "http://127.0.0.1:8000" # URL base para generar el código QR

    # Reglas de sanciones
    MAX_STRIKES: int = 2 # 3 Maximo de faltas antes de la suspension
    SUSPENSION_DAYS: int = 14 # Tiempo de suspension en dias

    # Reglas de waitlist
    MAX_ACTIVE_WAITLISTS_PER_WEEK: int = 3 # Maximo de waitlist por semana

    # Reglas Cooldown
    PRIME_TIME_START_HOUR: int = 18 # 18 de la tarde
    PRIME_TIME_END_HOUR: int = 21 # 21 de la noche
    COOLDOWN_DAYS: int = 3 # 3 dias de cooldown

    # Reglas de desbloqueo
    UNLOCK_VOTING_HOURS: int = 48 # La propuesta de desbloqueo dura 48 horas
    UNLOCK_MIN_YES_VOTES: int = 2 # Minimo de votos afirmativos para desbloquear

settings = Settings() # Crea una instancia de Settings
