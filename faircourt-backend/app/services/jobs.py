from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Reservation, ReservationStatus, UnlockProposal
from app.security import utcnow
from app.services.rules import (
    is_reservation_no_show,
    apply_no_show_penalty,
    try_promote_waitlist_for_slot,
)
from app.services.unlock import resolve_unlock_proposals_if_needed

def process_no_shows_job() -> None: 
    """
    Job programado que procesa automáticamente las reservas en no-show.

    Flujo:
    - busca reservas ACTIVE
    - comprueba si expiró la ventana de check-in
    - marca NO_SHOW
    - aplica strike/suspensión
    - intenta promocionar waitlist
    """
    db: Session = SessionLocal() 

    try: 
        now = utcnow() 

        candidate_reservations = (
            db.query(Reservation)
            .filter(Reservation.status == ReservationStatus.ACTIVE.value) 
            .all() 
        )

        processed = 0 
        no_show_count = 0 
        promoted_count = 0 

        # para cada reserva activa 
        for reservation in candidate_reservations: 
            processed += 1 

            # si no es no-show, pasamos a la siguiente 
            if not is_reservation_no_show(reservation, now): 
                continue

            # aplicamos la penalización de no-show 
            apply_no_show_penalty(db, reservation, now) 
            no_show_count += 1 

            # intentamos promocionar la lista de espera 
            promoted = try_promote_waitlist_for_slot(db, reservation.start_at)
            if promoted: 
                promoted_count += 1 

        # si hay no-shows, mostramos un resumen 
        if no_show_count > 0: 
            print(f"[JOB process_no_shows] Revisadas={processed} "
            f"NoShow={no_show_count} Promocionadas={promoted_count}"
            )

        if no_show_count <= 0: 
            print(f"[JOB process_no_shows] No se encontraron reservas en no-show")
            
    # si hay error, lo mostramos 
    except Exception as e: 
        print(f"[JOB process_no_shows] Error: {e}")
    finally:
        db.close() 

def process_expired_unlock_proposals_job() -> None: 
    """
    Procesa propuestas de desbloqueo abiertas para marcar como expiradas las que hayan superado su fecha de cierre
    """
    db = SessionLocal() 
    try: 
        open_proposals = (
            db.query(UnlockProposal)
            .filter(UnlockProposal.status == "OPEN")
            .all() 
        )

        processed = 0 

        for proposal in open_proposals: 
            previous_status = proposal.status
            resolve_unlock_proposals_if_needed(db, proposal) 

            if previous_status == "OPEN" and proposal.status == "EXPIRED":
                processed += 1 

        if processed > 0: 
            print(f"[JOB] Propuestas expiradas procesadas: {processed}")

    finally: 
        db.close()