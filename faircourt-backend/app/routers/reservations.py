from __future__ import annotations
from datetime import datetime, timedelta, date


from fastapi import APIRouter, Depends, HTTPException, status, Query
from jose import JWTError
from sqlalchemy.orm import Session


from app.config import settings 
from app.db import get_db
from app.deps import get_current_user
from app.models import Facility, Reservation, ReservationStatus, Household, User, WaitlistEntry
from app.services.audit import log_event
from app.services.notifications import notify_household
from app.schemas import CreateReservationIn, ReservationOut, SlotOut, WaitlistIn, WaitlistOut, CheckinQRout, MessageOut, NoShowProcessOut
from app.security import utcnow, create_access_token, decode_checkin_token, create_checkin_token
from app.services.rules import (
    # importamos las reglas de la reserva 
    is_within_booking_window, 
    count_active_reservations_this_week, 
    slot_is_free, 
    can_cancel_reservation,
    generate_daily_slots, 
    household_has_active_reservation_at,
    try_promote_waitlist_for_slot,
    can_household_join_waitlist, 
    can_household_book_slot, 
    waitlist_count_for_slot, 
    household_is_in_waitlist, 
    can_checkin_reservation, 
    is_reservation_no_show, 
    apply_no_show_penalty,
    count_active_waitlist_for_household,
    is_prime_time, 
    get_cooldown_group,
    household_is_on_cooldown_for_slot,
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

    facility = (
        db.query(Facility)
        .filter(Facility.id == payload.facility_id)
        .filter(Facility.is_active.is_(True))
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    if not facility.is_reservable:
        raise HTTPException(status_code=409, detail="Esta instalación no admite reservas")

    # Comprueba si la reserva está dentro del horario de la pista 
    """if payload.start_at.hour < settings.OPENING_HOUR or payload.start_at.hour > settings.CLOSING_HOUR: 
        raise HTTPException(status_code=400, detail="La reserva debe estar dentro del horario de la pista")
    """

    start_at = payload.start_at
    valid_starts = {slot_start for slot_start, _ in generate_daily_slots(start_at.date(), facility)}
    if start_at not in valid_starts:
        raise HTTPException(status_code=400, detail="La hora no corresponde a una franja de la instalación")
    end_at = start_at + timedelta(minutes=facility.slot_duration_minutes)

    # Comprueba si la fecha de inicio está en el pasado 
    if start_at < now: 
        raise HTTPException(status_code=400, detail="No se puede reservar en el pasado")

    # Comprueba si la fecha de inicio está dentro de la ventana de reserva 
    if not is_within_booking_window(start_at, now): 
        raise HTTPException(
            status_code = 400, 
            detail = f"La reserva debe estar dentro de los próximos {settings.BOOKING_WINDOW_DAYS} días"
        )

    # Comprueba si la franja horaria está libre 
    if not slot_is_free(db, facility.id, start_at):
        raise HTTPException(status_code=409, detail="La franja horaria solicitada ya está ocupada")   

    # Comprueba si la reserva empieza en una franja exacta (ej: 18:00, 19:00...) 
    """if start_at.minute != 0 or start_at.second != 0:
        raise HTTPException(
            status_code=400,
            detail="La reserva debe empezar en una franja exacta (ej: 18:00, 19:00...)"
        )"""
    
    # Comprueba si la vivienda tiene el máximo de reservas activas esta semana 
    weekly_count = count_active_reservations_this_week(db, household.id, facility.id, start_at)
    if weekly_count >= settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK: 
        raise HTTPException(
            status_code = 409, 
            detail=(
                f"La vivienda ya tiene el máximo de "
                f"{settings.MAX_ACTIVE_RESERVATIONS_PER_WEEK} reservas activas esta semana."
            ),
        )

    on_cooldown, cooldown_group = household_is_on_cooldown_for_slot(db, household.id, facility.id, start_at)
    if on_cooldown: 
        raise HTTPException(
            status_code = 409, 
            detail=(
                f"La vivienda está en cooldown para la franja {cooldown_group}. "
                f"Debe esperar {settings.COOLDOWN_DAYS} días para volver a reservar en esta franja horaria."
            ),
        )

    # Creamos la reserva 
    reservation = Reservation(
        household_id=household.id, 
        facility_id=facility.id,
        start_at=start_at,
        end_at=end_at, 
        status = ReservationStatus.ACTIVE.value, 
        created_at = now, 
        prime_time = is_prime_time(start_at), 
        cooldown_group = get_cooldown_group(start_at), 
    )

    # Lanzamos notificación
    notify_household(
        db,
        household_id=reservation.household_id,
        type="RESERVATION_CREATED",
        message=f"Reserva de {facility.name} creada para {reservation.start_at.strftime('%d/%m/%Y %H:%M')}.",
    )
    db.commit()

    # Guardamos la reserva en la base de datos 
    db.add(reservation) 
    db.commit()
    db.refresh(reservation)

    log_event(
        db, 
        event="RESERVATION_CREATED", 
        user_id=current_user.id, 
        household_id=household.id, 
        reservation_id=reservation.id, 
        metadata={
            "facility_id": facility.id,
            "facility_name": facility.name,
            "start_at": reservation.start_at.isoformat(),
        },
    )
    db.commit()

    return reservation

    

# el router.get es para obtener las reservas del usuario autenticado 
@router.get("/me", response_model=list[ReservationOut])
def list_my_reservations(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Lista las reservas del usuario autenticado ordenadas por fecha de inicio.
    """
    reservations = (
        db.query(Reservation) 
        .filter(Reservation.household_id == current_user.household_id)
        .order_by(Reservation.start_at.asc()) # Ordenamos por fecha de inicio ascendente
        .all() # Obtenemos todas las reservas
    )

    now = utcnow()
      
    return reservations 

# Cancelar una reserva 
@router.post("/{reservation_id}/cancel", response_model=ReservationOut) 
def cancel_reservation(
    # Pillamos el id, la sesion y el usuario autenticado 
    reservation_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
): 
    """
    Cancela una reserva de la vivienda autenticada.

    Reglas:
    - la reserva debe existir
    - debe pertenecer a la vivienda del usuario autenticado
    - debe estar en estado ACTIVE
    - debe cancelarse con al menos X horas de antelación
    """
    reservation = (
        db.query(Reservation) 
        .filter(Reservation.id == reservation_id) # si el id de la reserva es igual al id que se pasa por parametro
        .first() 
    )

    if not reservation: 
        raise HTTPException(status_code=404, detail ="Reserva no encontrada") # si no se encuentra la reserva

    if reservation.household_id != current_user.household_id: 
        raise HTTPException(
            status_code = 400, 
            detail = "No puedes cancelar una reserva de otra vivienda"
        ) # si la reserva no pertenece a la vivienda del usuario autenticado

    if reservation.status == ReservationStatus.CANCELLED.value: 
        raise HTTPException(
            status_code = 400, 
            detail = "La reserva ya ha sido cancelada"
        ) # si la reserva ya ha sido cancelada
    
    now = utcnow() 

    if not can_cancel_reservation(reservation.start_at, now): # si la reserva no se puede cancelar
        raise HTTPException(
            status_code = 400, 
            detail =(f"La reserva puede cancelarse solo con al menos {settings.CANCELLATION_LIMIT_HOURS} horas de antelación"
        ),
    )

    reservation.status = ReservationStatus.CANCELLED.value # cambiamos el estado de la reserva a cancelada
    reservation.cancelled_at = now # guardamos la fecha de cancelacion

    db.commit() # guardamos la reserva en la base de datos
    db.refresh(reservation) # actualizamos la reserva

    # Lanzamos notificación
    notify_household(
        db,
        household_id=reservation.household_id,
        type="RESERVATION_CANCELLED",
        message=(
            f"Reserva de {reservation.facility.name} cancelada para "
            f"{reservation.start_at.strftime('%d/%m/%Y %H:%M')}."
        ),
    )
    db.commit()

    # Intentamos promocionar la lista de espera para la franja horaria de la reserva cancelada
    try_promote_waitlist_for_slot(db, reservation.facility_id, reservation.start_at)
    
    log_event(
        db, 
        event="RESERVATION_CANCELLED", 
        user_id=current_user.id, 
        household_id=reservation.household_id, 
        reservation_id=reservation.id, 
        metadata={
            "facility_id": reservation.facility_id,
            "facility_name": reservation.facility.name,
            "start_at": reservation.start_at.isoformat(),
        },
    )
    db.commit()

    return reservation

    
# Ver Slots
@router.get("/slots", response_model=list[SlotOut])
def get_slots(
    day: date, 
    facility_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
): 
    """
    Devuelve las franjas horarias de un día y su disponibilidad enriquecida.

    Para cada slot informa de:
    - estado (FREE / OCCUPIED)
    - si la reserva es de la vivienda actual
    - si puede reservarse
    - si puede apuntarse a waitlist
    - cuánta gente hay en waitlist
    - si la vivienda actual ya está en waitlist
    """
    household = db.query(Household).filter(Household.id == current_user.household_id).first() 
    now = utcnow() 

    facility = (
        db.query(Facility)
        .filter(Facility.id == facility_id)
        .filter(Facility.is_active.is_(True))
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    if not facility.is_reservable:
        return []

    slots = generate_daily_slots(day, facility)

    day_start = datetime.combine(day, datetime.min.time()) # 00:00:00
    day_end = day_start + timedelta(days=1)  # 00:00:00 del día siguiente
    
    reservations = (
        db.query(Reservation) 
        .filter(Reservation.facility_id == facility.id)
        .filter(Reservation.start_at >= day_start) # Filtra las reservas que empiezan en el día indicado
        .filter(Reservation.start_at < day_end) # y que terminan en el día indicado
        .filter(Reservation.status == ReservationStatus.ACTIVE.value)
        .all() 
    )

    reservations_by_start = {r.start_at: r for r in reservations}

    result = []
    
    # Recorremos todas las franjas horarias del día
    for start_at, end_at in slots: 
        reservation = reservations_by_start.get(start_at) 
        # Si hay una reserva en esta franja horaria
        if reservation: 
            status_value = "OCCUPIED" 
            reservation_id = reservation.id
            is_mine = reservation.household_id == current_user.household_id
        else: 
            status_value = "FREE" 
            reservation_id = None
            is_mine = False
    
        #can_book , _ = can_household_book_slot(db, household, start_at, now) # Comprueba si la vivienda puede reservar en esta franja horaria
        #can_join_waitlist , _ = can_household_join_waitlist(db, household, start_at, now) # Comprueba si la vivienda puede apuntarse a la lista de espera en esta franja horaria
        waitlist_count = waitlist_count_for_slot(db, facility.id, start_at)
        in_waitlist = household_is_in_waitlist(db, household.id, facility.id, start_at)

        can_book, book_reason = can_household_book_slot(db, household, facility.id, start_at, now)
        can_join_waitlist, waitlist_reason = can_household_join_waitlist(db, household, facility.id, start_at, now)

        result.append(
            SlotOut( # Añade la franja horaria al resultado
                start_at = start_at, 
                end_at = end_at, 
                status = status_value,
                reservation_id = reservation_id, 
                is_mine = is_mine, 
                can_book = can_book, 
                can_join_waitlist = can_join_waitlist, 
                waitlist_count = waitlist_count, 
                in_waitlist = in_waitlist,  
                book_reason = book_reason,
                waitlist_reason = waitlist_reason,
            )
        )

    return result

# Unirse a waitlists
@router.post("/waitlist", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
def join_waitlist(
    payload: WaitlistIn,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) 
): 
    """
    Apunta la vivienda autenticada a la lista de espera de una franja
    """
    household = db.query(Household).filter(Household.id == current_user.household_id).first() # verifica que la vivienda existe y pertenece al usuario
    if not household or not household.is_active: 
        raise HTTPException(status_code=403, detail="La vivienda no está activa")

    now = utcnow() 

    if household.suspended_until and household.suspended_until > now: 
        raise HTTPException(status_code=403, detail="La vivienda está suspendida temporalmente")

    start_at = payload.start_at # coge la fecha de inicio de la reserva
    facility = (
        db.query(Facility)
        .filter(Facility.id == payload.facility_id)
        .filter(Facility.is_active.is_(True))
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    if not facility.is_reservable:
        raise HTTPException(status_code=409, detail="Esta instalación no admite reservas")
    valid_starts = {slot_start for slot_start, _ in generate_daily_slots(start_at.date(), facility)}
    if start_at not in valid_starts:
        raise HTTPException(status_code=400, detail="La hora no corresponde a una franja de la instalación")

    if start_at < now: 
        raise HTTPException(status_code=400, detail="No puedes apuntarte a una franja pasada") 

    if not is_within_booking_window(start_at, now): 
        raise HTTPException(
            status_code = 400, 
            detail=f"La franja debe estar dentro de los próximos {settings.BOOKING_WINDOW_DAYS} días"
        )
    
    if slot_is_free(db, facility.id, start_at):
        raise HTTPException(
            status_code = 400, 
            detail="La franja está libre, no existe lista de espera"
        )

    if household_has_active_reservation_at(db, household.id, start_at): 
        raise HTTPException(
            status_code = 409, 
            detail="Ya tienes una reserva activa en esa franja"
        )

    if count_active_waitlist_for_household(db, household.id, facility.id, start_at) >= settings.MAX_ACTIVE_WAITLISTS_PER_WEEK:
        raise HTTPException(
            status_code = 409, 
            detail="Ya tienes el máximo de waitlists activas permitidas"
        )

    """ if household_is_on_cooldown(db, household.id, start_at, now): 
        raise HTTPException(
            status_code = 409, 
            detail="Tu vivienda tiene cooldown en esta franja horaria 18:00h hasta 21:00h"
        )
    """

    existing = (db.query(WaitlistEntry)
    .filter(WaitlistEntry.household_id == household.id)
    .filter(WaitlistEntry.facility_id == facility.id)
    .filter(WaitlistEntry.start_at == start_at)
    .filter(WaitlistEntry.status == "WAITING") 
    .first() 
    )
    if existing: 
        raise HTTPException(
            status_code = 409, 
            detail="Ya estás apuntado a la lista de espera en esa franja"
        )

    entry = WaitlistEntry(
        start_at = start_at, 
        household_id = household.id, 
        facility_id = facility.id,
        status = "WAITING", 
        created_at = now, 
    )

    log_event(
        db, 
        event="WAITLIST_JOINED", 
        household_id = household.id, 
        user_id = current_user.id,
        metadata = {
            "waitlist_entry_id": entry.id,
            "facility_id": facility.id,
            "facility_name": facility.name,
            "start_at": entry.start_at.isoformat(), 
            "status": entry.status,
        }
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Lanzamos notificación
    notify_household(
        db,
        household_id=entry.household_id,
        type="WAITLIST_JOINED",
        message=(
            f"Te has unido a la lista de espera de {facility.name} para "
            f"{entry.start_at.strftime('%d/%m/%Y %H:%M')}."
        ),
    )
    db.commit()

    return entry

# Salirse de waitlists
@router.delete("/waitlist/{entry_id}", response_model=WaitlistOut)
def leave_waitlist(
    entry_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
): 
    """
    Permite a la vivienda autenticada abandonar una lista de espera
    """
    entry = (
        db.query(WaitlistEntry) 
        .filter(WaitlistEntry.id == entry_id)
        .first() 
    )

    if not entry: 
        raise HTTPException(status_code=404, detail="Entrada de lista de espera no encontrada") 

    if entry.household_id != current_user.household_id: 
        raise HTTPException(status_code=403, detail="No puedes modificar la lista de espera de otra vivienda")

    if entry.status != "WAITING": 
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar reservas activas")

    entry.status = "DROPPED"
    db.commit()
    db.refresh(entry)

    log_event(
        db, 
        event="WAITLIST_DROPPED", 
        household_id=current_user.household_id, 
        user_id=current_user.id, 
        metadata={
            "waitlist_entry_id": entry.id,
            "start_at": entry.start_at.isoformat(),
            "status": entry.status,
        }
    )
    db.commit() 

    return entry

@router.get("/{reservation_id}/checkin-qr", response_model=CheckinQRout)
def get_checkin_qr(
    reservation_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
): 
    """
    Genera la URL firmada que se incluirá en el QR de check-in.
    Solo la vivienda propietaria puede solicitarla.
    """
    reservation = (
        db.query(Reservation) 
        .filter(Reservation.id == reservation_id) 
        .first() 
    )

    if not reservation: 
        raise HTTPException(status_code=404, detail="Reserva no encontrada") 

    if reservation.household_id != current_user.household_id: 
        raise HTTPException(status_code=403, detail="No puedes acceder al QR de otra vivienda")  
    
    if reservation.status != ReservationStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="No puedes acceder al QR de una reserva que no está activa")

    expires_at = reservation.start_at + timedelta(minutes=settings.CHECKIN_WINDOW_MINUTES)
    token = create_checkin_token(reservation.id, expires_at)
    checkin_url = f"{settings.CHECKIN_BASE_URL}/reservations/checkin/scan?token={token}"

    return {
        "reservation_id": reservation.id, 
        "checkin_url": checkin_url, 
        "expires_at": expires_at, 
    }

@router.get("/checkin/scan", response_model=MessageOut) 
def checkin_scan(
    token: str = Query(...), 
    db: Session = Depends(get_db), 
): 
    """
    Valida el token del QR y marca la reserva como fichada.
    Este endpoint es público porque el propio token firmado actúa como autorización.
    """
    try: 
        payload = decode_checkin_token(token) 
    except JWTError: 
        raise HTTPException(status_code=401, detail="Token de check-in inválido o expirado") 
    
    if payload.get("purpose") != "checkin": # Comprueba que el propósito del token sea check-in
        raise HTTPException(status_code=401, detail="Token de check-in no válido") 

    reservation_id = payload.get("reservation_id") 
    if not reservation_id: # Comprueba que el token tenga una reserva_id
        raise HTTPException(status_code=401, detail="Token de check-in incompleto") 

    reservation = (
        db.query(Reservation) 
        .filter(Reservation.id == reservation_id) 
        .first() 
    )

    if not reservation: 
        raise HTTPException(status_code=404, detail="Reserva no encontrada") 

    now = utcnow() 
    can_checkin, reason = can_checkin_reservation(reservation, now) # Comprueba si la reserva se puede checkear

    if not can_checkin: # Si la reserva no se puede checkear
        detail_map = {
            "RESERVATION_NOT_ACTIVE": "La reserva no está activa.",
            "ALREADY_CHECKED_IN": "La reserva ya ha realizado el check-in.",
            "TOO_EARLY": "Todavía no se puede realizar el check-in.",
            "CHECKIN_WINDOW_EXPIRED": "La ventana de check-in ha expirado.",
            "TOO_LATE": "La reserva ha expirado.",
        }
        raise HTTPException(status_code=400, detail=detail_map.get(reason, "No se puede realizar el check-in"))

    reservation.checkin_at = now 
    db.commit() 

    return {"message": "Check-in realizado correctamente."}

@router.post("/process-no-shows", response_model=NoShowProcessOut)
def process_no_shows(
    db: Session = Depends(get_db) 
): 
    """
    Procesa reservas activas cuya ventana de check-in ya expiró sin check-in.

    Para cada una:
    - la marca como NO_SHOW
    - suma strike a la vivienda
    - si procede, aplica suspensión automática
    - intenta promocionar waitlist
    """
    now = utcnow() 

    candidate_reservations = (
        db.query(Reservation) 
        .filter(Reservation.status == ReservationStatus.ACTIVE.value) 
        .all()
    )

    # Processed será el número de reservas procesadas
    processed = 0 
    # no_show_count será el número de reservas marcadas como NO_SHOW
    no_show_count = 0 
    # promoted_count será el número de reservas promocionadas desde la lista de espera
    promoted_count = 0 

    for reservation in candidate_reservations: 
        processed += 1 

        # Si la reserva no es un no-show, se salta
        if not is_reservation_no_show(reservation, now): 
            continue
        
        # Si la reserva es un no-show, se aplica la penalización
        apply_no_show_penalty(db, reservation, now) 
        no_show_count += 1 

        # Se intenta promocionar la lista de espera
        promoted = try_promote_waitlist_for_slot(
            db, reservation.facility_id, reservation.start_at
        )
        if promoted: 
            promoted_count += 1 

    return {
        "processed_reservations": processed, 
        "no_show_reservations": no_show_count, 
        "promoted_from_waitlist": promoted_count, 
    }

