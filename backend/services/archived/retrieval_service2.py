# backend/services/retrieval_service2.py

from typing import List, Dict, Any
import re
from database import index_collection
from backend.services.index_service import embed_text
from backend.services.retrieval_scoring import score_chunk


MAX_CANDIDATOS = 150


# =========================================================
# NORMALIZAR DOCUMENTO
# =========================================================

def normalizar_nombre(nombre: str) -> str:
    if not nombre:
        return ""
    nombre = nombre.lower()
    nombre = nombre.replace(".pdf", "")
    nombre = re.sub(r"\s+", "", nombre)
    return nombre


def detectar_documento(pregunta: str):
    match = re.search(r'([\w\-\s]+\.pdf)', pregunta, re.IGNORECASE)
    if not match:
        return None
    return normalizar_nombre(match.group(1))


# =========================================================
# KEYWORDS SEGURAS
# =========================================================

PALABRAS_CLAVE_JURIDICAS = [
    "RESOLUCION","RESOLUCIÓN",
    "OBJETIVO","FINALIDAD",
    "CONVOCATORIA","REQUISITOS",
    "POSTULAR","POSTULACION",
    "FINANCIAMIENTO",
    "EVALUACION","EVALUACIÓN",
    "ADJUDICACION","ADJUDICACIÓN",
    "BASES","CONCURSO",
    "FONDECYT","ANID",
    "PROYECTO",
    "INVESTIGACION","INVESTIGACIÓN"
]


def extraer_keywords(pregunta: str):
    p = pregunta.upper()
    encontrados = []

    for palabra in PALABRAS_CLAVE_JURIDICAS:
        if palabra in p:
            encontrados.append(palabra)

    return list(set(encontrados))


# =========================================================
# BUSCAR CONTEXTO UNIFICADO
# =========================================================

def buscar_contexto(pregunta: str, k: int = 5):

    documento_objetivo = detectar_documento(pregunta)
    keywords = extraer_keywords(pregunta)

    filtro = {"embedding": {"$exists": True}}

    if documento_objetivo:
        filtro["metadata.documento_norm"] = documento_objetivo

    candidatos = list(
        index_collection.find(
            filtro,
            {"contenido": 1, "embedding": 1, "metadata": 1}
        ).limit(MAX_CANDIDATOS)
    )

    if not candidatos:
        return []

    # embedding query (normalizado)
    q_emb = embed_text(f"query: {pregunta}", normalize=True)

    scored = []

    for d in candidatos:

        contenido = d.get("contenido", "")
        emb = d.get("embedding")

        if not emb:
            continue

        meta = d.get("metadata", {})
        doc_chunk = normalizar_nombre(meta.get("documento", ""))

        if documento_objetivo and doc_chunk != documento_objetivo:
            continue

        score_lex = score_chunk(contenido, keywords, modo_cita=False)

        score_sem = sum(a*b for a, b in zip(q_emb, emb))

        seccion = str(meta.get("seccion", "")).upper()
        boost = 0

        if "OBJETIVO" in keywords and "OBJETIVO" in seccion:
            boost += 80

        if "REQUISITOS" in keywords and "REQUISITO" in seccion:
            boost += 80

        if "POSTULAR" in keywords and "POSTUL" in seccion:
            boost += 80

        score_final = (score_lex * 0.6) + (score_sem * 0.4) + boost

        scored.append((score_final, d))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [d for _, d in scored[:k]]

