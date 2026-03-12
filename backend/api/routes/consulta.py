# backend/api/routes/consulta.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.consulta_service import procesar_consulta

router = APIRouter(prefix="/consulta", tags=["consulta"])

class ConsultaIn(BaseModel):
    pregunta: str

@router.post("")
def consultar(data: ConsultaIn):
    try:
        return procesar_consulta(data.pregunta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))