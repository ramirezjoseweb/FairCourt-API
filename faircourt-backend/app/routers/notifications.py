from app.models import Household
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Notification, User
from app.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"]) 

@router.get("/me", response_model=list[NotificationOut])
def list_my_notifications(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) 
): 
    """ 
    Devuelve las notificaciones del usuario autenticado
    """
    return(
        db.query(Notification)
        .filter(Notification.community_id == current_user.community_id)
        .filter(Notification.household_id == current_user.household_id)
        .order_by(Notification.created_at.desc()) 
        .all() 
    )

@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_as_read(
    notification_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
): 
    """ 
    Marca una notificación como leida
    """ 
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id) 
        .filter(Notification.community_id == current_user.community_id)
        .first()
    )

    # Si no se encuentra ninguna notificacion
    if not notification: 
        raise HTTPException(status_code=404, detail="Notificación no encontrada.") 

    # Si el id de la notificacion es diferente al id de la vivienda 
    if notification.household_id != current_user.household_id: 
        raise HTTPException(status_code=403, detail="No puedes modificar esta notificación.") 

    notification.is_read = True 
    db.commit()
    db.refresh(notification) 

    return notification
