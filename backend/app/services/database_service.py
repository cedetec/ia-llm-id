"""
database_service.py

Servicio encargado de administrar la base documental del asistente RAG.

Responsabilidades:

- Gestión de PDFs
- Estadísticas de la base documental
- Administración del índice Chroma
- Reindexación
- Utilidades del panel de administración
"""

from __future__ import annotations

import shutil
import logging
import time

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import UploadFile, HTTPException

from app.schemas.database import (
    DatabaseStats,
    DatabaseStatus,
    DatabaseOperationStatus,
    DatabaseLog,
    IndexedContest,
    UploadResponse,
)

# =====================================================
# Reutilización del pipeline existente
# =====================================================

from LLM.indexing.indexing_service import (
    indexar_documentos,
    indexar_pdf,
)

from LLM.config.llm_config import (
    obtener_modelo,
)

from app.database.document_repository import (
    listar_documentos
)

from LLM.config.vectorstore_settings import (
    NOMIC_COLLECTION,
    GEMMA_COLLECTION,
)

from LLM.config.embedding_settings import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_GEMMA_MODEL,
)

from LLM.embeddings.embedding_service import crear_embeddings
from LLM.vectorstore.chroma_service import cargar_vectorstore

from app.core.paths import (

    DATA_DIR,

    PDF_DIR,

    VECTORSTORE_DIR,

    CHROMA_DIR,

    CHROMA_NOMIC_DIR,

    CHROMA_GEMMA_DIR,

    LOG_DIR,

    TEMP_DIR,

)

import re

# =====================================================
# Logger
# =====================================================

logger = logging.getLogger(__name__)

# =====================================================
# Configuración
# =====================================================

ALLOWED_EXTENSIONS = {
    ".pdf"
}

# =====================================================
# Estado del servicio
# =====================================================

_last_index_time: Optional[float] = None

_last_index_date: Optional[str] = None

_logs: List[DatabaseLog] = []

# =====================================================
# Registro interno
# =====================================================

def registrar_log(mensaje: str) -> None:

    hora = datetime.now().strftime("%H:%M:%S")

    registro = DatabaseLog(
        hora=hora,
        mensaje=mensaje,
    )

    _logs.append(registro)

    logger.info(mensaje)

# =====================================================
# Tiempo de indexación
# =====================================================

def iniciar_medicion() -> None:
    """
    Inicia el cronómetro de indexación.
    """

    global _last_index_time

    _last_index_time = time.perf_counter()


def finalizar_medicion() -> float:
    """
    Finaliza el cronómetro y devuelve los segundos empleados.
    """

    global _last_index_time
    global _last_index_date

    if _last_index_time is None:
        return 0.0

    duracion = time.perf_counter() - _last_index_time

    _last_index_date = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    return round(duracion, 2)

# =====================================================
# Gestión de PDFs
# =====================================================

async def upload_pdf(
    archivo: UploadFile,
) -> UploadResponse:
    """
    Guarda un PDF en el directorio de datos.

    La reindexación se implementará posteriormente.
    """

    extension = Path(
        archivo.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=f"Solo se permiten archivos PDF. Archivo recibido: {archivo.filename}"
        )

    destino = PDF_DIR / archivo.filename

    # Verificar si el archivo ya existe
    if destino.exists():

        raise HTTPException(
            status_code=409,
            detail=f"El archivo '{archivo.filename}' ya existe."
        )

    # Guardar el PDF

    with destino.open("wb") as buffer:

        shutil.copyfileobj(
            archivo.file,
            buffer
        )

    registrar_log(
        f"PDF '{archivo.filename}' cargado correctamente."
    )

    # Indexar únicamente ese PDF

    iniciar_medicion()

    registrar_log("Indexación iniciada")

    print("=" * 80)
    print("ANTES DE LLAMAR A indexar_pdf")
    print(indexar_pdf)
    print(indexar_pdf.__module__)
    print(indexar_pdf.__code__.co_filename)
    print("=" * 80)

    chunks = indexar_pdf(destino)

    print("=" * 80)
    print("DESPUÉS DE LLAMAR A indexar_pdf")
    print("chunks =", chunks)
    print("=" * 80)

    tiempo = finalizar_medicion()

    registrar_log(
        f"Indexación finalizada ({tiempo} s)"
    )

    registrar_log(
        f"{chunks} chunks generados."
    )

    return UploadResponse(

        ok=True,

        archivo=archivo.filename,

        mensaje="Archivo cargado correctamente."

    )


def list_pdfs() -> List[Dict[str, Any]]:
    """
    Devuelve todos los PDFs almacenados.
    """

    documentos: List[Dict[str, Any]] = []

    if not PDF_DIR.exists():

        return documentos

    return listar_documentos()

# =====================================================
# Descarga de PDFs
# =====================================================

def get_pdf(
    nombre_archivo: str,
) -> Path:
    """
    Devuelve un PDF almacenado para su descarga.
    """

    # Validar nombre del archivo
    if not nombre_archivo:

        raise HTTPException(
            status_code=400,
            detail="Debe indicar un nombre de archivo."
        )

    # Evitar path traversal
    nombre_archivo = Path(
        nombre_archivo
    ).name

    # Debe ser un PDF
    if Path(
        nombre_archivo
    ).suffix.lower() != ".pdf":

        raise HTTPException(
            status_code=400,
            detail="Solo se permite descargar archivos PDF."
        )

    ruta_pdf = PDF_DIR / nombre_archivo

    # Verificar existencia
    if not ruta_pdf.exists():

        raise HTTPException(
            status_code=404,
            detail=f"No existe el archivo '{nombre_archivo}'."
        )

    registrar_log(
        f"Descarga de '{nombre_archivo}'."
    )

    return ruta_pdf

# =====================================================
# Estadísticas
# =====================================================

def count_documents() -> int:
    """
    Cuenta la cantidad de archivos PDF
    existentes en el directorio PDF_DIR.
    """

    if not PDF_DIR.exists():
        return 0

    return len(list(PDF_DIR.glob("*.pdf")))


def count_chunks():
    """
    Devuelve la cantidad de chunks lógicos registrados
    en MongoDB.

    Cada documento se contabiliza una sola vez,
    independientemente de que sus chunks tengan
    representaciones vectoriales en Nomic y
    EmbeddingGemma.
    """

    total = 0

    for documento in listar_documentos():

        try:

            total += int(
                documento.get(
                    "chunks",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            logger.warning(
                "Cantidad de chunks inválida para %s",
                documento.get("nombre")
            )

    return total


def get_index_size() -> str:
    """
    Calcula el tamaño total de los dos índices vectoriales.
    """

    total_bytes = 0

    for directorio in (
        CHROMA_NOMIC_DIR,
        CHROMA_GEMMA_DIR,
    ):

        if not directorio.exists():

            continue

        for archivo in directorio.rglob("*"):

            if archivo.is_file():

                total_bytes += archivo.stat().st_size

    total_mb = total_bytes / (1024 * 1024)

    return f"{total_mb:.2f} MB"


def extraer_anio(nombre_archivo: str) -> int:
    """
    Extrae un año de cuatro dígitos desde el nombre del archivo.
    """
    match = re.search(
        r"(?<!\d)(20\d{2})(?!\d)",
        nombre_archivo or ""
    )

    if match:
        return int(match.group(1))

    return 0


def build_database_stats() -> DatabaseStats:
    """
    Construye el objeto de estadísticas utilizado
    por GET /database/stats.
    """

    embedding = (
        f"{DEFAULT_EMBEDDING_MODEL} / "
        f"{EMBEDDING_GEMMA_MODEL}"
    )

    coleccion = (
        f"{NOMIC_COLLECTION} / "
        f"{GEMMA_COLLECTION}"
    )

    modelo = obtener_modelo()

    documentos = count_documents()

    chunks = count_chunks()

    concursos: List[IndexedContest] = []

    for doc in listar_documentos():

        anio = doc.get("anio") or extraer_anio(
            doc.get("nombre", "")
        )

        concursos.append(
            IndexedContest(
                nombre=doc["nombre"],
                anio=anio,
                estado=doc["estado"],
                chunks=doc["chunks"]
            )
        )

    return DatabaseStats(
        documentos=documentos,
        chunks=chunks,
        coleccion=coleccion,
        embedding=embedding,
        modelo=modelo,
        ultimaIndexacion=_last_index_date or "-",
        tamanoIndice=get_index_size(),
        backend="Activo",
        ollama="Activo",
        chroma="Activo",
        tiempoIndexacion="-",
        concursos=concursos
    )

# =====================================================
# Administración del índice
# =====================================================

def reindex_database() -> DatabaseOperationStatus:

    try:

        iniciar_medicion()

        registrar_log(
            "Indexación iniciada."
        )

        indexar_documentos()

        tiempo = finalizar_medicion()

        registrar_log(
            f"Indexación finalizada ({tiempo} s)."
        )

        return DatabaseOperationStatus(

            estado="Indexado",

            documentos=count_documents(),

            chunks=count_chunks(),

            ultimaIndexacion=_last_index_date,

            mensaje="Base documental indexada correctamente."

        )

    except Exception as e:

        logger.exception(
            "Error durante la indexación."
        )

        registrar_log(
            f"Error de indexación: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible reconstruir el índice."
        )

def clear_database() -> DatabaseOperationStatus:
    """
    Elimina los índices vectoriales nuevos.
    El índice Chroma antiguo se conserva como respaldo.
    Los PDFs originales también se conservan.
    """

    try:

        for directorio in (
            CHROMA_NOMIC_DIR,
            CHROMA_GEMMA_DIR,
        ):

            if directorio.exists():

                shutil.rmtree(
                    directorio
                )

        registrar_log(
            "Índices Nomic y EmbeddingGemma eliminados."
        )

        return DatabaseOperationStatus(

            estado="Vacío",

            documentos=count_documents(),

            chunks=0,

            ultimaIndexacion=_last_index_date,

            mensaje=(
                "Índices vectoriales nuevos eliminados "
                "correctamente. El índice antiguo fue conservado."
            )

        )

    except Exception as e:

        logger.exception(
            "Error eliminando los índices."
        )

        registrar_log(
            f"Error eliminando índices: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible eliminar los índices."
        )

# =====================================================
# Registros y utilidades
# =====================================================

def get_logs(
    limite: int = 100,
) -> List[DatabaseLog]:
    """
    Devuelve los últimos registros del servicio.
    """

    return _logs[-limite:]


def clear_logs() -> None:
    """
    Elimina todos los registros almacenados.
    """

    _logs.clear()

    registrar_log(
        "Registros limpiados."
    )


def get_last_indexation() -> Optional[str]:
    """
    Devuelve la fecha de la última indexación.
    """

    return _last_index_date


def get_database_status() -> DatabaseOperationStatus:
    """
    Devuelve el estado general del índice.
    """

    estado = (
        "Indexado"
        if count_chunks() > 0
        else "Vacío"
    )

    return DatabaseOperationStatus(

        estado=estado,

        documentos=count_documents(),

        chunks=count_chunks(),

        ultimaIndexacion=_last_index_date,

        mensaje="Estado obtenido correctamente."

    )


def database_exists() -> bool:

    nomic_existe = (
        CHROMA_NOMIC_DIR.exists()
        and any(CHROMA_NOMIC_DIR.iterdir())
    )

    gemma_existe = (
        CHROMA_GEMMA_DIR.exists()
        and any(CHROMA_GEMMA_DIR.iterdir())
    )

    return nomic_existe or gemma_existe


def pdf_exists(
    nombre_archivo: str,
) -> bool:
    """
    Verifica si un PDF existe.
    """

    return (
        PDF_DIR / nombre_archivo
    ).exists()


def get_pdf_path(
    nombre_archivo: str,
) -> Path:
    """
    Devuelve la ruta absoluta de un PDF.
    """

    return PDF_DIR / nombre_archivo


def get_database_paths() -> Dict[str, str]:

    return {

        "data": str(DATA_DIR),

        "pdfs": str(PDF_DIR),

        "vectorstore": str(VECTORSTORE_DIR),

        "chroma_legacy": str(CHROMA_DIR),

        "chroma_nomic": str(CHROMA_NOMIC_DIR),

        "chroma_gemma": str(CHROMA_GEMMA_DIR),

        "logs": str(LOG_DIR),

        "temp": str(TEMP_DIR),

    }

def healthcheck() -> Dict[str, Any]:
    """
    Comprueba el estado básico del servicio.
    """

    return {

        "backend": True,

        "pdf_directory": PDF_DIR.exists(),

        "vectorstore": VECTORSTORE_DIR.exists(),

        "chroma": database_exists(),

        "documentos": count_documents(),

        "chunks": count_chunks(),

        "ultima_indexacion": _last_index_date,

    }
