# services/preprocessing/handlers/csv_handler.py

from database import clean_collection
from backend.services.mineria_service import extraer_keywords, extraer_entidades_basicas
from backend.services.preprocessing.chunking_service import chunkear
from backend.services.preprocessing.chunk_id_builder import build_chunk_id
from backend.services.preprocessing.text_normalizer import normalizar_texto_completo


def procesar_csv(doc, nombre_doc):

    texto = ""
    for fila in doc.get("contenido", []):
        texto += " ".join(str(v) for v in fila.values() if v) + ". "

    texto = normalizar_texto_completo(texto)
    chunks = chunkear(texto)

    for i, frag in enumerate(chunks):

        chunk_id = build_chunk_id(
            str(doc.get("_id")),
            nombre_doc,
            "CSV",
            "DOCUMENTO",
            i,
            frag
        )

        payload = {
            "chunk_id": chunk_id,
            "documento": nombre_doc,
            "fragmento": frag,
            "origen": "DOCUMENTO",
            "tipo": "CSV",
            "keywords": extraer_keywords(frag),
            "entidades": extraer_entidades_basicas(frag),
        }

        clean_collection.update_one(
            {"chunk_id": chunk_id},
            {"$set": payload},
            upsert=True
        )

    return len(chunks)