import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.indexing import router as indexing_router
from app.routes.database import router as database_router

app = FastAPI(
    title="Backend RAG",
    version="1.0.0"
)

# =====================================================
# Configuración de CORS
# =====================================================

#CORS_ORIGINS = [
#    origin.strip()
#    for origin in os.getenv(
#        "CORS_ORIGINS",
#        "https://iac-id.cedetec.cl:5173"
#    ).split(",")
#    if origin.strip()
#]

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["https://iac-id.cedetec.cl"],
    allow_origins=["https://iac-id.cedetec.cl", "http://localhost:5173"],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Routers
# =====================================================

app.include_router(
    database_router
)

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(indexing_router)
