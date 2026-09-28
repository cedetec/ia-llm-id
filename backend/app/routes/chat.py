# app/routes/chat.py

import time

from fastapi import APIRouter, HTTPException
from langchain_core.prompts import ChatPromptTemplate

from app.schemas_old import Pregunta

import app.startup as startup

from app.database.conversation_repository import (
    crear_conversacion,
    agregar_mensaje
)

from LLM.llm.ollama_client import (
    crear_llm
)

from LLM.config.llm_config import (
    cambiar_modelo
)

from LLM.prompts.system_prompt import (
    SYSTEM_PROMPT
)

from LLM.validators.llm_validator import (
    validar_llm
)

from LLM.translators.translation_policy import (
    usar_traduccion
)

from LLM.translators.argos_translator import (
    translator
)


router = APIRouter()


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT
        ),
        (
            "human",
            """
Contexto:

{context}

Pregunta:

{input}

Responde únicamente en español.

No traduzcas la pregunta al inglés.

Utiliza solamente el contexto entregado.
"""
        )
    ]
)


#
# Ollama vive directamente en esta ruta.
#
_llm = crear_llm()


@router.post("/chat")
def chat(body: Pregunta):

    global _llm

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
    # Verificar RAG.
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
    # Cambiar modelo de Ollama.
    #

    if body.modelo:

        cambiar_modelo(
            body.modelo
        )

        _llm = crear_llm()

    #
    # Debug.
    #

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
        "Modelo activo:",
        getattr(
            _llm,
            "model",
            "NO DISPONIBLE"
        )
    )

    print(
        "LLM:",
        _llm
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

    #
    # Crear conversación.
    #

    conversation_id = body.conversation_id

    if conversation_id is None:

        conversation_id = crear_conversacion()

    #
    # Guardar pregunta.
    #

    agregar_mensaje(
        conversation_id=conversation_id,
        rol="user",
        contenido=body.pregunta
    )

    inicio = time.perf_counter()

    #
    # =====================================================
    # 1. RAG: SOLO RECUPERACIÓN
    # =====================================================
    #

    resultado_rag = rag_service.recuperar(
        body.pregunta
    )

    documentos = resultado_rag.get(
        "context",
        []
    )

    contexto = resultado_rag.get(
        "context_text",
        ""
    )

    #
    # =====================================================
    # 2. TRADUCCIÓN DE ENTRADA
    # =====================================================
    #

    if usar_traduccion():

        pregunta_llm = translator.es_a_en(
            body.pregunta
        )

    else:

        pregunta_llm = body.pregunta

    print(
        "[LLM QUESTION]",
        pregunta_llm
    )

    #
    # =====================================================
    # 3. CONSTRUIR PROMPT PARA OLLAMA
    # =====================================================
    #

    mensajes = PROMPT.invoke(
        {
            "context": contexto,
            "input": pregunta_llm
        }
    )

    print(
        "\n========== PROMPT ENVIADO A OLLAMA ==========\n"
    )

    print(
        mensajes
    )

    print(
        "\n==============================================\n"
    )

    #
    # =====================================================
    # 4. OLLAMA GENERA LA RESPUESTA
    # =====================================================
    #

    respuesta_llm = _llm.invoke(
        mensajes
    )

    respuesta = respuesta_llm.content

    #
    # =====================================================
    # 5. TRADUCCIÓN DE SALIDA
    # =====================================================
    #

    if usar_traduccion():

        respuesta = translator.en_a_es(
            respuesta
        )

    #
    # =====================================================
    # 6. VALIDACIÓN
    # =====================================================
    #

    validar_llm(
        body.pregunta,
        contexto,
        respuesta
    )

    tiempo = round(
        time.perf_counter() - inicio,
        2
    )

    #
    # Guardar respuesta.
    #

    agregar_mensaje(
        conversation_id=conversation_id,
        rol="assistant",
        contenido=respuesta
    )

    #
    # Documentos recuperados.
    #

    documentos_nombres = list(
        dict.fromkeys(
            doc.metadata.get("documento")
            for doc in documentos
            if doc.metadata.get("documento")
        )
    )

    chunks = len(
        documentos
    )

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

    print(
        "\n================ RESPUESTA DE OLLAMA ================\n"
    )

    print(
        respuesta
    )

    print(
        "\nModelo:",
        getattr(
            _llm,
            "model",
            "-"
        )
    )

    print(
        "Tiempo:",
        tiempo,
        "s"
    )

    print(
        "Chunks:",
        chunks
    )

    print(
        "======================================================\n"
    )

    return {

        "conversation_id":
            conversation_id,

        "respuesta":
            respuesta,

        "documento":
            ", ".join(
                documentos_nombres
            ),

        "modelo":
            getattr(
                _llm,
                "model",
                body.modelo or "-"
            ),

        "tiempo":
            f"{tiempo} s",

        "chunks":
            chunks,

        "tokens":
            tokens,

        "score":
            score

    }
