# services/indexing/index_service.py

from database.mongo import clean_collection, index_collection

from backend.services.indexing.text_cleaning import normalize_text
from backend.services.indexing.document_classifier import detectar_tipo_documento
from backend.services.indexing.hashing_utils import sha256_text
from backend.services.indexing.embedding_pipeline import generar_embedding
from backend.services.indexing.mongo_upsert import upsert_chunk
from backend.services.indexing.config import MIN_CHUNK_LENGTH

from backend.services.retrieval_text_utils import normalizar
from backend.services.chunking_juridico import detectar_tipo_chunk

import re


# ==========================================
# 🔥 DETECTOR DE ARTÍCULO
# ==========================================

MAPA_ARTICULOS = {
    "primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4,
    "quinto": 5, "sexto": 6, "septimo": 7, "séptimo": 7,
    "octavo": 8, "noveno": 9, "decimo": 10, "décimo": 10
}

def detectar_articulo(texto: str):

    t = texto.lower()

    m_num = re.search(r'art[ií]culo\s+(\d+)', t)
    if m_num:
        return int(m_num.group(1))

    m_txt = re.search(
        r'art[ií]culo\s+(primero|segundo|tercero|cuarto|quinto|sexto|septimo|séptimo|octavo|noveno|decimo|décimo)',
        t
    )
    if m_txt:
        return MAPA_ARTICULOS.get(m_txt.group(1))

    return None


# ==========================================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================================

def indexar_documentos(*, doc: str | None = None, mode: str = "upsert"):

    doc_norm = normalizar(doc) if doc else None

    if mode == "rebuild":
        print("🧹 Borrando índice anterior...")
        index_collection.delete_many({})

    inserted = 0
    updated = 0
    skipped = 0
    embedding_errors = 0

    # --------------------------------------
    # QUERY
    # --------------------------------------

    query = (
        {
            "$or": [
                {"documento": doc_norm},
                {"metadata.documento": doc_norm}
            ]
        }
        if doc_norm
        else {}
    )

    total_docs = clean_collection.count_documents(query)
    print(f"📄 Documentos encontrados: {total_docs}")

    cursor = list(clean_collection.find(query))

    hashes = set()

    # --------------------------------------
    # LOOP PRINCIPAL
    # --------------------------------------

    for i, row in enumerate(cursor, start=1):

        metadata_row = row.get("metadata", {})

        texto_raw = (
            row.get("fragmento")
            or row.get("contenido")
            or row.get("texto")
            or row.get("text")
            or row.get("chunk")
        )

        documento = (
            row.get("documento")
            or row.get("nombre")
            or metadata_row.get("documento")
        )

        # -------------------------
        # VALIDACIONES
        # -------------------------

        if not texto_raw or not documento:
            skipped += 1
            continue

        if not isinstance(texto_raw, str):
            skipped += 1
            continue

        documento_norm = normalizar(str(documento))

        if not documento_norm:
            skipped += 1
            continue

        # -------------------------
        # LIMPIEZA
        # -------------------------

        texto_chunk = normalize_text(texto_raw)

        if len(texto_chunk.split()) < 15:
            skipped += 1
            continue

        contenido_norm = normalizar(texto_chunk)

        # -------------------------
        # HASH
        # -------------------------

        content_hash = sha256_text(texto_chunk)

        if content_hash in hashes:
            skipped += 1
            continue

        hashes.add(content_hash)

        # -------------------------
        # TIPO CHUNK (🔥 CLAVE)
        # -------------------------

        tipo_chunk = detectar_tipo_chunk(texto_chunk)

        # -------------------------
        # SECCIÓN (derivada simple)
        # -------------------------

        if tipo_chunk in ["resolucion"]:
            seccion = "resolucion"

        elif tipo_chunk == "considerando":
            seccion = "considerando"

        elif tipo_chunk == "objetivo":
            seccion = "objetivo"

        elif tipo_chunk == "postulacion":
            seccion = "postulacion"

        elif tipo_chunk == "requisito":
            seccion = "requisito"

        else:
            seccion = "general"

        # -------------------------
        # TIPO DOCUMENTO
        # -------------------------

        tipo_doc = detectar_tipo_documento(documento_norm, texto_chunk)

        # -------------------------
        # ARTÍCULO
        # -------------------------

        articulo = detectar_articulo(texto_chunk)

        # -------------------------
        # METADATA FINAL
        # -------------------------

        metadata = {
            "documento": documento_norm,
            "documento_norm": documento_norm,
            "tipo_documento": tipo_doc,
            "tipo_chunk": tipo_chunk,
            "seccion": seccion,
            "articulo": articulo,
            "chunk_index": i,
            "longitud": len(texto_chunk.split()),
            "char_length": len(texto_chunk),
            "hash": content_hash,
            "es_resolutivo": tipo_chunk == "resolucion",
        }

        # -------------------------
        # EMBEDDING
        # -------------------------

        try:
            embedding = generar_embedding(texto_chunk, tipo_doc)

            if not embedding:
                embedding_errors += 1
                continue

        except Exception as e:
            print("❌ Error embedding:", e)
            embedding_errors += 1
            continue

        # -------------------------
        # UPSERT
        # -------------------------

        chunk_id = sha256_text(f"{documento_norm}_{i}_{content_hash}")

        try:

            res = upsert_chunk(
                chunk_id,
                texto_chunk,
                metadata,
                embedding,
                content_hash,
                contenido_norm=contenido_norm
            )

            if res.upserted_id:
                inserted += 1
            elif res.modified_count > 0:
                updated += 1

        except Exception as e:
            print("❌ Error Mongo:", e)
            skipped += 1

    # --------------------------------------
    # RESULTADO FINAL
    # --------------------------------------

    print("\n📊 RESULTADO INDEXACIÓN")
    print("Insertados:", inserted)
    print("Actualizados:", updated)
    print("Saltados:", skipped)
    print("Errores embedding:", embedding_errors)

    return {
        "mode": mode,
        "documento_filtrado": doc_norm,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "embedding_errors": embedding_errors
    }
