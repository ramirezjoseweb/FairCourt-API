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
from app.models import User, AuthOTP 

def main() -> None: 
    db = SessionLocal() 
    try: 
        #Orden importa si hay FKs: primero OTPs, luego users
        deleted_otps = db.query(AuthOTP).delete()
        deleted_users = db.query(User).delete()
        db.commit() 

        print(f"✅ Auth reseteado: {deleted_users} usuarios y {deleted_otps} OTPs eliminados.")
    except Exception as e: 
        db.rollback()
        print(f"❌ Error al resetear auth: {e}")
    finally: 
        db.close() 

if __name__ == "__main__": 
    main() 