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
    is_within_booking_window, 
    count_active_reservations_this_week, 
    slot_is_free, 
)

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: CreateReservationIn, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
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
    household = db.query(Household).filter(Household.id == current_user.household_id).first() 
    if not household or not household.is_active: 
        raise HTTPException(status_code=403, detail="La vivienda no está activa") 

    now = utcnow()

    if household.suspended_until and household.suspended_until > now: 
        raise HTTPException(status_code=403, detail="La vivienda está suspendida temporalmente") 

    start_at = payload.start_at
    end_at = start_at + timedelta(hours=settings.SLOT_DURATION_HOURS) 

    if starts_at < now: 
        raise HTTPException(status_code=400, detail="No se puede reservar en el pasado")

    if not is_within_booking_window(start_at, now): 
        raise HTTPException(
            status_code = 400, 
            detail = f"La reserva debe estar dentro de los próximos{settings.BOOKING_WINDOW_DAYS}"
        )

    if not slot_is_free(db, start_at): 
        raise HTTPException(status_code=409, detail="La franja solicitada ya está ocupada") 
        
    weekly_count = count_active_reservations_this_week(db, household.id, start_at)
    if weekly_count >= settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK: 
        raise HTTPException(
            status_code = 409, 
            detail=(
                f"La vivienda ya tiene el máximo de "
                f"{settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK} reservas activas esta semana."
            ),
        )

    reservation = Reservation(
        household_id=household.id, 
        start_at=start_at,
        end_at=end_at, 
        status = ReservationStatus.ACTIVE.value, 
        created_at = now, 
    )

    db.add(reservation) 
    db.commit()
    db.refresh(reservation)

    return reservation
