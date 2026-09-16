from sqlalchemy.orm import Session 
from app.models import Household, Notification, User

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
    user = db.get(User, user_id)
    household = db.get(Household, household_id)
    if (
        not user
        or not household
        or user.community_id != household.community_id
        or user.household_id != household.id
    ):
        raise ValueError("Usuario y vivienda deben pertenecer a la misma comunidad.")

    notification = Notification(
        community_id=household.community_id,
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
    household = db.get(Household, household_id)
    if not household:
        return None

    user = (
        db.query(User)
        .filter(User.household_id == household_id)
        .filter(User.community_id == household.community_id)
        .first()
    )

    if not user: 
        return None

    return create_notification(
        db=db,
        user_id=user.id,
        household_id=household_id,
        type=type,
        message=message,
    )
