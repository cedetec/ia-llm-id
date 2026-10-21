# backend/PREPROCESSING/indexing/indexing_service.py

from pathlib import Path
from collections import Counter
import traceback
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma

from RAG.embeddings.embedding_service import crear_embeddings
from RAG.vectorstore.chroma_service import (
    agregar_documentos_vectorstore,
)

from PREPROCESSING.preprocessing.preprocessing_pipeline import (
    preprocesar_documentos
)

from app.database.document_repository import (
    guardar_documento
)

from RAG.config.vectorstore_settings import (
    NOMIC_COLLECTION,
    GEMMA_COLLECTION,
)

from RAG.config.embedding_settings import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_GEMMA_MODEL,
)

from app.core.paths import (
    PDF_DIR,
    CHROMA_NOMIC_DIR,
    CHROMA_GEMMA_DIR,
)

def _preprocesar(documentos):
    print("Preprocesando documentos...")
    fragmentos = preprocesar_documentos(documentos)
    print(f"Fragmentos generados: {len(fragmentos)}")
    return fragmentos

def _mostrar_estadisticas(contador_secciones, contador_titulos):
    print("\n================ SECCIONES INDEXADAS ================\n")
    for nombre, cantidad in contador_secciones.most_common():
        print(f"{nombre:<35} {cantidad}")

    print("\n================ TITULOS HIJO ================\n")
    for nombre, cantidad in contador_titulos.most_common():
        print(f"{nombre:<35} {cantidad}")

def _limpiar_cache_chroma():
    try:
        from chromadb.api.client import SharedSystemClient
        SharedSystemClient.clear_system_cache()
    except Exception:
        pass

def _limpiar_indice(embedding_model, persist_directory, collection_name):
    print(f"Limpiando colección anterior: {collection_name}")
    _limpiar_cache_chroma()
    embeddings = crear_embeddings(embedding_model)
    try:
        vectorstore_existente = Chroma(
            persist_directory=str(persist_directory),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        vectorstore_existente.delete_collection()
    except Exception:
        pass

def _agregar_al_indice(
    fragmentos,
    embedding_model,
    persist_directory,
    collection_name
):
    _limpiar_cache_chroma()
    embeddings = crear_embeddings(embedding_model)
    agregar_documentos_vectorstore(
        fragmentos,
        embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )

def _notificar_recarga_retrieval():
    import os
    import requests

    retrieval_url = os.getenv(
        "RETRIEVAL_RELOAD_URL",
        "http://backend-retrieval:8001/reload"
    )
    try:
        resp = requests.post(retrieval_url, timeout=30)
        if resp.ok:
            print("[INDEXING] Servicio backend-retrieval recargado automáticamente.")
        else:
            print(f"[INDEXING] Aviso al recargar retrieval ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"[INDEXING] No se pudo notificar a backend-retrieval ({e}). Se recargará en la próxima consulta.")


def indexar_pdf(pdf_path: Path, recargar_retrieval: bool = True):
    print("=" * 80)
    print(f"INDEXANDO: {pdf_path.name}")
    print("=" * 80)

    try:
        loader = PyPDFLoader(str(pdf_path))
        documentos = loader.load()
    except Exception as e:
        print(f"\nError leyendo {pdf_path}")
        traceback.print_exc()
        print(f"Excepción: {e}\n")
        return 0, Counter(), Counter()

    fragmentos = _preprocesar(documentos)

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

    if recargar_retrieval:
        _notificar_recarga_retrieval()

    contador_secciones = Counter()
    contador_titulos = Counter()
    for doc in fragmentos:
        contador_secciones[doc.metadata.get("seccion", "")] += 1
        contador_titulos[doc.metadata.get("titulo_hijo", "")] += 1

    return len(fragmentos), contador_secciones, contador_titulos

def indexar_documentos():
    tiempo_inicio = time.time()
    print("=" * 80)
    print("VERSION NUEVA DE INDEXING_SERVICE (ITERATIVA)")
    print("=" * 80)

    ruta = Path(PDF_DIR)
    print("Ruta:", ruta.resolve())

    # Limpiar el índice completo antes de empezar la indexación por lotes
    _limpiar_indice(
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        persist_directory=CHROMA_NOMIC_DIR,
        collection_name=NOMIC_COLLECTION
    )

    _limpiar_indice(
        embedding_model=EMBEDDING_GEMMA_MODEL,
        persist_directory=CHROMA_GEMMA_DIR,
        collection_name=GEMMA_COLLECTION
    )

    total_chunks = 0
    total_sec = Counter()
    total_tit = Counter()

    archivos_pdf = list(ruta.glob("*.pdf"))
    if not archivos_pdf:
        print("No se encontraron PDFs en el directorio.")
        return

    for idx, pdf in enumerate(archivos_pdf, 1):
        print(f"\nProcesando archivo {idx}/{len(archivos_pdf)}...")
        chunks, c_sec, c_tit = indexar_pdf(pdf, recargar_retrieval=False)
        total_chunks += chunks
        total_sec.update(c_sec)
        total_tit.update(c_tit)

    _notificar_recarga_retrieval()

    print("=" * 80)
    print("TOTAL CHUNKS ALMACENADOS:", total_chunks)
    print("=" * 80)
    _mostrar_estadisticas(total_sec, total_tit)
    tiempo_fin = time.time()
    tiempo_total = tiempo_fin - tiempo_inicio
    minutos = int(tiempo_total // 60)
    segundos = int(tiempo_total % 60)
    print(f"Indexación finalizada en {minutos} minutos y {segundos} segundos.")
