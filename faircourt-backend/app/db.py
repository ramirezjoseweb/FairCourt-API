"""
Módulo de configuración de base de datos.

Este módulo se encarga de:

- Crear el motor de conexión (engine) de SQLAlchemy.
- Configurar la factoría de sesiones (SessionLocal).
- Definir la clase base para los modelos ORM.
- Proporcionar una dependencia de FastAPI para gestionar
  una sesión de base de datos por cada petición HTTP.

La aplicación utiliza SQLite como base de datos ligera y local,
lo cual encaja con la arquitectura offline-first del sistema.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./faircourt.db"
"""
URL de conexión a la base de datos SQLite.

La base de datos se almacena como un fichero local (faircourt.db),
permitiendo persistencia en entorno offline sin necesidad de un
servidor externo de base de datos.
"""

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario en SQLite con FastAPI
)
"""
Instancia del motor de SQLAlchemy.

El parámetro `check_same_thread=False` es obligatorio cuando se usa
SQLite junto con FastAPI, ya que este framework puede manejar
peticiones en múltiples hilos (multi-threading). Sin esta opción,
SQLite lanzaría errores al reutilizar conexiones entre hilos.
"""

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
Factoría de sesiones de base de datos.

Crea sesiones de SQLAlchemy con las siguientes características:
- autocommit=False: Las operaciones no se confirman automáticamente.
  Se requiere un `db.commit()` explícito para guardar cambios.
- autoflush=False: Las operaciones de base de datos no se envían
  automáticamente a la base de datos. Se requiere un `db.flush()`
  explícito para sincronizar el estado de la sesión con la BD.
- bind=engine: Las sesiones están vinculadas al motor de conexión creado
  previamente.
"""

class Base(DeclarativeBase):
    pass
"""
Clase base para todos los modelos ORM.

Herencia de `DeclarativeBase` proporciona funcionalidades declarativas
para la definición de modelos, incluyendo:
- Mapeo automático de tablas basado en atributos de clase.
- Columnas definidas con tipos de datos de SQLAlchemy.
- Relaciones entre tablas.
- Metadatos para la generación de esquemas.
"""

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