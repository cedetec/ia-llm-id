# backend/services/retrieval_semantic_ranker.py

from backend.services.embedding_service import embed_text
import numpy as np


# =====================================================
# COSINE SEGURO Y OPTIMIZADO
# =====================================================

def cosine_normalized(a, b):
    """
    Asume embeddings ya normalizados.
    Solo producto punto.
    """
    return float(np.dot(a, b))


# =====================================================
# RERANK SEMÁNTICO
# =====================================================

def rerank_semanticamente(pregunta, docs, top_n=8):
    """
    Reordena docs según similitud semántica.
    Requiere que cada doc tenga campo 'embedding'.
    """

    if not docs:
        return []

    # limitar antes de procesar
    docs = docs[:40]

    # generar embedding QUERY (debe estar normalizado)
    q_emb = embed_text(
        pregunta,
        mode="query",
        normalize=True
    )

    scored = []

    for d in docs:
        emb = d.get("embedding")

        if not emb:
            continue

        sim = cosine_normalized(q_emb, emb)
        scored.append((sim, d))

    # fallback controlado
    if not scored:
        return docs[:top_n]

    scored.sort(key=lambda x: x[0], reverse=True)

    return [d for _, d in scored[:top_n]]