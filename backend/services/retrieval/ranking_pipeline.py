# ranking_pipeline.py
import re

from backend.services.embedding_service import embed_text
from backend.services.retrieval_scoring import score_chunk
from backend.services.rerank_legal import rerank_legal_chunks

from backend.services.ranking_utils import cosine
from backend.services.retrieval_text_utils import normalizar

from backend.services.ranking_intent import (
    detectar_intent,
    detectar_pregunta_beneficiarios
)

from backend.services.retrieval.intent_utils import detectar_seccion_simple
from backend.services.retrieval.ranking_boosts_anid import aplicar_boosts_anid


# ==========================================
# 🔥 CONFIG
# ==========================================

RUIS_LEGAL = [
    "recurso de reposicion",
    "plazo para interponer",
    "dias habiles",
    "carta certificada",
    "notificacion",
    "seran notificados",
    "sin perjuicio",
    "de conformidad con",
    "facultades que detenta",
    "adjunto al acto administrativo",
]

RUIDO_TECNICO = [
    "tabla", "figura", "ranking", "editorial", "scopus"
]


# ==========================================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================================

def rankear_chunks(pregunta, docs, toks, modo_cita=False):

    preg_l = normalizar(pregunta)

    intent = detectar_intent(preg_l)
    seccion_detectada = detectar_seccion_simple(pregunta)

    if seccion_detectada:
        intent = seccion_detectada  # 🔥 manda la sección

    # ----------------------------------
    # 🔥 EMBEDDING
    # ----------------------------------

    try:
        q_emb = embed_text(pregunta)
    except:
        q_emb = None

    ranked = []

    # ==========================================
    # 🔥 LOOP PRINCIPAL
    # ==========================================

    for d in docs:

        cont = str(d.get("contenido") or "")
        if not cont:
            continue

        cont_l = d.get("contenido_norm", "")
        meta = d.get("metadata") or {}

        # ----------------------------------
        # ❌ FILTRO DURO (CRÍTICO)
        # ----------------------------------

        if any(x in cont_l for x in RUIS_LEGAL):
            continue

        if any(x in cont_l for x in RUIDO_TECNICO):
            continue

        if len(cont_l) < 40:
            continue

        # ----------------------------------
        # 🔥 SCORE BASE
        # ----------------------------------

        score_lex = float(score_chunk(
            cont,
            toks,
            modo_cita=modo_cita,
            seccion_objetivo=intent
        ))

        score_sem = 0.0
        emb = d.get("embedding")

        if q_emb is not None and emb is not None:
            try:
                score_sem = cosine(q_emb, emb)
            except:
                pass

        # 🔥 IMPORTANTE: bajar peso semántico
        total = (score_lex * 4.0) + (score_sem * 3.0)

        # ----------------------------------
        # 🔥 MATCH DIRECTO (CLAVE)
        # ----------------------------------

        match_count = sum(1 for t in toks if t in cont_l)

        if match_count >= 4:
            total += 30
        elif match_count == 3:
            total += 18
        elif match_count == 2:
            total += 8

        # ----------------------------------
        # 🔥 TIPO DE CHUNK
        # ----------------------------------

        tipo = meta.get("tipo_chunk", "")

        if tipo == "articulo_resolucion":
            total += 18
        elif tipo == "resolucion":
            total += 14
        elif tipo == "objetivo":
            total += 20
        elif tipo == "requisito":
            total += 18
        elif tipo == "considerando":
            total += 2
        elif tipo == "bases_concurso":
            total -= 8
        elif tipo == "postulacion":
            total += 15
        elif tipo == "general":
            total -= 25

        # ----------------------------------
        # 🔥 INTENT BOOST (NO DESTRUCTIVO)
        # ----------------------------------

        if intent == "objetivo":
            if any(x in cont_l for x in [
                "objetivo del concurso",
                "objetivo general",
                "tiene por objetivo",
                "finalidad"
            ]):
                total += 50

        elif intent == "requisito":
            if any(x in cont_l for x in [
                "requisitos",
                "deben",
                "deberan",
                "postular"
            ]):
                total += 35

        elif intent == "beneficiarios":
            if any(x in cont_l for x in [
                "beneficiario",
                "postulante",
                "persona natural"
            ]):
                total += 25

        elif intent == "resolucion":
            if any(x in cont_l for x in [
                "resuelv",
                "aprueb",
                "resolucion"
            ]):
                total += 30

        # ❗ IMPORTANTE: NO castigar fuerte mismatch

        # ----------------------------------
        # 🔥 SECCIÓN MATCH (CLAVE)
        # ----------------------------------

        seccion = normalizar(meta.get("seccion", ""))

        if intent and seccion == intent:
            total += 60
        elif intent and intent in seccion:
            total += 20

        # ----------------------------------
        # 🔥 POSICIÓN
        # ----------------------------------

        idx = meta.get("chunk_index", 999)

        if idx < 5:
            total += 6
        elif idx < 15:
            total += 3

        # ----------------------------------
        # 🔥 LONGITUD IDEAL
        # ----------------------------------

        length = len(cont.split())

        if 80 <= length <= 220:
            total += 4
        elif length < 30:
            total -= 5

        # ----------------------------------
        # 🔥 SEÑALES LEGALES
        # ----------------------------------

        if "resuelv" in cont_l:
            total += 12

        if "resolucion exenta" in cont_l:
            total += 10

        if re.search(r'\bart[ií]culo\s+\d+', cont_l):
            total += 8

        # ----------------------------------
        # 🔥 PENALIZACIONES SUAVES
        # ----------------------------------

        if "modificacion de convenio" in cont_l:
            total -= 8

        if sum(c.isdigit() for c in cont_l) > 100:
            total -= 5

        # ----------------------------------
        # 🔥 BOOST ANID
        # ----------------------------------

        boost_anid = aplicar_boosts_anid(
            0,
            cont_l,
            cont_l[:300],
            meta.get("seccion", ""),
            intent,
            detectar_pregunta_beneficiarios(preg_l)
        )

        total += boost_anid * 0.3

        # ----------------------------------
        # 🔥 MODO CITA
        # ----------------------------------

        if modo_cita:
            if re.search(r'\b(resolucion|apruebase|resuelvo|objetivo)\b', cont_l):
                total += 12

            if len(cont.split()) < 6:
                total -= 5

        # ----------------------------------
        # 🔥 FINAL
        # ----------------------------------

        d["score"] = float(max(total, 0))
        ranked.append(d)

    # ==========================================
    # 🔥 DEDUPLICACIÓN
    # ==========================================

    seen = set()
    filtered = []

    for d in ranked:
        key = d.get("contenido_norm", "")[:400]

        if key in seen:
            continue

        seen.add(key)
        filtered.append(d)

    # ----------------------------------
    # 🔥 ORDEN
    # ----------------------------------

    filtered.sort(key=lambda x: x["score"], reverse=True)

    # ----------------------------------
    # 🔥 RE-RANK FINAL
    # ----------------------------------

    final = rerank_legal_chunks(pregunta, filtered)

    return final[:15]
