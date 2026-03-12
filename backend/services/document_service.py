# backend/services/document_service.py

from __future__ import annotations

import os
from datetime import datetime
from fastapi import UploadFile
from database import documents_collection, clean_collection, fs
from backend.services.preprocess_service import preprocesar_documentos

import pdfplumber
import uuid

import hashlib


async def subir_documento_service(file: UploadFile):

    if not file.filename:
        raise ValueError("Archivo inválido")

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    # Verificar si ya existe
    existing = documents_collection.find_one({"sha256": sha256})
    if existing:
        return {
            "message": "Documento ya existía (mismo hash), no se re-subió",
            "archivo": file.filename,
            "gridfs_id": str(existing.get("gridfs_id")),
            "sha256": sha256
        }

    # Guardar en GridFS
    gridfs_id = fs.put(
        content,
        filename=file.filename,
        content_type=file.content_type
    )

    doc_payload = {
        "nombre": file.filename.lower(),
        "tipo": file.filename.split(".")[-1].upper(),
        "gridfs_id": gridfs_id,
        "sha256": sha256,
        "fecha_subida": datetime.utcnow(),
        "texto": "",
        "texto_ok": False,
    }

    documents_collection.insert_one(doc_payload)

    return {
        "message": "Documento subido correctamente",
        "archivo": file.filename,
        "gridfs_id": str(gridfs_id),
        "sha256": sha256
    }

# ==========================================================
# 2️⃣ EXTRAER TEXTO (PDF / DOCX)
# ==========================================================

def extraer_documentos(doc: str | None = None):

    query = {"nombre": doc} if doc else {}

    procesados = 0

    for d in documents_collection.find(query):

        ruta = d.get("ruta_archivo")
        tipo = (d.get("tipo") or "").upper()

        if not ruta or not os.path.exists(ruta):
            continue

        texto = ""

        if tipo == "PDF":
            try:
                with pdfplumber.open(ruta) as pdf:
                    for page in pdf.pages:
                        texto += page.extract_text() or ""
                        texto += "\n\n"
            except Exception as e:
                print("Error PDF:", e)
                continue

        elif tipo == "DOCX":
            try:
                from docx import Document
                docx = Document(ruta)
                texto = "\n".join(p.text for p in docx.paragraphs)
            except Exception as e:
                print("Error DOCX:", e)
                continue

        if not texto.strip():
            continue

        documento = (d.get("nombre") or "").lower()

        if not documento:
            continue

        fragmentos = texto.split("\n\n")

        for f in fragmentos:

            f = f.strip()

            if len(f) < 40:
                continue

            clean_collection.insert_one({
                "documento": documento,
                "fragmento": f
            })

        documents_collection.update_one(
            {"_id": d["_id"]},
            {
                "$set": {
                    "texto_extraido_ok": True,
                }
            }
        )

        procesados += 1

    return {
        "documentos_extraidos": procesados
    }
