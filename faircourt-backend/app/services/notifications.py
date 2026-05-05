from sqlalchemy.orm import Session 
from app.models import Notification, User

def create_notification(
    db: Session,
    user_id: int, 
    household_id: int, 
    type: str, 
    message: str
) -> Notification: 
    """ 
    Crea una notificación interna para una vivienda/usuario
    """
    notification = Notification(
        user_id=user_id, 
        household_id=household_id, 
        type=type, 
        message=message,
    )

    db.add(notification)
    db.flush() 

    return notification

def notify_household(
    db: Session, 
    household_id: int, 
    type: str, 
    message: str,
) -> Notification | None: 
    """ 
    Notifica al usuario asociado a una vivienda
    """
    user = db.query(User).filter(User.household_id == household_id).first()

    if not user: 
        return None

    return create_notification(
        db=db,
        user_id=user.id,
        household_id=household_id,
        type=type,
        message=message,
    )