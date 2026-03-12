# backend/api/routes/admin.py

from fastapi import APIRouter, HTTPException, Query, Header
from database import documents_collection, clean_collection, index_collection

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_TOKEN = "super-secret-token"  # mover a .env idealmente

@router.post("/reset")
def reset(
    mode: str = Query("soft"),
    x_admin_token: str | None = Header(None)
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")

    if mode not in ("soft", "full"):
        raise HTTPException(status_code=400, detail="mode debe ser 'soft' o 'full'")

    clean_deleted = clean_collection.delete_many({}).deleted_count
    index_deleted = index_collection.delete_many({}).deleted_count

    docs_deleted = 0
    gridfs_files_deleted = 0
    gridfs_chunks_deleted = 0

    if mode == "full":
        docs_deleted = documents_collection.delete_many({}).deleted_count
        db = documents_collection.database
        gridfs_chunks_deleted = db["fs.chunks"].delete_many({}).deleted_count
        gridfs_files_deleted = db["fs.files"].delete_many({}).deleted_count

    return {
        "mode": mode,
        "deleted": {
            "concursos_limpios": clean_deleted,
            "indexados": index_deleted,
            "documentos": docs_deleted,
            "gridfs.files": gridfs_files_deleted,
            "gridfs.chunks": gridfs_chunks_deleted,
        }
    }