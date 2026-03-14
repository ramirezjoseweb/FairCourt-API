from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings 
from app.db import get_db
from app.deps import get_current_user
from app.models import Reservation, ReservationStatus, Household, User
from app.schemas import CreateReservationIn, ReservationOut
from app.security import utcnow
from app.services.rules import (
    # importamos las reglas de reserva 
    is_within_booking_window, 
    count_active_reservations_this_week, 
    slot_is_free, 
)

router = APIRouter(prefix="/reservations", tags=["reservations"])

# el router.post es para crear una reserva 
@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: CreateReservationIn, # payload es la petición de reserva y CreateReservationIn es la clase de la petición de reserva 
    db: Session = Depends(get_db), # db es la sesión de la base de datos 
    current_user: User = Depends(get_current_user), # current_user es el usuario autenticado 
): 
    """
    Crea una reserva para la vivienda del usuario autenticado.

    Reglas implementadas en esta versión:
    - usuario autenticado
    - vivienda activa
    - vivienda no suspendida
    - start_at no puede estar en el pasado
    - start_at debe estar dentro de la ventana de reserva
    - una única reserva activa por franja
    - máximo de reservas activas por semana por vivienda
    """
    # Obtenemos la vivienda del usuario autenticado 
    household = db.query(Household).filter(Household.id == current_user.household_id).first() 
    if not household or not household.is_active: 
        raise HTTPException(status_code=403, detail="La vivienda no está activa") 

    now = utcnow() 

    # Comprueba si la vivienda está suspendida 
    if household.suspended_until and household.suspended_until > now: 
        raise HTTPException(status_code=403, detail="La vivienda está suspendida temporalmente") 

    start_at = payload.start_at
    end_at = start_at + timedelta(hours=settings.SLOT_DURATION_HOURS) 

    # Comprueba si la fecha de inicio está en el pasado 
    if starts_at < now: 
        raise HTTPException(status_code=400, detail="No se puede reservar en el pasado")

    # Comprueba si la fecha de inicio está dentro de la ventana de reserva 
    if not is_within_booking_window(start_at, now): 
        raise HTTPException(
            status_code = 400, 
            detail = f"La reserva debe estar dentro de los próximos{settings.BOOKING_WINDOW_DAYS}"
        )

    # Comprueba si la franja horaria está libre 
    if not slot_is_free(db, start_at): 
        raise HTTPException(status_code=409, detail="La franja solicitada ya está ocupada")   
    
    # Comprueba si la vivienda tiene el máximo de reservas activas esta semana 
    weekly_count = count_active_reservations_this_week(db, household.id, start_at)
    if weekly_count >= settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK: 
        raise HTTPException(
            status_code = 409, 
            detail=(
                f"La vivienda ya tiene el máximo de "
                f"{settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK} reservas activas esta semana."
            ),
        )

    # Creamos la reserva 
    reservation = Reservation(
        household_id=household.id, 
        start_at=start_at,
        end_at=end_at, 
        status = ReservationStatus.ACTIVE.value, 
        created_at = now, 
    )
    # Guardamos la reserva en la base de datos 
    db.add(reservation) 
    db.commit()
    db.refresh(reservation)

    return reservation
