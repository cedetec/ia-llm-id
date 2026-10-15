# app/routes/chat.py

import time
from fastapi import APIRouter, HTTPException

from app.schemas_old import Pregunta
from LLM.response.response_generation_service import generar_respuesta
from app.database.conversation_repository import crear_conversacion, agregar_mensaje

# Importar cliente de Ollama
from LLM.llm.ollama_client import crear_llm
from RAG.config.llm_config import cambiar_modelo

router = APIRouter()

@router.post("/chat")
def chat(body: Pregunta):
    if body.rag not in ["nomic", "embeddinggemma"]:
        raise HTTPException(
            status_code=400,
            detail="RAG no válido. Use 'nomic' o 'embeddinggemma'."
        )

    conversation_id = body.conversation_id
    if conversation_id is None:
        conversation_id = crear_conversacion()

    agregar_mensaje(
        conversation_id=conversation_id,
        rol="user",
        contenido=body.pregunta
    )

    if body.modelo:
        cambiar_modelo(body.modelo)
    
    # Crear el LLM específicamente para esta request usando el modelo proporcionado
    llm_local = crear_llm(body.modelo)

    inicio = time.perf_counter()

    # Ejecutar la generación, la cual hace el HTTP POST al Retrieval
    resultado = generar_respuesta(
        llm=llm_local,
        pregunta=body.pregunta,
        rag_name=body.rag,
        modelo=body.modelo
    )

    tiempo = round(time.perf_counter() - inicio, 2)
    respuesta = resultado["answer"]

    agregar_mensaje(
        conversation_id=conversation_id,
        rol="assistant",
        contenido=respuesta
    )

    documentos = resultado.get("context", [])
    documentos_nombres = list(
        dict.fromkeys(
            doc.metadata.get("documento")
            for doc in documentos
            if doc.metadata.get("documento")
        )
    )

    modelo_nombre = getattr(llm_local, "model", body.modelo or "-")
    chunks = len(documentos)
    tokens = len(respuesta.split())
    score = None

    if documentos:
        scores = [
            doc.metadata.get("rerank_score")
            for doc in documentos
            if doc.metadata.get("rerank_score") is not None
        ]
        if scores:
            score = max(scores)

    # Extraer los textos de los documentos para enviarlos al usuario
    extractos = [doc.page_content for doc in documentos]

    return {
        "conversation_id": conversation_id,
        "respuesta": respuesta,
        "documento": ", ".join(documentos_nombres),
        "modelo": modelo_nombre,
        "tiempo": f"{tiempo} s",
        "chunks": chunks,
        "tokens": tokens,
        "score": score,
        "extractos": extractos
    }