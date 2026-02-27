from fastapi import FastAPI
from .db import engine
from . import models

app = FastAPI(title="FairCourt API")

# Para empezar rápido, creamos tablas así.
# Luego lo sustituimos por Alembic (migraciones) cuando lo inicialicemos.
models.Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

""" 
.\.venv\Scripts\activate
uvicorn app.main:app --reload
 """