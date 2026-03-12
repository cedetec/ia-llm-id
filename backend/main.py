from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.health import router as health_router
from backend.api.routes.documentos import router as documentos_router
from backend.api.routes.consulta import router as consulta_router
from backend.api.routes import admin

app = FastAPI(title="Asistente I+D Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documentos_router)
app.include_router(consulta_router)
app.include_router(admin.router)
