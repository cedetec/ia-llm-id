from __future__ import annotations

import os
from datetime import datetime
from fastapi import UploadFile

from database.mongo import documents_collection, clean_collection, fs
from backend.utils.ocr_pdf_extractor import extract_text_smart

import pdfplumber
import hashlib
import re


# ==========================================================
# 1️⃣ SUBIR DOCUMENTO
# ==========================================================

async def subir_documento_service(file: UploadFile):

    if not file.filename:
        raise ValueError("Archivo inválido")

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    existing = documents_collection.find_one({"sha256": sha256})

    if existing:
        return {
            "message": "Documento ya existía (mismo hash)",
            "archivo": file.filename,
            "gridfs_id": str(existing.get("gridfs_id")),
            "sha256": sha256
        }

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
        "texto_extraido_ok": False
    }

    documents_collection.insert_one(doc_payload)

    return {
        "message": "Documento subido correctamente",
        "archivo": file.filename,
        "gridfs_id": str(gridfs_id),
        "sha256": sha256
    }


# ==========================================================
# 2️⃣ EXTRAER TEXTO
# ==========================================================

def extraer_documentos(doc: str | None = None):

    query = {"nombre": doc.lower()} if doc else {}

    procesados = 0

    for d in fs.find():

        filename = d.filename.lower()

        if doc and filename != doc.lower():
            continue

        print("📄 Procesando:", filename)

        gridfs_id = d._id

        file_data = fs.get(gridfs_id)

        ruta_tmp = f"/tmp/{filename}"

        with open(ruta_tmp, "wb") as f:
            f.write(file_data.read())

        texto = ""

        try:
            with pdfplumber.open(ruta_tmp) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        texto += txt + "\n\n"

        except Exception as e:
            print("⚠ Error leyendo PDF:", e)

        if len(texto.strip()) < 100:

            print("🧠 PDF escaneado detectado → activando OCR...")

            try:
                texto = extract_text_smart(ruta_tmp)
            except Exception as e:
                print("❌ Error OCR:", e)
                continue

        documento = filename

        # ==================================================
        # LIMPIEZA OCR
        # ==================================================

        texto = re.sub(r'\(cid:\d+\)', ' ', texto)
        texto = re.sub(r'[^\x00-\x7FáéíóúÁÉÍÓÚñÑ0-9\.,;:\-\(\) ]', ' ', texto)
        texto = texto.replace("\n", " ")
        texto = re.sub(r'\s+', ' ', texto)

        # ==================================================
        # FRAGMENTACIÓN
        # ==================================================

        fragmentos = re.split(
            r'\.\s+(?=[A-ZÁÉÍÓÚÑ])|\n{2,}',
            texto
        )

        fragmentos = [
            f.strip()
            for f in fragmentos
            if len(f.strip()) > 40
        ]

        # ==================================================
        # CONTROL DE TAMAÑO
        # ==================================================

        MAX_FRAGMENT = 1800

        fragmentos_finales = []

        for f in fragmentos:

            if len(f) <= MAX_FRAGMENT:
                fragmentos_finales.append(f)

            else:

                for i in range(0, len(f), MAX_FRAGMENT):
                    fragmentos_finales.append(f[i:i+MAX_FRAGMENT])

        fragmentos = fragmentos_finales

        # ==================================================
        # INSERTAR EN CLEAN COLLECTION
        # ==================================================

        inserted = 0

        for f in fragmentos:

            if len(f) < 40:
                continue

            clean_collection.insert_one({
                "documento": documento,
                "fragmento": f
            })

            inserted += 1

        print(f"🧩 Fragmentos creados: {inserted}")

        # ==================================================
        # MARCAR COMO PROCESADO
        # ==================================================

        procesados += 1

    return {
        "documentos_extraidos": procesados
    }

def preprocesar_documentos(doc: str | None = None):

    query = {"documento": doc.lower()} if doc else {}

    procesados = 0

    cursor = clean_collection.find(query)

    for row in cursor:

        texto = row.get("fragmento")

        if not texto:
            continue

        # limpieza básica
        texto = texto.strip()

        texto = re.sub(r'\s+', ' ', texto)

        texto = texto.replace(" ,", ",")
        texto = texto.replace(" .", ".")

        clean_collection.update_one(
            {"_id": row["_id"]},
            {
                "$set": {
                    "fragmento": texto,
                    "preprocesado": True
                }
            }
        )

        procesados += 1

    return {
        "fragmentos_preprocesados": procesados
    }
