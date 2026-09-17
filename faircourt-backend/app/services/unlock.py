from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import UnlockProposal, UnlockVote, Household
from app.services.audit import log_event
from app.services.notifications import notify_household
from app.security import utcnow
from app.services.policies import get_community_policy

# Este archivo se encarga de la lógica de desbloqueo de cuentas

def resolve_unlock_proposals_if_needed(db: Session, proposal: UnlockProposal): 
    """
    Revisa si una propuesta debe aprobarse o rechazarse
    en función de los votos y del tiempo.
    """ 
    if proposal.status != "OPEN": 
        return proposal

    now = utcnow() 
    policy = get_community_policy(db, proposal.community_id)

    votes = (
        db.query(UnlockVote)
        .filter(UnlockVote.proposal_id == proposal.id)
        .filter(UnlockVote.community_id == proposal.community_id)
        .all()
    ) # Obtiene los votos de la propuesta
    yes_votes = sum(1 for v in votes if v.vote == "YES") # Cuenta los votos a favor
    no_votes = sum(1 for v in votes if v.vote == "NO") # Cuenta los votos en contra

    # SI SE ACEPTA LA PROPUESTA
    should_approve = (
        # Si los votos positivos son >= 2 y mayor que los votos negativos, deberia aprobarse la petición y levantar el bloqueo
        yes_votes >= policy.unlock_min_yes_votes
        and yes_votes > no_votes
    )

    if should_approve: # Si debe aprobarse el status pasa a aprobado y se rellena el campo resolved_at con now 
        proposal.status = "APPROVED" 
        proposal.resolved_at = now

        household = (
            db.query(Household)
            .filter(Household.id == proposal.target_household_id)
            .filter(Household.community_id == proposal.community_id)
            .first()
        )
        # si el household es igual al household_id de la propuesta entonces se libera y resetean los strikes 
        if household: 
            household.suspended_until = None 
            household.strikes = household.strikes - 1 
            household.is_active = True

        # Lanzamos notificación
        notify_household(
        db,
        household_id=proposal.target_household_id,
        type="ACCOUNT_UNLOCKED",
        message=f"Tu cuenta ha sido desbloqueada.",
    )
    db.commit()

    log_event(
        db, 
        event="UNLOCK_APPROVED",
        household_id=proposal.target_household_id, 
        metadata={
            "proposal_id": proposal.id, 
            "yes_votes": yes_votes, 
            "no_votes": no_votes,
        },
    )
    db.commit()
    db.refresh(proposal)

    # SI SE RECHAZA LA PROPUESTA
    should_reject = (
        # Si los votos negativos son 2 o mas, votos negativos son mayores que los positivos o ahora es superior a la fecha de cierre de la propuesta
        no_votes >= policy.unlock_min_yes_votes
        and no_votes > yes_votes
    )

    if should_reject: 
        proposal.status= "REJECTED"
        proposal.resolved_at= now

        log_event(
            db, 
            event="UNLOCK_REJECTED", 
            household_id = proposal.target_household_id, 
            metadata={
                "proposal_id": proposal.id,
                "yes_votes": yes_votes, 
                "no_votes": no_votes, 
                "reason": "NOT_ENOUGH_YES_VOTES"
            },
        )
        db.commit() 
        db.refresh(proposal) 

    # SI EXPIRA LA PROPUESTA
    should_expire = now > proposal.closes_at # should_expire cuando now sea superior a la fecha en la que se cierra el proposal

    if should_expire: 
        proposal.status = "EXPIRED" 
        proposal.resolved_at = now 

        log_event(
            db, 
            event = "UNLOCK_EXPIRED", 
            household_id = proposal.target_household_id, 
            metadata = {
                "proposal_id": proposal.id, 
                "yes_votes": yes_votes, 
                "no_votes": no_votes,
                "reason": "EXPIRED", 
            },
        )
        db.commit() 
        db.refresh(proposal) 
    
    return proposal
