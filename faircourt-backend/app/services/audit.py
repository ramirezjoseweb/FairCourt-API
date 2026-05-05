import json 

from sqlalchemy.orm import Session
from app.models import AuditLog

# Función para registrar eventos
def log_event(
    db: Session, 
    event: str, 
    household_id: int | None = None, 
    user_id: int | None = None, 
    reservation_id: int | None = None, 
    metadata: dict | None = None, 
) -> None: 
    # Crea una entrada en el registro de auditoría
    entry = AuditLog(
        event=event, # Tipo de evento
        household_id=household_id, # ID de la vivienda
        user_id=user_id, # ID del usuario
        reservation_id=reservation_id, # ID de la reserva
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False), # Convierte el diccionario de metadatos en una cadena JSON
    )
    db.add(entry) 
    db.flush() 