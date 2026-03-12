# services/indexing/index_service.py

from database import clean_collection, index_collection
from backend.services.indexing.text_cleaning import normalize_text
from backend.services.indexing.document_classifier import detectar_tipo_documento
from backend.services.indexing.section_classifier import clasificar_seccion
from backend.services.indexing.hashing_utils import sha256_text
from backend.services.indexing.embedding_pipeline import generar_embedding
from backend.services.indexing.mongo_upsert import upsert_chunk
from backend.services.indexing.config import MIN_CHUNK_LENGTH
from backend.services.retrieval_text_utils import normalizar
from backend.services.chunking_juridico import (
    reconstruir_secciones,
    extraer_nombre_seccion
)

from langchain_text_splitters import RecursiveCharacterTextSplitter


def indexar_documentos(*, doc: str | None = None, mode: str = "upsert"):

    # ----------------------------------------
    # Normalizar filtro de documento
    # ----------------------------------------

    doc_norm = normalizar(doc) if doc else None

    if mode == "rebuild":
        index_collection.delete_many({})

    inserted = 0
    updated = 0

    buffer_docs: dict[str, list[str]] = {}

    # ----------------------------------------
    # Query Mongo
    # ----------------------------------------

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

    cursor = clean_collection.find(query)

    # ----------------------------------------
    # ACUMULAR TEXTO POR DOCUMENTO
    # ----------------------------------------

    for row in cursor:

        contenido_raw = (
            row.get("fragmento")
            or row.get("contenido")
            or row.get("texto")
            or row.get("text")
            or row.get("chunk")
        )

        if not isinstance(contenido_raw, str):
            continue

        contenido = normalize_text(contenido_raw)

        if len(contenido) < MIN_CHUNK_LENGTH:
            continue

        documento = (
            row.get("documento")
            or row.get("metadata", {}).get("documento")
            or row.get("nombre")
        )

        if not documento:
            continue

        documento = str(documento)

        buffer_docs.setdefault(documento, []).append(contenido)

    # ----------------------------------------
    # PROCESAR DOCUMENTOS
    # ----------------------------------------

    for documento, fragmentos in buffer_docs.items():

        documento_norm = normalizar(documento)

        texto_doc = "\n".join(fragmentos)

        # dividir primero el documento
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250
        )

        chunks_base = splitter.split_text(texto_doc)

        # luego reconstruir secciones jurídicas
        chunks = reconstruir_secciones(chunks_base)

        # ----------------------------------------
        # DEDUPLICACIÓN DE CHUNKS SIMILARES
        # ----------------------------------------

        chunks_filtrados = []
        hashes = set()

        for ch in chunks:

            txt = ch.strip()

            if len(txt) < 40:
                continue

            # hash semántico corto
            h = sha256_text(txt[:500])

            if h in hashes:
                continue

            hashes.add(h)
            chunks_filtrados.append(txt)

        chunks = chunks_filtrados

        total_chunks = len(chunks)

        for i, texto_chunk in enumerate(chunks):

            if not texto_chunk or len(texto_chunk) < 30:
                continue

            if len(texto_chunk) > 2000:
                texto_chunk = texto_chunk[:2000]

            tipo_doc = detectar_tipo_documento(documento, texto_chunk)

            seccion = (
                extraer_nombre_seccion(texto_chunk)
                or clasificar_seccion(texto_chunk)
            )

            metadata = {
                "documento": documento_norm,
                "documento_norm": documento_norm,
                "tipo_documento": tipo_doc,
                "seccion": seccion,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "longitud": len(texto_chunk.split())
            }

            embedding = generar_embedding(texto_chunk, tipo_doc)

            content_hash = sha256_text(texto_chunk)

            # hash más estable
            chunk_id = sha256_text(f"{documento_norm}_{i}_{total_chunks}")

            res = upsert_chunk(
                chunk_id,
                texto_chunk,
                metadata,
                embedding,
                content_hash,
            )

            if res.upserted_id:
                inserted += 1
            elif res.modified_count > 0:
                updated += 1

    return {
        "mode": mode,
        "documento_filtrado": doc_norm,
        "inserted": inserted,
        "updated": updated,
    }
