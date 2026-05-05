from app.db import SessionLocal
from app.models import Reservation

def main() -> None: 
    db = SessionLocal() 
    try: 
        deleted_reservations = db.query(Reservation).delete() 
        db.commit() 

        print(f"✅ Reservas reseteadas: {deleted_reservations} reservas.")
    except Exception as e: 
        db.rollback()
        print(f"❌ Error al resetear reservas: {e}")
    finally: 
        db.close() 

if __name__ == "__main__": 
    main() 