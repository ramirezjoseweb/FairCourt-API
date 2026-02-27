from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./faircourt.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario en SQLite con FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        """
    Dependency de FastAPI para proporcionar una sesión de BD por petición.

    Abre una sesión al inicio de la request y garantiza el cierre al finalizar,
    evitando fugas de conexiones y asegurando un scope transaccional controlado.
    """