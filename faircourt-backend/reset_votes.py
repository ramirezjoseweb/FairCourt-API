from app.db import SessionLocal
from app.models import UnlockVote

def main() -> None: 
    db = SessionLocal() 
    try: 
        deleted_votes = db.query(UnlockVote).delete() 
        db.commit() 

        print(f"✅ Votos reseteados: {deleted_votes} votos.")
    except Exception as e: 
        db.rollback()
        print(f"❌ Error al resetear votos: {e}")
    finally: 
        db.close() 

if __name__ == "__main__": 
    main() 