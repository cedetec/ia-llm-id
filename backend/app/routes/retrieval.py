# app/routes/retrieval.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import app.startup as startup

router = APIRouter()

class RetrieveRequest(BaseModel):
    pregunta: str
    rag: str
    modelo: Optional[str] = None
    documento: Optional[str] = None

class ContextDocument(BaseModel):
    page_content: str
    metadata: dict

class RetrieveResponse(BaseModel):
    context: List[ContextDocument]
    context_text: str
    contextos_ragas: List[str]
    # metricas: dict (omitiendo por simplicidad de serialización)

def _obtener_rag_service(rag: str):
    if rag == "nomic":
        return startup.rag_nomic, "NOMIC"
    elif rag == "embeddinggemma":
        return startup.rag_gemma, "EMBEDDINGGEMMA"
    else:
        raise HTTPException(
            status_code=400,
            detail="RAG no válido. Use 'nomic' o 'embeddinggemma'."
        )


@router.post("/reload")
def reload_rag():
    startup.reinicializar_rag()
    return {
        "ok": True,
        "mensaje": "Servicios RAG recargados correctamente."
    }


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(body: RetrieveRequest):

    rag_service, rag_nombre = _obtener_rag_service(body.rag)

    if rag_service is None:
        startup.reinicializar_rag()
        rag_service, rag_nombre = _obtener_rag_service(body.rag)

    if rag_service is None:
        raise HTTPException(
            status_code=503,
            detail=f"El servicio RAG {rag_nombre} no está disponible."
        )

    if body.modelo:
        rag_service.cambiar_modelo(body.modelo)

    try:
        from RAG.evaluation.rag_metrics import RAGMetrics
        from RAG.rag.context_builder import construir_contexto
        from RAG.rag.document_detector import detectar_documentos

        metricas = RAGMetrics()
        pregunta_busqueda = body.pregunta.lower()

        documentos_detectados = detectar_documentos(body.pregunta)
        documentos_relevantes = None
        if len(documentos_detectados) > 1:
            documentos_relevantes = [
                [item["documento"], item["anio"]]
                for item in documentos_detectados
            ]

        try:
            documentos = rag_service.pipeline.recuperar(
                pregunta_busqueda,
                body.pregunta,
                metricas,
                documento=body.documento,
                documentos_relevantes=documentos_relevantes
            )
        except Exception:
            # Si la colección de Chroma fue recreada al reindexar, recargar y reintentar
            startup.reinicializar_rag()
            rag_service, rag_nombre = _obtener_rag_service(body.rag)
            if rag_service is None:
                raise
            documentos = rag_service.pipeline.recuperar(
                pregunta_busqueda,
                body.pregunta,
                metricas,
                documento=body.documento,
                documentos_relevantes=documentos_relevantes
            )

        contextos_ragas = [doc.page_content for doc in documentos]
        contexto_texto = construir_contexto(documentos)

        # Mapear a diccionarios
        docs_dict = []
        for doc in documentos:
            docs_dict.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })

        return RetrieveResponse(
            context=docs_dict,
            context_text=contexto_texto,
            contextos_ragas=contextos_ragas
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
