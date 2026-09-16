from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Community, Reservation, ReservationStatus, UnlockProposal
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
            .join(Community, Community.id == Reservation.community_id)
            .filter(Community.is_active.is_(True))
            .filter(Reservation.status == ReservationStatus.ACTIVE.value)
            .all()
        )

        processed = 0
        no_show_count = 0
        promoted_count = 0

        for reservation in candidate_reservations:
            processed += 1

            try:
                if not is_reservation_no_show(reservation, now):
                    continue

                apply_no_show_penalty(db, reservation, now)
                no_show_count += 1

                promoted = try_promote_waitlist_for_slot(
                    db, reservation.facility_id, reservation.start_at
                )

                if promoted:
                    promoted_count += 1

            except Exception as exc:
                db.rollback()
                print(
                    "[JOB process_no_shows] Error procesando reserva "
                    f"id={reservation.id}, start_at={reservation.start_at}, "
                    f"end_at={reservation.end_at}: {exc}"
                )

        if no_show_count > 0:
            print(
                f"[JOB process_no_shows] Revisadas={processed} "
                f"NoShow={no_show_count} Promocionadas={promoted_count}"
            )
        else:
            print("[JOB process_no_shows] No se encontraron reservas en no-show")

    except Exception as exc:
        db.rollback()
        print(f"[JOB process_no_shows] Error general: {exc}")

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
            .join(Community, Community.id == UnlockProposal.community_id)
            .filter(Community.is_active.is_(True))
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
