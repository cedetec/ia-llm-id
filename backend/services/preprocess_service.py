# services/preprocessing/preprocess_service.py

from database import documents_collection
from backend.services.preprocessing.handlers.csv_handler import procesar_csv
from backend.services.preprocessing.handlers.pdf_handler import procesar_pdf


def preprocesar_documentos(doc=None):

    docs_procesados = 0
    docs_saltados = 0
    total_chunks = 0

    query = {"texto": {"$exists": True}}

    if doc:
        query["nombre"] = doc

    for d in documents_collection.find(query):

        if not isinstance(d, dict):
            docs_saltados += 1
            continue

        nombre_doc = d.get("nombre", "").lower()
        tipo = (d.get("tipo") or "").upper()

        if tipo == "CSV":
            total_chunks += procesar_csv(d, nombre_doc)
            docs_procesados += 1
            continue

        if tipo in ("PDF", "DOCX") and d.get("texto_extraido"):
            total_chunks += procesar_pdf(d, nombre_doc)
            docs_procesados += 1
            continue

        docs_saltados += 1

    return {
        "fragmentos_creados": total_chunks,
        "docs_procesados": docs_procesados,
        "docs_saltados": docs_saltados,
    }
