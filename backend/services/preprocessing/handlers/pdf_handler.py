# services/preprocessing/handlers/pdf_handler.py

from database.mongo import index_collection as clean_collection
from backend.services.mineria_service import extraer_keywords, extraer_entidades_basicas

from backend.services.preprocessing.text_normalizer import normalizar_texto_completo
from backend.services.preprocessing.chunking_service import chunkear
from backend.services.preprocessing.section_detector import detectar_seccion_legal
from backend.services.preprocessing.chunk_id_builder import build_chunk_id
from backend.services.preprocessing.document_classifier import detectar_tipo_documento


def procesar_pdf(doc, nombre_doc):

    texto = normalizar_texto_completo(doc.get("texto_extraido", ""))

    tipo_doc = detectar_tipo_documento(texto)
    chunks = chunkear(texto)

    for i, frag in enumerate(chunks):

        chunk_id = build_chunk_id(
            str(doc.get("_id")),
            nombre_doc,
            "PDF",
            "DOCUMENTO",
            i,
            frag
        )

        payload = {
            "chunk_id": chunk_id,
            "documento": nombre_doc,
            "contenido": frag,
            "origen": "DOCUMENTO",
            "tipo": "PDF",
            "metadata": {
                "seccion": detectar_seccion_legal(frag),
                "tipo_documento": tipo_doc,
            },
            "keywords": extraer_keywords(frag),
            "entidades": extraer_entidades_basicas(frag),
        }

        clean_collection.update_one(
            {"chunk_id": chunk_id},
            {"$set": payload},
            upsert=True
        )

    return len(chunks)
