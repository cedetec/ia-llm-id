# backend/app/startup.py

from pathlib import Path

from RAG.startup.startup_service import (
    crear_rag_service
)

from app.core.paths import (
    CHROMA_NOMIC_DIR,
    CHROMA_GEMMA_DIR
)

from RAG.config.vectorstore_settings import (
    NOMIC_COLLECTION,
    GEMMA_COLLECTION,
)

from RAG.config.embedding_settings import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_GEMMA_MODEL
)

rag_nomic = None

rag_gemma = None


def reinicializar_rag():

    global rag_nomic
    global rag_gemma

    try:
        from chromadb.api.client import SharedSystemClient
        SharedSystemClient.clear_system_cache()
    except Exception as e:
        print(f"[STARTUP] Aviso limpiando caché de Chroma: {e}")

    #
    # RAG Nomic
    #

    if Path(CHROMA_NOMIC_DIR).exists():

        rag_nomic = crear_rag_service(

            embedding_model=DEFAULT_EMBEDDING_MODEL,

            persist_directory=CHROMA_NOMIC_DIR,

            collection_name=NOMIC_COLLECTION

        )

    else:

        print(
            "[STARTUP] Índice Nomic todavía no existe."
        )

        rag_nomic = None

    #
    # RAG EmbeddingGemma
    #

    if Path(CHROMA_GEMMA_DIR).exists():

        rag_gemma = crear_rag_service(

            embedding_model=EMBEDDING_GEMMA_MODEL,

            persist_directory=CHROMA_GEMMA_DIR,

            collection_name=GEMMA_COLLECTION

        )

    else:

        print(
            "[STARTUP] Índice EmbeddingGemma todavía no existe."
        )

        rag_gemma = None


reinicializar_rag()
