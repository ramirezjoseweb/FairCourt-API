from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.db import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])

# Endpoint que obtiene los logs de auditoría del usuario autenticado 
@router.get("/me", response_model=list[AuditLogOut])
def get_my_audit_logs(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
):
    # Filtra los logs de auditoría por el ID de la vivienda del usuario autenticado
    entries = (
        db.query(AuditLog) 
        .filter(AuditLog.household_id == current_user.household_id)
        .order_by(AuditLog.created_at.desc())
        .all() 
    )
    return entries
