# services/indexing/index_service.py

from database.mongo import clean_collection, index_collection

from backend.services.indexing.text_cleaning import normalize_text
from backend.services.indexing.document_classifier import detectar_tipo_documento
from backend.services.indexing.hashing_utils import sha256_text
from backend.services.indexing.embedding_pipeline import generar_embedding
from backend.services.indexing.mongo_upsert import upsert_chunk
from backend.services.indexing.config import MIN_CHUNK_LENGTH

from backend.services.retrieval_text_utils import normalizar, safe_split
from backend.services.chunking_juridico import detectar_tipo_chunk

import re

def limpiar_texto_ocr(texto: str) -> str:
    t = texto.lower()

    palabras = safe_split(t)
    if not palabras:
        return ""

    # ❌ palabras sin vocales (más confiable)
    validas = [
        p for p in palabras
        if sum(c in "aeiouáéíóú" for c in p) >= 1
    ]

    if len(validas) < len(palabras) * 0.25:
        return ""

    # ❌ exceso de símbolos
    letras = sum(c.isalpha() for c in t)
    if letras < len(t) * 0.3:
        return ""

    # ❌ SOLO si hay MUCHAS secuencias raras
    if len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{6,}', t)) >= 3:
        return ""

    # limpieza
    t = re.sub(r'[^a-z0-9áéíóúñü\s\.\,\-\(\)/°]', ' ', t)
    t = re.sub(r'\s+', ' ', t)

    return t.strip()

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

    MAX_CHUNKS_PER_DOC = 1000
    doc_chunk_count = {}
    doc_inserted_count = {}

    # ✅ DEBUG DOCUMENTOS
    docs_vistos = set()
    doc_skip_count = {}

    def registrar_skip(doc):
        doc_skip_count.setdefault(doc, 0)
        doc_skip_count[doc] += 1

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
            if documento:
                registrar_skip(normalizar(str(documento)))
            continue

        if not isinstance(texto_raw, str):
            skipped += 1
            if documento:
                registrar_skip(normalizar(str(documento)))
            continue

        documento_norm = normalizar(str(documento))

        if not documento_norm:
            skipped += 1
            registrar_skip(documento_norm)
            continue

        docs_vistos.add(documento_norm)

        # 🔥 LIMITAR CHUNKS POR DOCUMENTO
        doc_key = documento_norm
        doc_chunk_count.setdefault(doc_key, 0)
        doc_inserted_count.setdefault(doc_key, 0)

        if doc_chunk_count[doc_key] >= MAX_CHUNKS_PER_DOC:
            continue

        doc_chunk_count[doc_key] += 1

        # -------------------------
        # LIMPIEZA
        # -------------------------

        # 🔥 LIMPIEZA TEMPRANA
        texto_chunk = normalize_text(texto_raw)

        texto_filtrado = limpiar_texto_ocr(texto_chunk)

        if documento_norm == "09-22-res-bases-apoyo-basal-2022.pdf":
            print(f"DEBUG LEN: {len(safe_split(texto_filtrado))} → {texto_filtrado[:120]}")

        # 🔥 SI OCR FALLA → USAR TEXTO ORIGINAL LIMPIO (fallback)
        if not texto_filtrado:
            print(f"⚠️ OCR débil, usando fallback: {documento_norm}")
            texto_filtrado = texto_chunk  # 🔥 CLAVE

        MIN_WORDS = 8

        if len(safe_split(texto_filtrado)) < MIN_WORDS:

            # 🚨 permitir al menos algunos chunks si el documento está vacío
            if doc_inserted_count[doc_key] == 0:
                print(f"⚠️ Forzando chunk mínimo: {documento_norm}")
            else:
                skipped += 1
                registrar_skip(documento_norm)
                continue

        contenido_norm = normalizar(texto_filtrado)

        if not contenido_norm:
            continue

        # 🔥 boost secciones importantes
        if len(safe_split(contenido_norm)) > 220:
            palabras = safe_split(texto_filtrado)
            texto_filtrado = " ".join(palabras[:220])
            contenido_norm = normalizar(texto_filtrado)

        # -------------------------
        # HASH
        # -------------------------

        content_hash = sha256_text(texto_filtrado)

        if content_hash in hashes:
            registrar_skip(documento_norm)
            continue

        hashes.add(content_hash)

        # -------------------------
        # TIPO CHUNK (🔥 CLAVE)
        # -------------------------

        tipo_chunk = detectar_tipo_chunk(texto_filtrado)

        cont_l = contenido_norm

        # 🔥 fallback si clasificador falla
        if tipo_chunk == "general":

            if re.search(r'\b(objetivo|finalidad|proposito)\b', cont_l):
                tipo_chunk = "objetivo"

            elif re.search(r'\b(requisito|condiciones)\b', cont_l):
                tipo_chunk = "requisito"

            elif re.search(r'\b(postul|beneficiario)\b', cont_l):
                tipo_chunk = "beneficiarios"

            elif re.search(r'\b(financiamiento|monto|recursos)\b', cont_l):
                tipo_chunk = "financiamiento"

            elif re.search(r'\b(duracion|plazo|vigencia)\b', cont_l):
                tipo_chunk = "duracion"

            elif re.search(r'\b(evaluacion|criterios)\b', cont_l):
                tipo_chunk = "evaluacion"

            elif re.search(r'\b(resuelv|aprueb|resolucion)\b', cont_l):
                tipo_chunk = "resolucion"

            elif re.search(r'\b(considerando|visto)\b', cont_l):
                tipo_chunk = "considerando"

        # -------------------------
        # SECCIÓN (derivada simple)
        # -------------------------

        if tipo_chunk in ["resolucion"]:
            seccion = "resolucion"

        elif tipo_chunk == "considerando":
            seccion = "considerando"

        elif tipo_chunk == "objetivo":
            seccion = "objetivo"

        elif tipo_chunk in ["postulacion", "beneficiarios"]:
            seccion = "beneficiarios"

        elif tipo_chunk == "requisito":
            seccion = "requisito"

        else:
            # 🔥 fallback semántico
            if re.search(r'\bobjetivo(s)?\b', contenido_norm):
                seccion = "objetivo"

            elif re.search(r'\brequisito(s)?\b', contenido_norm):
                seccion = "requisitos"

            elif re.search(r'\b(postul|beneficiario)\b', contenido_norm):
                seccion = "postulacion"

            elif re.search(r'\b(resuelv|aprueb|resolucion)\b', contenido_norm):
                seccion = "resolucion"

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
            "longitud": len(safe_split(texto_chunk)),
            "char_length": len(texto_chunk),
            "hash": content_hash,
            "es_resolutivo": tipo_chunk == "resolucion",
        }

        # -------------------------
        # EMBEDDING
        # -------------------------

        try:
            embedding = generar_embedding(contenido_norm, tipo_doc)

            if not embedding:
                embedding_errors += 1
                registrar_skip(documento_norm)
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
                texto_filtrado,
                metadata,
                embedding,
                content_hash,
                contenido_norm=contenido_norm
            )

            if res.upserted_id:
                inserted += 1
                doc_inserted_count[doc_key] += 1  # 🔥 CLAVE
            elif res.modified_count > 0:
                updated += 1
                doc_inserted_count[doc_key] += 1

            

        except Exception as e:
            print("❌ Error Mongo:", e)
            skipped += 1
            registrar_skip(documento_norm)

    print("\n📊 DOCUMENTOS INDEXADOS:")
    print(docs_vistos)

    print("\n📊 SKIPS POR DOCUMENTO:")
    for doc, count in doc_skip_count.items():
        print(doc, "→", count)

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
