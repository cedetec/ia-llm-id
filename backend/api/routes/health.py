from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/ping")
def ping():
    return {
        "service": "Asistente I+D Backend",
        "status": "ok"
    }