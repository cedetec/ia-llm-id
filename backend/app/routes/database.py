"""
database.py

Endpoints REST para administrar la base documental.
"""

import io

from typing import List

from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
)

from fastapi.responses import (
    FileResponse,
    StreamingResponse,
)

from app.schemas.database import (
    DatabaseStats,
    DatabaseStatus,
    DatabaseOperationStatus,
    DatabaseLog,
    UploadResponse,
)

from app.services.database_service import (
    upload_pdf,
    list_pdfs,
    get_pdf,
    build_database_stats,
    reindex_database,
    clear_database,
    get_logs,
    get_database_status,
)

from app.services.system_service import (
    build_system_status,
)

router = APIRouter(
    prefix="/database",
    tags=["Database"],
)

# =====================================================
# PDFs
# =====================================================

@router.post(
    "/upload",
    response_model=UploadResponse,
)
async def upload_database_pdf(
    archivo: UploadFile = File(...)
):

    return await upload_pdf(
        archivo
    )


@router.get(
    "/list",
)
def list_database_pdfs():

    return list_pdfs()


@router.get(
    "/download/{nombre_archivo}",
    response_class=FileResponse,
)
def download_database_pdf(
    nombre_archivo: str,
):

    ruta = get_pdf(
        nombre_archivo
    )

    return FileResponse(
        path=ruta,
        filename=ruta.name,
        media_type="application/pdf"
    )

@router.post(
    "/download-selected",
)
def download_selected_database_pdfs(
    nombres_archivos: List[str],
):

    if not nombres_archivos:

        raise HTTPException(
            status_code=400,
            detail="Debe seleccionar al menos un archivo."
        )

    rutas = []
    vistos = set()

    for nombre_archivo in nombres_archivos:

        if nombre_archivo in vistos:
            continue

        ruta = get_pdf(
            nombre_archivo
        )

        rutas.append(
            ruta
        )

        vistos.add(
            nombre_archivo
        )

    buffer = io.BytesIO()

    with ZipFile(
        buffer,
        "w",
        ZIP_DEFLATED
    ) as archivo_zip:

        for ruta in rutas:

            archivo_zip.write(
                ruta,
                arcname=ruta.name
            )

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
                'attachment; filename="anid_pdfs_seleccionados.zip"'
        }
    )

# =====================================================
# Estadísticas
# =====================================================

@router.get(
    "/stats",
    response_model=DatabaseStats,
)
def database_stats():

    return build_database_stats()


@router.get(
    "/status",
    response_model=DatabaseOperationStatus,
)
def database_status():

    return get_database_status()

# =====================================================
# Administración
# =====================================================

@router.post(
    "/reindex",
    response_model=DatabaseOperationStatus,
)
def database_reindex():

    return reindex_database()


@router.delete(
    "/clear",
    response_model=DatabaseOperationStatus,
)
def database_clear():

    return clear_database()

# =====================================================
# Logs
# =====================================================

@router.get(
    "/logs",
    response_model=list[DatabaseLog],
)
def database_logs():

    return get_logs()

# =====================================================
# Estado del sistema
# =====================================================

@router.get(
    "/system",
    response_model=DatabaseStatus,
)
def system_status():

    return build_system_status()
