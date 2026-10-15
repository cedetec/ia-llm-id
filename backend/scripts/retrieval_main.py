import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.retrieval import router as retrieval_router
from app.routes.health import router as health_router

app = FastAPI(
    title="Backend Retrieval Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieval_router)
app.include_router(health_router)
