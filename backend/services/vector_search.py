#vector_search.py
from sentence_transformers import SentenceTransformer
from database.mongo import index_collection
from backend.services.retrieval_text_utils import normalizar

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model


def buscar_semanticamente(pregunta, documento=None, seccion=None, k=60):

    model = _get_model()

    pregunta = pregunta.strip()

    # 🔥 IMPORTANTE: formato correcto E5
    query_embedding = model.encode(
        f"query: {pregunta}",
        normalize_embeddings=True
    )

    query_embedding = list(query_embedding)

    # -------------------------------------------------
    # FILTRO DINÁMICO
    # -------------------------------------------------

    filtro = {}

    if documento:
        filtro["metadata.documento_norm"] = normalizar(documento)

    if seccion:
        filtro["metadata.seccion"] = seccion

    # -------------------------------------------------
    # VECTOR SEARCH
    # -------------------------------------------------

    vector_stage = {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,
            "numCandidates": 800,   # 🔥 subir recall
            "limit": k,
        }
    }

    if filtro:
        vector_stage["$vectorSearch"]["filter"] = filtro

    pipeline = [
        vector_stage,
        {
            "$project": {
                "contenido": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(index_collection.aggregate(pipeline))

    filtrados = []

    for r in results:
        meta = r.get("metadata", {})
        seccion = (meta.get("seccion") or "").lower()

        if any(x in seccion for x in ["anexo", "referencias", "bibliografia"]):
            continue

        filtrados.append(r)

    results = filtrados

    # -------------------------------------------------
    # NORMALIZAR + ENRIQUECER RESULTADOS
    # -------------------------------------------------

    for r in results:

        score = float(r.get("score", 0))

        # ----------------------------------
        # 🔥 NORMALIZAR TEXTO (para ranking posterior)
        # ----------------------------------

        r["contenido_norm"] = normalizar(r.get("contenido", ""))

        # ----------------------------------
        # 🔥 BOOST TEMPRANO POR TIPO
        # ----------------------------------

        meta = r.get("metadata", {})
        tipo = meta.get("tipo_chunk", "")

        boost = 0

        if tipo == "articulo_resolucion":
            boost += 5
        elif tipo == "resolucion":
            boost += 4

        # ----------------------------------
        # 🔥 SCORE FINAL
        # ----------------------------------

        r["score_sem"] = score
        r["score"] = score * 100 + boost

        return results
