# backend/LLM/indexing/indexing_service.py

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from LLM.embeddings.embedding_service import crear_embeddings
from LLM.vectorstore.chroma_service import (
    crear_vectorstore,
    agregar_documentos_vectorstore,
)

from LLM.preprocessing.preprocessing_pipeline import (
    preprocesar_documentos
)

from app.database.document_repository import (
    guardar_documento
)

from LLM.config.vectorstore_settings import (
    NOMIC_COLLECTION,
    GEMMA_COLLECTION,
)

from LLM.config.embedding_settings import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_GEMMA_MODEL
)

from collections import Counter

from app.core.paths import (
    PDF_DIR,
    CHROMA_NOMIC_DIR,
    CHROMA_GEMMA_DIR
)

def cargar_pdfs_seguro(ruta_carpeta):

    documentos = []

    ruta = Path(ruta_carpeta)

    print("Ruta:", ruta.resolve())

    print("PDF encontrados:")

    for pdf in ruta.glob("*.pdf"):

        try:

            loader = PyPDFLoader(str(pdf))

            documentos.extend(loader.load())

        except Exception as e:

            print(f"\nError leyendo {pdf}")

            import traceback
            traceback.print_exc()

            print(f"Excepción: {e}\n")

    return documentos


def _preprocesar(documentos):

    print("Preprocesando documentos...")

    fragmentos = preprocesar_documentos(
        documentos
    )

    print(
        f"Fragmentos generados: {len(fragmentos)}"
    )

    return fragmentos


def _guardar_documentos_indexados(fragmentos):

    contador_chunks = Counter()

    for fragmento in fragmentos:

        source = fragmento.metadata.get(
            "source",
            ""
        )

        nombre = Path(source).name

        contador_chunks[nombre] += 1

    print("=" * 80)
    print("CONTADOR DE CHUNKS")
    print("=" * 80)

    for nombre, cantidad in contador_chunks.items():

        print(nombre, cantidad)

    for pdf in Path(PDF_DIR).glob("*.pdf"):

        guardar_documento(

            nombre=pdf.name,

            tamano=pdf.stat().st_size,

            chunks=contador_chunks.get(
                pdf.name,
                0
            ),

            estado="Indexado"

        )

    return contador_chunks


def _mostrar_estadisticas(fragmentos):

    contador_secciones = Counter()

    contador_titulos = Counter()

    for doc in fragmentos:

        contador_secciones[
            doc.metadata.get(
                "seccion",
                ""
            )
        ] += 1

        contador_titulos[
            doc.metadata.get(
                "titulo_hijo",
                ""
            )
        ] += 1

    print(
        "\n================ SECCIONES INDEXADAS ================\n"
    )

    for nombre, cantidad in contador_secciones.most_common():

        print(f"{nombre:<35} {cantidad}")

    print(
        "\n================ TITULOS HIJO ================\n"
    )

    for nombre, cantidad in contador_titulos.most_common():

        print(f"{nombre:<35} {cantidad}")


def _crear_indice(
    fragmentos,
    embedding_model,
    persist_directory,
    collection_name
):

    embeddings = crear_embeddings(
        embedding_model
    )

    crear_vectorstore(
        fragmentos,
        embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )


def _agregar_al_indice(
    fragmentos,
    embedding_model,
    persist_directory,
    collection_name
):

    embeddings = crear_embeddings(
        embedding_model
    )

    agregar_documentos_vectorstore(

        fragmentos,

        embeddings,

        persist_directory=persist_directory,

        collection_name=collection_name

    )


def indexar_documentos():

    print("=" * 80)
    print("VERSION NUEVA DE INDEXING_SERVICE")
    print("=" * 80)

    documentos = cargar_pdfs_seguro(
        PDF_DIR
    )

    fragmentos = _preprocesar(
        documentos
    )

    _guardar_documentos_indexados(
        fragmentos
    )

    _mostrar_estadisticas(
        fragmentos
    )

    _crear_indice(
        fragmentos,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        persist_directory=CHROMA_NOMIC_DIR,
        collection_name=NOMIC_COLLECTION
    )

    _crear_indice(
        fragmentos,
        embedding_model=EMBEDDING_GEMMA_MODEL,
        persist_directory=CHROMA_GEMMA_DIR,
        collection_name=GEMMA_COLLECTION
    )

    print("Indexación finalizada.")


def indexar_pdf(pdf_path: Path):

    print("=" * 80)
    print(f"INDEXANDO: {pdf_path.name}")
    print("=" * 80)

    loader = PyPDFLoader(str(pdf_path))

    documentos = loader.load()

    fragmentos = _preprocesar(
        documentos
    )

    _agregar_al_indice(
        fragmentos,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        persist_directory=CHROMA_NOMIC_DIR,
        collection_name=NOMIC_COLLECTION
    )

    _agregar_al_indice(
        fragmentos,
        embedding_model=EMBEDDING_GEMMA_MODEL,
        persist_directory=CHROMA_GEMMA_DIR,
        collection_name=GEMMA_COLLECTION
    )

    guardar_documento(

        nombre=pdf_path.name,

        tamano=pdf_path.stat().st_size,

        chunks=len(fragmentos),

        estado="Indexado"

    )

    print(f"PDF indexado: {pdf_path.name}")

    return len(fragmentos)
