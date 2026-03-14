from __future__ import annotations
from datetime import datetime

from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Reservation, ReservationStatus

def is_within_booking_window(start_at, now) -> bool: 
    """
    Comprueba si la reserva está dentro de la ventana de reserva.
    """
    max_date = now + timedelta(days=settings.BOOKING_WINDOW_DAYS) 
    return now <= start_at <= max_date # ahora debe ser menor o igual a la fecha de inicio y la fecha de inicio debe ser menor o igual a la fecha maxima

def count_active_reservations_this_week(db: Session, household_id: int, start_at): 
    """
    Cuenta cuantas reservas activas tiene una vivienda en la semana de la fecha indicada.
    """
    week_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0) # Calcula el inicio de la semana
    week_start = week_start - timedelta(days=week_start.weekday()) # esto es para que empiece en lunes
    week_end = week_start + timedelta(days=7) # Calcula el fin de la semana

    return(
        db.query(Reservation) 
        .filter(
            Reservation.household_id == household_id, # Esto es para que solo cuente las reservas de esa vivienda
            Reservation.status == ReservationStatus.ACTIVE.value, # esto es para que solo cuente las reservas activas
            Reservation.start_at >= week_start, # la fecha de la reserva tiene que ser mayor o igual a lunes    
            Reservation.start_at < week_end # y menor que el siguiente lunes
        )
        .count()
    )

def slot_is_free(db: Session, household_id: int, start_at, end_at) -> bool: 
    """ Comprubea si la franja horaria está libre """
    existing = (
        db.query(Reservation)
        .filter(Reservation.start_at == start_at)
        .filter(Reservation.status == ReservationStatus.ACTIVE.value)
        .first()
    )

    return existing is None 