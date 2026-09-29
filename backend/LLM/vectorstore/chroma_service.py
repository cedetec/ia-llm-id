# chroma_service.py

from langchain_community.vectorstores import Chroma

from Preprocesamiento.validators.metadata_validator import (
    validar_metadata
)

from RAG.validators.vectorstore_validator import (
    validar_vectorstore
)


from app.core.paths import CHROMA_DIR

# Cantidad máxima de chunks enviados a Ollama/Chroma por lote.
BATCH_SIZE = 100


def asignar_ids_documentos(documentos):
    """
    Asigna IDs únicos y deterministas a los documentos.

    El ID depende de la posición del fragmento dentro
    del conjunto de documentos de la indexación.
    """

    for indice, documento in enumerate(documentos):

        documento.id = (
            f"anid_chunk_{indice:08d}"
        )

    return documentos


def _sanitizar_metadata(documentos):
    """
    Reemplaza valores None de metadata por cadenas vacías.

    Chroma no admite valores None en determinados campos
    de metadata.
    """

    for doc in documentos:

        for clave, valor in list(
            doc.metadata.items()
        ):

            if valor is None:

                print(
                    f"[WARNING] {clave} era None. "
                    f"Se reemplaza por ''."
                )

                doc.metadata[clave] = ""

    return documentos


def _agregar_por_lotes(
    vectorstore,
    documentos
):
    """
    Agrega documentos a Chroma en lotes.

    Devuelve la cantidad total de chunks almacenados.
    """

    total_documentos = len(documentos)

    total_lotes = (
        total_documentos + BATCH_SIZE - 1
    ) // BATCH_SIZE

    print(
        f"[CHROMA] {total_documentos} chunks "
        f"en {total_lotes} lotes de hasta {BATCH_SIZE}."
    )

    for inicio in range(
        0,
        total_documentos,
        BATCH_SIZE
    ):

        fin = min(
            inicio + BATCH_SIZE,
            total_documentos
        )

        lote = documentos[
            inicio:fin
        ]

        numero_lote = (
            inicio // BATCH_SIZE
        ) + 1

        print(
            f"\n[CHROMA LOTE] "
            f"{numero_lote}/{total_lotes} "
            f"| chunks {inicio + 1}-{fin} "
            f"| cantidad={len(lote)}"
        )

        vectorstore.add_documents(
            lote
        )

        almacenados = (
            vectorstore._collection.count()
        )

        print(
            f"[CHROMA LOTE COMPLETADO] "
            f"{numero_lote}/{total_lotes} "
            f"| almacenados={almacenados}"
        )

    return vectorstore._collection.count()


def cargar_vectorstore(
    embeddings,
    persist_directory=str(CHROMA_DIR),
    collection_name=None
):
    """
    Abre un vectorstore previamente indexado.
    No crea una nueva colección ni elimina documentos.
    """

    persist_directory = str(
        persist_directory
    )

    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    validar_vectorstore(vectorstore)

    return vectorstore


def crear_vectorstore(
    documentos,
    embeddings,
    persist_directory=str(CHROMA_DIR),
    collection_name=None
):
    """
    Crea un nuevo vectorstore desde documentos.

    La indexación se realiza en lotes para evitar enviar
    todos los chunks simultáneamente al servidor Ollama.
    """

    if not documentos:
        print("No hay documentos para indexar.")
        return None

    persist_directory = str(
        persist_directory
    )

    validar_metadata(documentos)

    #
    # Elimina la colección anterior si existe.
    #

    try:

        vectorstore_existente = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        vectorstore_existente.delete_collection()

    except Exception:
        pass


    #
    # Crea una nueva colección limpia.
    #

    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    #
    # Sanitizar metadata para Chroma.
    #

    _sanitizar_metadata(
        documentos
    )

    #
    # Asignar IDs deterministas.
    #

    asignar_ids_documentos(
        documentos
    )

    total_almacenados = _agregar_por_lotes(
        vectorstore,
        documentos
    )

    print(
        "[CHROMA] Indexación por lotes finalizada. "
        f"Chunks almacenados: {total_almacenados}"
    )

    validar_vectorstore(
        vectorstore
    )

    return vectorstore


def agregar_documentos_vectorstore(
    documentos,
    embeddings,
    persist_directory=str(CHROMA_DIR),
    collection_name=None
):
    """
    Agrega documentos a una colección Chroma ya existente.

    También utiliza lotes para evitar enviar demasiados
    documentos simultáneamente a Ollama.
    """

    if not documentos:
        print("No hay documentos para agregar.")
        return None

    persist_directory = str(
        persist_directory
    )

    validar_metadata(documentos)

    vectorstore = cargar_vectorstore(
        embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )

    #
    # Sanitizar metadata.
    #

    _sanitizar_metadata(
        documentos
    )

    total_almacenados = _agregar_por_lotes(
        vectorstore,
        documentos
    )

    print(
        "[CHROMA] Total de chunks almacenados:",
        total_almacenados
    )

    validar_vectorstore(
        vectorstore
    )

    return vectorstore
