from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Header
from database.mongo import index_collection

from backend.services.document_service import (
    extraer_documentos,
    subir_documento_service,
    preprocesar_documentos
)

from backend.services.index_service import indexar_documentos

from backend.api.routes.security import ADMIN_TOKEN

router = APIRouter(prefix="/documentos", tags=["documentos"])

ADMIN_TOKEN = "super-secret-token"

@router.get("")
def listar_documentos():

    docs = index_collection.distinct("metadata.documento")

    return {
        "total": len(docs),
        "documentos": sorted(docs)
    }

@router.post("")
async def subir_documento(file: UploadFile = File(...)):
    try:
        return await subir_documento_service(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extraer")
def extraer(doc: str | None = Query(None)):
    try:
        return extraer_documentos(doc=doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preprocesar")
def preprocesar(doc: str | None = Query(None)):
    try:
        return preprocesar_documentos(doc=doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexar")
def indexar(
    mode: str = Query("upsert", pattern="^(upsert|rebuild)$"),
    doc: str | None = Query(None),
    x_admin_token: str | None = Header(None)
):

    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        return indexar_documentos(doc=doc, mode=mode)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
