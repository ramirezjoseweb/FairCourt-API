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
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.reservations import router as reservations_router
from app.scheduler import start_scheduler, shutdown_scheduler
from app.routers.audit import router as audit_router
from app.routers.unlock import router as unlock_router
from app.routers.notifications import router as notifications_router


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router) 
app.include_router(users_router)
app.include_router(reservations_router) 
app.include_router(audit_router)
app.include_router(unlock_router)
app.include_router(notifications_router)

@app.on_event("startup") 
def on_startup(): 
    start_scheduler() 

@app.on_event("shutdown") 
def on_shutdown(): 
    shutdown_scheduler() 

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

npm run dev
npm run build
npm run preview
"""