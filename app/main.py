"""
Módulo principal de la aplicación FairCourt API.

Este archivo:

- Inicializa la aplicación FastAPI.
- Configura metadatos básicos del servicio.
- Define endpoints básicos del sistema (por ejemplo, health check).
- Importa los modelos para que SQLAlchemy registre las tablas.

Este módulo actúa como punto de entrada del backend.
"""


from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

from .db import engine
from . import models

# ---------------------------------------------------------------------
# Inicialización de la aplicación
# ---------------------------------------------------------------------

app = FastAPI(
    title="FairCourt API",
    description="API para la gestión de reservas de pistas de pádel.",
    version="0.1.0",
)

app.include_router(auth_router) 
app.include_router(users_router)

# Para empezar rápido, creamos tablas así.
# Luego lo sustituimos por Alembic (migraciones) cuando lo inicialicemos.

@app.get("/health")
def health():
    """
    Endpoint de health check.

    Responde con un estado "ok" si la aplicación está funcionando correctamente.
    """

    return {"status": "ok"}


# ---------------------------------------------------------------------
# Instrucciones de ejecución (solo informativas)
# ---------------------------------------------------------------------

"""
Para ejecutar la aplicación en entorno de desarrollo:

1. Activar el entorno virtual:
   .\.venv\Scripts\activate

2. Lanzar el servidor:
   uvicorn app.main:app --reload

El parámetro --reload permite recargar automáticamente
el servidor ante cambios en el código.
"""