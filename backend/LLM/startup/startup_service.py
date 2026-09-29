# startup_service.py

from RAG.embeddings.embedding_service import (
    crear_embeddings
)

from RAG.vectorstore.chroma_service import (
    cargar_vectorstore
)

from RAG.retriever.retrieval_service import (
    crear_retriever
)

from RAG.rag.rag_service import (
    construir_rag
)

from RAG.config.embedding_settings import (
    DEFAULT_EMBEDDING_MODEL
)

from app.core.paths import (
    CHROMA_NOMIC_DIR,
    CHROMA_GEMMA_DIR
)


def crear_rag_service(
    embedding_model=DEFAULT_EMBEDDING_MODEL,
    persist_directory=None,
    collection_name=None
):

    embeddings = crear_embeddings(
        embedding_model
    )

    if persist_directory is None:

        vectorstore = cargar_vectorstore(
            embeddings,
            collection_name=collection_name
        )

    else:

        vectorstore = cargar_vectorstore(
            embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )

    print(
        "Embedding:",
        embedding_model
    )

    print(
        "Colección:",
        collection_name
    )

    print(
        "Chunks:",
        vectorstore._collection.count()
    )

    retriever = crear_retriever(
        vectorstore
    )

    return construir_rag(
        retriever
    )
