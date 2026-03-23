from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.consulta_service import procesar_consulta
from backend.services.consulta.validacion_consulta import es_consulta_id

router = APIRouter(prefix="/consulta", tags=["consulta"])

class ConsultaIn(BaseModel):
    pregunta: str

@router.post("")
def consultar(data: ConsultaIn):

    pregunta = data.pregunta

    # 🔥 VALIDACIÓN DE DOMINIO
    if not es_consulta_id(pregunta):
        return {
            "respuesta": "Consulta no válida. Este asistente responde solo preguntas sobre fondos concursables, financiamiento e investigación y desarrollo (I+D).",
            "fuente": "Sistema",
            "score_semantico": 0,
            "score_lexico": 0
        }

    try:
        return procesar_consulta(pregunta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
