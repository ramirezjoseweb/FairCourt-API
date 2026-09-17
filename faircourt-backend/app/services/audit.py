import json 

from sqlalchemy.orm import Session
from app.models import (
    AuditLog,
    AuditVisibility,
    Household,
    Reservation,
    User,
)

# Función para registrar eventos
def log_event(
    db: Session, 
    event: str, 
    household_id: int | None = None, 
    user_id: int | None = None, 
    reservation_id: int | None = None, 
    metadata: dict | None = None, 
    community_id: int | None = None,
    visibility: str = AuditVisibility.RESIDENT.value,
) -> None: 
    community_ids = {community_id} if community_id is not None else set()
    if household_id is not None:
        household = db.get(Household, household_id)
        if household:
            community_ids.add(household.community_id)
    if user_id is not None:
        user = db.get(User, user_id)
        if user and user.community_id is not None:
            community_ids.add(user.community_id)
    if reservation_id is not None:
        reservation = db.get(Reservation, reservation_id)
        if reservation:
            community_ids.add(reservation.community_id)
    if len(community_ids) != 1:
        raise ValueError("El evento de auditoría debe pertenecer a una única comunidad.")

    # Crea una entrada en el registro de auditoría
    entry = AuditLog(
        community_id=community_ids.pop(),
        event=event, # Tipo de evento
        visibility=visibility,
        household_id=household_id, # ID de la vivienda
        user_id=user_id, # ID del usuario
        reservation_id=reservation_id, # ID de la reserva
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False), # Convierte el diccionario de metadatos en una cadena JSON
    )
    db.add(entry) 
    db.flush()


def log_admin_event(
    db: Session,
    event: str,
    admin_user_id: int,
    community_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    """Registra una acción visible únicamente en la auditoría administrativa."""
    admin = db.get(User, admin_user_id)
    if not admin or admin.role != "platform_admin":
        raise ValueError("La auditoría administrativa requiere un platform_admin.")
    entry = AuditLog(
        community_id=community_id,
        event=event,
        visibility=AuditVisibility.ADMIN.value,
        user_id=admin_user_id,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
    )
    db.add(entry)
    db.flush()
