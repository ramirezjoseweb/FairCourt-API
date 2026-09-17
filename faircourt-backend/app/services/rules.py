from __future__ import annotations
from email import message
from app.security import utcnow
from app.models import CommunityPolicy, Household
from app.models import Facility, WaitlistEntry, Reservation, ReservationStatus

from datetime import timedelta, datetime, time 

from sqlalchemy.orm import Session 

from app.models import Reservation, ReservationStatus
from app.services.audit import log_event
from app.services.notifications import notify_household, create_notification
from app.services.policies import get_community_policy

def is_within_booking_window(
    start_at,
    now,
    policy: CommunityPolicy,
) -> bool:
    """
    Comprueba si la reserva está dentro de la ventana de reserva.
    """
    max_date = now + timedelta(days=policy.booking_window_days)
    return now <= start_at <= max_date # ahora debe ser menor o igual a la fecha de inicio y la fecha de inicio debe ser menor o igual a la fecha maxima

def count_active_reservations_this_week(db: Session, household_id: int, facility_id: int, start_at):
    """
    Cuenta cuantas reservas activas tiene una vivienda en la semana de la fecha indicada.
    """
    now = utcnow() 

    week_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0) # Calcula el inicio de la semana
    week_start = week_start - timedelta(days=week_start.weekday()) # esto es para que empiece en lunes
    week_end = week_start + timedelta(days=7) # Calcula el fin de la semana

    return(
        db.query(Reservation) 
        .filter(Reservation.household_id == household_id)
        .filter(Reservation.facility_id == facility_id)
        .filter(Reservation.status == ReservationStatus.ACTIVE.value)
        .filter(Reservation.start_at >= now)
        .filter(Reservation.start_at >= week_start)
        .filter(Reservation.start_at < week_end)
        .count()
    )

def slot_is_free(db: Session, facility_id: int, start_at) -> bool:
    """Comprueba si una instalación está libre en la franja indicada."""
    existing = (
        db.query(Reservation)
        .filter(Reservation.facility_id == facility_id)
        .filter(Reservation.start_at == start_at)
        .filter(Reservation.status == ReservationStatus.ACTIVE.value)
        .first()
        # esto busca si existe una reserva con la misma fecha de inicio y estado activo para que no haya 2 a la vez activos y a la misma hora y fecha
    )

    return existing is None 

def can_cancel_reservation(
    start_at,
    now,
    policy: CommunityPolicy,
) -> bool:
    """
    Comprueba si la reserva se puede cancelar.
    """
    limit = start_at - timedelta(hours=policy.cancellation_limit_hours)
    return now <= limit # ahora debe ser menor o igual al limite

def generate_daily_slots(target_date, facility: Facility):
    """
    Genera las franjas de un día con el horario y duración de la instalación.
    """
    slots = []
    start_at = datetime.combine(target_date, time(hour=facility.opening_hour))
    closing_at = datetime.combine(target_date, time(hour=facility.closing_hour))
    duration = timedelta(minutes=facility.slot_duration_minutes)
    while start_at + duration <= closing_at:
        end_at = start_at + duration
        slots.append((start_at, end_at)) # Añade la franja horaria a la lista
        start_at = end_at
        
    return slots

#def generate_daily_slots2(target_date):
    """
    Genera franjas reducidas para pruebas.
    Ejemplo: 12:03-12:05, 12:05-12:07, 12:07-12:09...
    """
    slots = []

    start_at = datetime.combine(target_date, time(hour=19, minute=40))
    closing_time = datetime.combine(target_date, time(hour=19, minute=59))

    while start_at < closing_time:
        end_at = start_at + timedelta(minutes=2)
        slots.append((start_at, end_at))
        start_at = end_at

    return slots

def household_has_active_reservation_at(db:Session, household_id: int, start_at) -> bool: 
    """ Comprueba si una vivienda tiene una reserva activa en esa franja"""
    existing = (
        db.query(Reservation) 
        .filter(Reservation.household_id == household_id)
        .filter(Reservation.start_at == start_at) 
        .filter(Reservation.status == ReservationStatus.ACTIVE.value)
        .first()
    )
    
    return existing is not None # devuelve True si existe, False si no y is not None es para que no haya 2 a la vez activos y a la misma hora y fecha

def try_promote_waitlist_for_slot(db: Session, facility_id: int, start_at):
    """
    Busca la primera vivienda en waitlist para la franja indicada e intenta
    promocionarla a reserva activa.

    Si la primera no cumple reglas, se marca como DROPPED y se sigue con la siguiente.
    """
    facility = db.get(Facility, facility_id)
    if not facility:
        return None
    policy = get_community_policy(db, facility.community_id)

    waiting_entries = (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.community_id == facility.community_id)
        .filter(WaitlistEntry.facility_id == facility_id)
        .filter(WaitlistEntry.start_at == start_at) # Filtra por la fecha de inicio
        .filter(WaitlistEntry.status == "WAITING") # Filtra por el estado WAITING
        .order_by(WaitlistEntry.created_at.asc()) # Ordenamos por fecha de creacion ascendente
        .all() # Obtenemos todas las reservas
    )

    now = utcnow() 

    for entry in waiting_entries: # Recorremos todas las reservas
        household = (
            db.query(Household)
            .filter(Household.id == entry.household_id)
            .filter(Household.community_id == facility.community_id)
            .first()
        ) # Obtenemos la vivienda de la lista de espera
        if not household or not household.is_active: # Si la vivienda no existe o no está activa
            entry.status = "DROPPED" # La marcamos como eliminada

            log_event(
            db,
            event="WAITLIST_DROPPED",
            household_id=entry.household_id,
            metadata={
                "waitlist_entry_id": entry.id,
                "start_at": entry.start_at.isoformat(),
                "reason": "HOUSEHOLD_INACTIVE",  # cambia según el caso
            },
        )
            db.commit() 
            continue
 
        weekly_count = count_active_reservations_this_week(db, household.id, facility_id, start_at)
        if weekly_count >= policy.max_active_reservations_per_week:
            entry.status = "DROPPED" # La marcamos como eliminada

            log_event(
            db,
            event="WAITLIST_DROPPED",
            household_id=entry.household_id,
            metadata={
                "waitlist_entry_id": entry.id,
                "start_at": entry.start_at.isoformat(),
                "reason": "HOUSEHOLD_WEEKLY_LIMIT",  # cambia según el caso
            },
        )
            db.commit() 
            continue
    
        if not slot_is_free(db, facility_id, start_at):
            return None # Si la franja horaria no está libre, devolvemos None

        on_cooldown, _ = household_is_on_cooldown_for_slot(
            db,
            household.id,
            facility_id,
            start_at,
            policy,
        )
        if on_cooldown:
            entry.status = "DROPPED" 

            log_event(
            db,
            event="WAITLIST_DROPPED",
            household_id=entry.household_id,
            metadata={
                "waitlist_entry_id": entry.id,
                "start_at": entry.start_at.isoformat(),
                "reason": "HOUSEHOLD_ON_COOLDOWN",  # cambia según el caso
            },
        )
            db.commit() 
            continue

        # Creamos la reserva 
        reservation = Reservation (
            community_id = facility.community_id,
            household_id = household.id, 
            facility_id = facility_id,
            start_at = start_at, 
            end_at = start_at + timedelta(minutes=entry.facility.slot_duration_minutes),
            status = ReservationStatus.ACTIVE.value, 
            created_at = now, 
            prime_time = is_prime_time(start_at, policy),
            cooldown_group = get_cooldown_group(start_at, policy),
        )

        db.add(reservation) # Añadimos la reserva a la base de datos 
        db.flush() # Esto es para que se guarde la reserva en la base de datos 

        entry.status = "PROMOTED" # La marcamos como promovida 
        db.commit() # Guardamos la reserva en la base de datos 
        db.refresh(reservation) # Actualizamos la reserva con los datos de la base de datos 

        log_event(
            db,
            event="WAITLIST_PROMOTED",
            household_id=household.id,
            reservation_id=reservation.id,
            metadata={
                "waitlist_entry_id": entry.id,
                "start_at": reservation.start_at.isoformat(),
            },
        )
        db.commit()

        # Lanzamos notificación
        notify_household(
        db,
        household_id=reservation.household_id,
        type="WAITLIST_PROMOTED",
        message=(
            f"Has sido promocionado desde la lista de espera de {entry.facility.name} "
            f"para {reservation.start_at.strftime('%d/%m/%Y %H:%M')}."
        ),
        )
        db.commit()

        return reservation
    
    return None # Si ninguna vivienda cumple las reglas, devolvemos None
        
def can_household_book_slot(db: Session, household, facility_id: int, start_at, now) -> tuple[bool, str | None]:
    """
    Determina si una vivienda puede reservar una franja.

    Devuelve:
    - bool: si puede reservar
    - str | None: motivo si no puede
    """
    if not household:
        print("RETURN -> HOUSEHOLD_INACTIVE (household is None)")
        return False, "HOUSEHOLD_INACTIVE"

    if not household.is_active:
        print("RETURN -> HOUSEHOLD_INACTIVE (is_active=False)")
        return False, "HOUSEHOLD_INACTIVE"

    policy = get_community_policy(db, household.community_id)

    if household.suspended_until and household.suspended_until > now:
        print("RETURN -> HOUSEHOLD_SUSPENDED")
        return False, "HOUSEHOLD_SUSPENDED"

    if start_at < now:
        print("RETURN -> PAST_SLOT")
        return False, "PAST_SLOT"

    if not is_within_booking_window(start_at, now, policy):
        print("RETURN -> OUTSIDE_BOOKING_WINDOW")
        return False, "OUTSIDE_BOOKING_WINDOW"

    if not slot_is_free(db, facility_id, start_at):
        print("RETURN -> SLOT_OCCUPIED")
        return False, "SLOT_OCCUPIED"

    weekly_count = count_active_reservations_this_week(db, household.id, facility_id, start_at)
    print("weekly_count =", weekly_count)

    if weekly_count >= policy.max_active_reservations_per_week:
        print("RETURN -> WEEKLY_LIMIT_REACHED")
        return False, "WEEKLY_LIMIT_REACHED"

    if household.suspended_until and household.suspended_until > now:
        return False, "HOUSEHOLD_SUSPENDED"

    on_cooldown, cooldown_group = household_is_on_cooldown_for_slot(
        db,
        household.id,
        facility_id,
        start_at,
        policy,
    )
    if on_cooldown:
        return False, "COOLDOWN_ACTIVE"

    return True, None

def waitlist_count_for_slot(db: Session, facility_id: int, start_at) -> int:
    """
    Cuenta cuantas viviendas están en lista de espera para una franja horaria
    """
    return (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.facility_id == facility_id)
        .filter(WaitlistEntry.start_at == start_at) 
        .filter(WaitlistEntry.status == "WAITING") 
        .count()
    )

def household_is_in_waitlist(db: Session, household_id: int, facility_id: int, start_at) -> bool:
    """
    Comprueba si la vivienda esta en lista de espera 
    """
    existing = (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.household_id == household_id)
        .filter(WaitlistEntry.facility_id == facility_id)
        .filter(WaitlistEntry.start_at == start_at)
        .filter(WaitlistEntry.status == "WAITING") 
        .first()  
    )
    return existing is not None # devuelve True si existe, False si no y is not None es para que no haya 2 a la vez activos y a la misma hora y fecha

def count_active_waitlist_for_household(db: Session, household_id: int, facility_id: int, start_at) -> int:
    """
    Cuenta para cada vivienda, cuantas waitlist tiene en estado
    WAITING a lo largo de la semana 
    """

    now = utcnow() 


    week_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0) 
    week_start = week_start - timedelta(days=week_start.weekday()) # lunes
    week_end = week_start + timedelta(days=7) # domingo

    return(
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.household_id == household_id) # Filtra por vivienda
        .filter(WaitlistEntry.facility_id == facility_id)
        .filter(WaitlistEntry.status == "WAITING") # Filtra por waitlist activas
        .filter(WaitlistEntry.start_at >= now) # filtra las entradas que estén en el futuro
        .filter(WaitlistEntry.start_at >= week_start) 
        .filter(WaitlistEntry.start_at < week_end) # Filtra por semana
        .count() # Cuenta las reservas activas de la vivienda en la semana de la fecha indicada
    ) 

def can_household_join_waitlist(db: Session, household, facility_id: int, start_at, now) -> tuple[bool, str | None]:
    """ 
    Determina si una vivienda puede apuntarse a la waitlist de una franja 
    """
    if not household:
        print("RETURN -> HOUSEHOLD_INACTIVE (household is None)")
        return False, "HOUSEHOLD_INACTIVE"

    if not household.is_active:
        print("RETURN -> HOUSEHOLD_INACTIVE (is_active=False)")
        return False, "HOUSEHOLD_INACTIVE"

    policy = get_community_policy(db, household.community_id)

    if household.suspended_until and household.suspended_until > now:
        print("RETURN -> HOUSEHOLD_SUSPENDED")
        return False, "HOUSEHOLD_SUSPENDED"

    if start_at < now:
        print("RETURN -> PAST_SLOT")
        return False, "PAST_SLOT"

    if not is_within_booking_window(start_at, now, policy):
        print("RETURN -> OUTSIDE_BOOKING_WINDOW")
        return False, "OUTSIDE_BOOKING_WINDOW"

    if slot_is_free(db, facility_id, start_at):
        print("RETURN -> SLOT_FREE")
        return False, "SLOT_FREE"

    if household_has_active_reservation_at(db, household.id, start_at):
        print("RETURN -> ALREADY_HAS_RESERVATION")
        return False, "ALREADY_HAS_RESERVATION"

    if household_is_in_waitlist(db, household.id, facility_id, start_at):
        print("RETURN -> ALREADY_IN_WAITLIST")
        return False, "ALREADY_IN_WAITLIST"

    weekly_waitlist_count = count_active_waitlist_for_household(db, household.id, facility_id, start_at)
    if weekly_waitlist_count >= policy.max_active_waitlists_per_week:
        return False, "WAITLIST_WEEKLY_LIMIT_REACHED"

    weekly_count = count_active_reservations_this_week(db, household.id, facility_id, start_at)
    if weekly_count >= policy.max_active_reservations_per_week:
        return False, "WEEKLY_LIMIT_REACHED"

    return True, None

def can_checkin_reservation(
    reservation,
    now,
    policy: CommunityPolicy,
) -> tuple[bool, str | None]:
    """
    Comprueba si una reserva puede hacer check-in.

    Regla actual:
    - debe estar ACTIVE
    - no debe tener checkin_at
    - solo se puede hacer entre start_at y start_at + CHECKIN_WINDOW_MINUTES
    """
    if reservation.status != ReservationStatus.ACTIVE.value: 
        return False, "RESERVATION_NOT_ACTIVE" 

    if reservation.checkin_at is not None: 
        return False, "ALREADY_CHECKED_IN"

    if now < reservation.start_at: # Si la hora actual es menor a la hora de inicio de la reserva porque no se puede hacer check-in antes de la hora de inicio
        return False, "TOO_EARLY" 

    if now > reservation.end_at: # Si la hora actual es mayor a la hora de fin de la reserva porque no se puede hacer check-in después de la hora de fin
        return False, "TOO_LATE" # La reserva ha expirado

    checkin_deadline = reservation.start_at + timedelta(
        minutes=policy.checkin_window_minutes
    )
    if now > checkin_deadline: # Si la hora actual es mayor a la fecha limite para hacer check-in
        return False, "TOO_LATE" # La reserva ha expirado

    return True, None # La reserva puede hacer check-in
    # el usuario dispone de 15 minutos para hacer check-in desde el inicio de la reserva

def get_effective_checkin_start(reservation: Reservation):
    """
    Devuelve el momento desde el que debe empezar a contar la ventana de check-in.

    En reservas normales, se usa start_at.
    En reservas promocionadas desde waitlist, created_at puede ser posterior a start_at,
    por lo que se usa created_at para conceder una ventana real de check-in.
    """
    if reservation.created_at and reservation.created_at > reservation.start_at:
        return reservation.created_at

    return reservation.start_at

def is_reservation_no_show(
    reservation,
    now,
    policy: CommunityPolicy,
) -> bool:
    """ Determina si una reserva debe considerarse no-show. 
    Reglas: 
        - sigue ACTIVE
        - no se ha hecho check-in 
        - ha pasado más de 15 minutos desde el inicio de la reserva
    """
    if reservation.status != ReservationStatus.ACTIVE.value: 
        return False

    if reservation.checkin_at is not None: 
        return False

    effective_start = get_effective_checkin_start(reservation)
    deadline = effective_start + timedelta(minutes=policy.checkin_window_minutes)

    return now > deadline # Si la hora actual es mayor a la fecha limite para hacer check-in, la reserva es no-show

def apply_no_show_penalty(db: Session, reservation: Reservation, now):
    """
    Marca una reserva como NO_SHOW, suma un strike a la vivienda y aplica
    suspensión temporal si alcanza el límite de strikes configurado.
    """
    household = (
        db.query(Household)
        .filter(Household.id == reservation.household_id)
        .filter(Household.community_id == reservation.community_id)
        .first()
    )

    if not household:
        return None

    policy = get_community_policy(db, reservation.community_id)

    suspension_applied = False

    was_promoted_from_waitlist = (
    db.query(WaitlistEntry)
    .filter(WaitlistEntry.community_id == reservation.community_id)
    .filter(WaitlistEntry.household_id == reservation.household_id)
    .filter(WaitlistEntry.start_at == reservation.start_at)
    .filter(WaitlistEntry.status == "PROMOTED")
    .first()
    is not None
)

    # Marcamos la reserva como NO_SHOW y añadimos strike.
    reservation.status = ReservationStatus.NO_SHOW.value
    if not was_promoted_from_waitlist:
        household.strikes += 1

    # Aplicamos suspensión solo si alcanza el límite.
    if not was_promoted_from_waitlist and household.strikes >= policy.max_strikes:
        household.suspended_until = now + timedelta(days=policy.suspension_days)
        suspension_applied = True

    db.commit()
    db.refresh(reservation)
    db.refresh(household)

    log_event(
        db,
        event="RESERVATION_NO_SHOW",
        household_id=household.id,
        reservation_id=reservation.id,
        metadata={
            "start_at": reservation.start_at.isoformat(),
            "checkin_at": reservation.checkin_at.isoformat()
            if reservation.checkin_at
            else None,
        },
    )

    if not was_promoted_from_waitlist:
        log_event(
            db,
            event="STRIKE_ADDED",
            household_id=household.id,
            reservation_id=reservation.id,
            metadata={
                "new_strikes": household.strikes,
                "start_at": reservation.start_at.isoformat(),
            },
        ),
    else:
        log_event(
            db,
            event="No-show en reserva promocionada desde waitlist (sin strike)",
            household_id=household.id,
            reservation_id=reservation.id,
            metadata={
                "start_at": reservation.start_at.isoformat(),
                "reason": "PROMOTED_FROM_WAITLIST",
            },
        )

    if suspension_applied:
        log_event(
            db,
            event="HOUSEHOLD_SUSPENDED",
            household_id=household.id,
            reservation_id=reservation.id,
            metadata={
                "suspended_until": household.suspended_until.isoformat()
                if household.suspended_until
                else None,
                "strikes": household.strikes,
            },
        )

    db.commit()

    if was_promoted_from_waitlist:
        notify_household(
            db,
            household_id=household.id,
            type="NO_SHOW",
            message=(
                f"No se ha realizado check-in en la reserva promocionada desde lista de espera "
                f"para {reservation.start_at.strftime('%d/%m/%Y %H:%M')}. "
                "No se ha añadido ningún strike."
            ),
        )
    else:
        notify_household(
            db,
            household_id=household.id,
            type="NO_SHOW",
            message=(
                f"No se ha realizado check-in en la reserva de "
                f"{reservation.start_at.strftime('%d/%m/%Y %H:%M')}. "
                "Se ha añadido un strike."
            ),
        )

    if suspension_applied and household.suspended_until:
        notify_household(
            db,
            household_id=household.id,
            type="HOUSEHOLD_SUSPENDED",
            message=(
                f"La vivienda ha sido suspendida hasta "
                f"{household.suspended_until.strftime('%d/%m/%Y %H:%M')}."
            ),
        )

    db.commit()

    return household

def is_prime_time(start_at, policy: CommunityPolicy) -> bool:
    """ 
    Determina si una franja pertenece a prime time
    """
    return policy.prime_time_start_hour <= start_at.hour < policy.prime_time_end_hour

def get_cooldown_group(
    start_at,
    policy: CommunityPolicy,
) -> str | None:
    """ 
    Devuelve el grupo de cooldown de una franja
    Solo aplica a franjas prime time
    """
    if not is_prime_time(start_at, policy):
        return None
    return f"{start_at.hour:02d}:00" # Devuelve la franja en formato HH:00

def household_is_on_cooldown_for_slot(
    db: Session,
    household_id,
    facility_id: int,
    start_at,
    policy: CommunityPolicy,
) -> tuple[bool, str | None]:
    """
    Comprueba si una vivienda está en cooldown para la franja solicitada.

    La regla se aplica sobre reservas activas o ya disfrutadas/no-show/canceladas
    creadas dentro de la ventana de cooldown para el mismo grupo horario.
    """
    cooldown_group = get_cooldown_group(start_at, policy)
    if not cooldown_group: 
        return False, None # No hay cooldown si no es prime time
    
    cooldown_since = start_at - timedelta(days=policy.cooldown_days)
     
    existing = ( # si existe una reserva con el mismo grupo de cooldown y dentro de la ventana de cooldown
        db.query(Reservation)
        .filter(Reservation.household_id == household_id) # y que sea del mismo usuario
        .filter(Reservation.facility_id == facility_id)
        .filter(Reservation.cooldown_group == cooldown_group) # y que sea del mismo grupo de cooldown
        .filter(Reservation.start_at >= cooldown_since) # y que no sea una reserva que ya se ha disfrutado
        .filter( # y que no sea una reserva que ya se ha disfrutado
            Reservation.status.in_([ 
                ReservationStatus.ACTIVE.value,
                #ReservationStatus.CANCELLED.value,
                ReservationStatus.NO_SHOW.value,
                ReservationStatus.RELEASED.value,
            ])
        )
        .first() 
    )

    if existing:
        return True, cooldown_group # Devuelve True si la vivienda está en cooldown, False si no
    
    return False, None # No hay cooldown si no existe una reserva existente
