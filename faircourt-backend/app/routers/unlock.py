from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_resident
from app.models import UnlockProposal, UnlockVote, Household, User
from app.schemas import(
    UnlockProposalIn, 
    UnlockVoteIn, 
    UnlockProposalOut, 
    UnlockVoteOut,
)
from app.security import utcnow
from app.services.audit import log_event
from app.services.unlock import resolve_unlock_proposals_if_needed
from app.services.policies import get_community_policy

router = APIRouter(prefix="/unlock", tags=["unlock"]) 

# router para crear una propuesta de desbloqueo
@router.get("/proposals", response_model=list[UnlockProposalOut])
def list_unlock_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_resident),
):
    """
    Lista las propuestas de desbloqueo existentes.

    Para cada propuesta se añade el código público de vivienda
    asociado a target_household_id, de forma que el frontend pueda
    mostrar A1, B2, AT1, etc., en lugar del identificador interno.
    """
    proposals = (
        db.query(UnlockProposal)
        .filter(UnlockProposal.community_id == current_user.community_id)
        .order_by(UnlockProposal.created_at.desc())
        .all()
    )

    result = []

    for proposal in proposals:
        proposal = resolve_unlock_proposals_if_needed(db, proposal)

        household = (
            db.query(Household)
            .filter(Household.id == proposal.target_household_id)
            .filter(Household.community_id == current_user.community_id)
            .first()
        )

        result.append(
            {
                "id": proposal.id,
                "target_household_id": proposal.target_household_id,
                "target_household_code": household.code if household else None,
                "created_by_user_id": proposal.created_by_user_id,
                "reason": proposal.reason,
                "status": proposal.status,
                "created_at": proposal.created_at,
                "closes_at": proposal.closes_at,
                "resolved_at": proposal.resolved_at,
            }
        )

    return result

@router.post("/proposal", response_model=UnlockProposalOut, status_code=status.HTTP_201_CREATED)
def create_unlock_proposal(
    payload: UnlockProposalIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_resident),
):
    """
    Crea una propuesta de desbloqueo excepcional para la vivienda autenticada.

    Solo se permite crearla si la vivienda está suspendida actualmente.
    """
    household = (
        db.query(Household)
        .filter(Household.id == current_user.household_id)
        .filter(Household.community_id == current_user.community_id)
        .first()
    )

    if not household:
        raise HTTPException(
            status_code=404,
            detail="Vivienda no encontrada.",
        )

    now = utcnow()
    policy = get_community_policy(db, current_user.community_id)

    if not policy.unlock_voting_enabled:
        raise HTTPException(
            status_code=409,
            detail="Las votaciones de desbloqueo no están activadas en esta comunidad.",
        )

    if not household.suspended_until or household.suspended_until <= now:
        raise HTTPException(
            status_code=400,
            detail="La vivienda no está suspendida; no necesita desbloqueo.",
        )

    existing = (
        db.query(UnlockProposal)
        .filter(UnlockProposal.community_id == current_user.community_id)
        .filter(UnlockProposal.target_household_id == household.id)
        .filter(UnlockProposal.status == "OPEN")
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una propuesta de desbloqueo abierta para esta vivienda.",
        )

    proposal = UnlockProposal(
        community_id=current_user.community_id,
        target_household_id=household.id,
        created_by_user_id=current_user.id,
        reason=payload.reason,
        status="OPEN",
        created_at=now,
        closes_at=now + timedelta(hours=policy.unlock_voting_hours),
    )

    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    log_event(
        db,
        event="UNLOCK_VOTE_CREATED",
        household_id=household.id,
        user_id=current_user.id,
        metadata={
            "proposal_id": proposal.id,
            "reason": proposal.reason,
            "closes_at": proposal.closes_at.isoformat(),
        },
    )
    db.commit()

    return {
        "id": proposal.id,
        "target_household_id": proposal.target_household_id,
        "target_household_code": household.code if household else None,
        "created_by_user_id": proposal.created_by_user_id,
        "reason": proposal.reason,
        "status": proposal.status,
        "created_at": proposal.created_at,
        "closes_at": proposal.closes_at,
        "resolved_at": proposal.resolved_at,
    }

# Router para votar
@router.post("/proposal/{proposal_id}/vote", response_model=UnlockVoteOut, status_code=status.HTTP_201_CREATED)
def cast_unlock_vote(
    proposal_id: int, 
    payload: UnlockVoteIn, 
    db: Session = Depends(get_db),
    current_user = Depends(require_resident),
): 
    # Convertimos el voto a mayúsculas
    vote_value = payload.vote.upper() 
    if vote_value not in {"YES", "NO"}: 
        raise HTTPException(status_code=400, detail="El voto debe ser YES o NO")

    # Buscamos la propuesta
    proposal = (
        db.query(UnlockProposal)
        .filter(UnlockProposal.id == proposal_id)
        .filter(UnlockProposal.community_id == current_user.community_id)
        .first()
    )
    if not proposal: 
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    policy = get_community_policy(db, current_user.community_id)
    if not policy.unlock_voting_enabled:
        raise HTTPException(
            status_code=409,
            detail="Las votaciones de desbloqueo no están activadas en esta comunidad.",
        )

    # Resolvemos la propuesta
    proposal = resolve_unlock_proposals_if_needed(db, proposal) 
    if proposal.status != "OPEN": 
        raise HTTPException(status_code=400, detail="La propuesta ya no está abierta") 

    # Verificamos que la vivienda no sea la misma que la propuesta
    if proposal.target_household_id == current_user.household_id: 
        raise HTTPException(status_code=403, detail="La vivienda afectada no puede votar en su propia propuesta.") 

    # Obtenemos la vivienda del usuario
    voter_household = (
        db.query(Household)
        .filter(Household.id == current_user.household_id)
        .filter(Household.community_id == current_user.community_id)
        .first()
    )
    now = utcnow() 
 
    # Verificamos que la vivienda esté activa
    if not voter_household or not voter_household.is_active: 
        raise HTTPException(status_code=403, detail="Tu vivienda no está activa")

    # Verificamos que la vivienda no esté suspendida
    if voter_household.suspended_until and voter_household.suspended_until > now: 
        raise HTTPException(status_code=403, detail="Tu vivienda está suspendida, no puedes votar.")  
    
    # Verificamos que la vivienda no haya votado ya
    existing_vote = (
        db.query(UnlockVote) 
        .filter(UnlockVote.proposal_id == proposal_id) 
        .filter(UnlockVote.voter_household_id == current_user.household_id) 
        .first() 
    )

    # Si la vivienda ya ha votado, lanzamos error
    if existing_vote: 
        raise HTTPException(status_code=409, detail="Tu vivienda ya ha votado para esta propuesta") 

    # Creamos el voto
    vote = UnlockVote(
        community_id=current_user.community_id,
        proposal_id=proposal_id, 
        voter_household_id = current_user.household_id,
        vote = vote_value, 
    )

    db.add(vote)
    db.commit() 
    db.refresh(vote)

    log_event(
        db, 
        event="UNLOCK_VOTE_CAST",
        household_id=current_user.household_id, 
        user_id=current_user.id, 
        metadata = {
            "proposal_id": proposal.id, 
            "vote": vote.vote, 
        }, 
    ) 
    db.commit() 
 
    resolve_unlock_proposals_if_needed(db, proposal) 

    return vote
