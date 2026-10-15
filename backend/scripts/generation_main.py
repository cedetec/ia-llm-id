import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.database import router as database_router
from app.routes.indexing import router as indexing_router

app = FastAPI(
    title="Backend Generation Service",
    version="1.0.0"
)

# Permitir configuración de CORS por variable de entorno
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "https://iac-id.cedetec.cl,http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(database_router)
app.include_router(indexing_router)
