#ingest_service.py
import io, json, hashlib
import pandas as pd
import unicodedata
import re
from datetime import datetime
from bson import ObjectId

from database import documents_collection, fs

from datetime import timezone

MAX_FILE_SIZE_MB = 25  # ajusta según tu servidor

def _validar_magic_bytes(contenido: bytes, extension: str):
    if extension == "pdf":
        if not contenido.startswith(b"%PDF"):
            raise ValueError("El archivo no es un PDF válido")

    if extension == "docx":
        # DOCX es un ZIP (PK)
        if not contenido.startswith(b"PK"):
            raise ValueError("El archivo no es un DOCX válido")

def _guardar_en_gridfs(contenido, filename, extension, now, sha256):
    content_type = (
        "application/pdf"
        if extension == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    file_id = fs.put(
        contenido,
        filename=filename,
        contentType=content_type,
        metadata={
            "tipo": extension.upper(),
            "nombre": filename,
            "fecha_carga": now.isoformat(),
            "sha256": sha256,
            "tamano_bytes": len(contenido),
        }
    )

    return file_id, content_type

def normalizar_nombre_documento(nombre: str) -> str:
    if not nombre:
        return ""

    nombre = unicodedata.normalize("NFKC", nombre)
    nombre = nombre.replace("\u00A0", " ")
    nombre = nombre.strip()
    nombre = re.sub(r"\s+", " ", nombre)

    return nombre.lower()

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


async def procesar_documento(file):
    contenido: bytes = await file.read()

    # 🔒 Validación tamaño
    if len(contenido) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE_MB}MB)"
        )

    filename = normalizar_nombre_documento(file.filename)
    extension = filename.split(".")[-1].lower()

    # 🔒 Validación tipo real (solo para pdf/docx)
    if extension in ("pdf", "docx"):
        _validar_magic_bytes(contenido, extension)

    now = datetime.now(timezone.utc)
    sha256 = _sha256_bytes(contenido)

    doc_base = {
        "nombre": filename,
        "tipo": extension.upper(),
        "fecha_carga": now,
        "sha256": sha256,
        "tamano_bytes": len(contenido),
    }

    # -------------------------
    # CSV
    # -------------------------
    if extension == "csv":
        df = pd.read_csv(io.BytesIO(contenido))
        doc_base["contenido"] = df.to_dict(orient="records")

        documents_collection.update_one(
            {"nombre": filename},
            {"$set": doc_base},
            upsert=True
        )
        return {"message": "Documento almacenado", "archivo": filename}

    # -------------------------
    # JSON
    # -------------------------
    if extension == "json":
        try:
            parsed = json.loads(contenido.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("JSON inválido")

        doc_base["contenido"] = parsed

        documents_collection.update_one(
            {"sha256": sha256},
            {"$set": doc_base},
            upsert=True
        )
        return {"message": "Documento almacenado", "archivo": filename}

    # -------------------------
    # PDF / DOCX -> GridFS (idempotente por hash)
    # -------------------------
    if extension in ("pdf", "docx"):
        # Busca previo (para comparar hash y/o borrar GridFS)
        prev = documents_collection.find_one(
            {"sha256": sha256},
            {"gridfs_id": 1, "sha256": 1, "tamano_bytes": 1, "mime": 1}
        )

        # ✅ Si es el mismo archivo (mismo hash), NO re-subir
        if prev and prev.get("sha256") == sha256 and prev.get("gridfs_id"):
            # OJO: NO reseteamos texto_extraido*, porque el archivo no cambió.
            return {
                "message": "Documento ya existía (mismo hash), no se re-subió",
                "archivo": filename,
                "gridfs_id": str(prev["gridfs_id"]),
                "sha256": sha256,
            }

        # Si cambió, borra el anterior en GridFS (si existe)
        if prev and prev.get("gridfs_id"):
            try:
                old_id = prev["gridfs_id"]
                if not isinstance(old_id, ObjectId):
                    old_id = ObjectId(str(old_id))
                fs.delete(old_id)
            except Exception:
                # si falla, no bloquees la subida (pero podrías loggear)
                pass

        file_id, content_type = _guardar_en_gridfs(
            contenido, filename, extension, now, sha256
        )

        # ✅ Como el binario cambió, resetea extracción para forzar /extraer_pdf
        doc_update = {
            **doc_base,
            "gridfs_id": file_id,
            "mime": content_type,
            "texto_extraido": None,
            "texto_extraido_ok": False,
            "requiere_ocr": False if extension == "pdf" else None,
        }

        documents_collection.update_one(
            {"sha256": sha256},
            {"$set": doc_update},
            upsert=True
        )
        return {
            "message": "Documento almacenado",
            "archivo": filename,
            "gridfs_id": str(file_id),
            "sha256": sha256,
        }

    # -------------------------
    # Otros formatos
    # -------------------------
    doc_base["contenido"] = "Formato no soportado"

    documents_collection.update_one(
        {"nombre": filename},
        {"$set": doc_base},
        upsert=True
    )
    return {"message": "Documento almacenado", "archivo": filename}
