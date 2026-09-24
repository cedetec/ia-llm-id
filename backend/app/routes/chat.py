# app/routes/chat.py

import time

from fastapi import APIRouter, HTTPException

from app.schemas_old import Pregunta

import app.startup as startup

from LLM.response.response_generation_service import (
    generar_respuesta
)

from app.database.conversation_repository import (
    crear_conversacion,
    agregar_mensaje
)

router = APIRouter()


@router.post("/chat")
def chat(body: Pregunta):

    #
    # Seleccionar RAG según la interfaz.
    #

    if body.rag == "nomic":

        rag_service = startup.rag_nomic

        rag_nombre = "NOMIC"

    elif body.rag == "embeddinggemma":

        rag_service = startup.rag_gemma

        rag_nombre = "EMBEDDINGGEMMA"

    else:

        raise HTTPException(

            status_code=400,

            detail=(
                "RAG no válido. "
                "Use 'nomic' o 'embeddinggemma'."
            )

        )

    #
    # Verificar que el RAG seleccionado esté disponible.
    #

    if rag_service is None:

        raise HTTPException(

            status_code=503,

            detail=(
                f"El servicio RAG {rag_nombre} "
                "no está disponible."
            )

        )

    #
    # Crear conversación si no existe.
    #

    conversation_id = body.conversation_id

    if conversation_id is None:

        conversation_id = crear_conversacion()

    #
    # Guardar pregunta del usuario.
    #

    agregar_mensaje(

        conversation_id=conversation_id,

        rol="user",

        contenido=body.pregunta

    )

    #
    # Aplicar modelo seleccionado desde la interfaz.
    #

    if body.modelo:

        rag_service.cambiar_modelo(

            body.modelo

        )

    print("=" * 80)

    print("[CHAT DEBUG]")

    print(
        "RAG solicitado:",
        body.rag
    )

    print(
        "RAG activo:",
        rag_nombre
    )

    print(
        "Modelo solicitado:",
        body.modelo
    )

    print(
        "RAG Service:",
        rag_service
    )

    try:

        print(
            "Modelo activo:",
            rag_service.llm.model
        )

    except Exception as e:

        print(
            "[MODEL DEBUG ERROR]",
            repr(e)
        )

    try:

        vectorstore = (
            rag_service
            .pipeline
            .retriever
            .vectorstore
        )

        print(
            "collection name:",
            vectorstore._collection.name
        )

        print(
            "collection id:",
            vectorstore._collection.id
        )

        print(
            "collection count:",
            vectorstore._collection.count()
        )

    except Exception as e:

        print(
            "[CHAT DEBUG ERROR]",
            repr(e)
        )

    print("=" * 80)

    inicio = time.perf_counter()

    #
    # Ejecutar RAG seleccionado.
    #

    resultado = generar_respuesta(
        rag_service,
        body.pregunta
    )

    tiempo = round(
        time.perf_counter() - inicio,
        2
    )

    respuesta = resultado["answer"]

    #
    # Guardar respuesta del asistente.
    #

    agregar_mensaje(

        conversation_id=conversation_id,

        rol="assistant",

        contenido=respuesta

    )

    documentos = resultado.get(
        "context",
        []
    )

    documentos_nombres = list(
        dict.fromkeys(
            doc.metadata.get("documento")
            for doc in documentos
            if doc.metadata.get("documento")
        )
    )

    modelo = getattr(
        rag_service.llm,
        "model",
        body.modelo or "-"
    )

    chunks = len(documentos)

    tokens = len(
        respuesta.split()
    )

    score = None

    if documentos:

        scores = [
            doc.metadata.get(
                "rerank_score"
            )
            for doc in documentos
            if doc.metadata.get(
                "rerank_score"
            ) is not None
        ]

        if scores:

            score = max(
                scores
            )

    return {

        "conversation_id": conversation_id,

        "respuesta": respuesta,

        "documento": ", ".join(
            documentos_nombres
        ),
        
        "modelo": modelo,

        "tiempo": f"{tiempo} s",

        "chunks": chunks,

        "tokens": tokens,

        "score": score

    }