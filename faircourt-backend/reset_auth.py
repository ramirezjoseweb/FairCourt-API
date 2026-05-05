"""
reset_auth.py

Resetea el estado de autenticación:
- Borra todos los usuarios (users)
- Borra todos los OTPs (auth_otps)

Mantiene:
- Lista blanca de viviendas (households)

Uso:
    python reset_auth.py
""" 

from app.db import SessionLocal
from app.models import User, AuthOTP, Reservation, WaitlistEntry, Household, AuditLog, UnlockVote, Notification

def main() -> None: 
    db = SessionLocal() 
    try: 
        #Orden importa si hay FKs: primero OTPs, luego users
        deleted_otps = db.query(AuthOTP).delete()
        deleted_users = db.query(User).delete()
        deleted_reservations = db.query(Reservation).delete() 
        deleted_waitlist = db.query(WaitlistEntry).delete() 
        deleted_votes = db.query(UnlockVote).delete()
        db.query(Household).update({Household.strikes: 0, Household.suspended_until: None}) 
        db.query(Household).update({Household.is_active: True}) 
        deleted_audit_logs = db.query(AuditLog).delete() 
        deleted_notifications = db.query(Notification).delete() 
        db.commit() 

        print(f"✅ Auth reseteado: {deleted_users} usuarios, {deleted_otps} OTPs, {deleted_reservations} reservas, {deleted_waitlist} listas de espera, {deleted_audit_logs} logs de auditoría, {deleted_votes} votos, {deleted_notifications} notificaciones y strikes reiniciados.")
    except Exception as e: 
        db.rollback()
        print(f"❌ Error al resetear auth: {e}")
    finally: 
        db.close() 

if __name__ == "__main__": 
    main() 