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
from backend.services.retrieval_text_utils import safe_split


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

        cont = (
            d.get("contenido")
            or d.get("contenido_norm")
            or d.get("texto")
            or ""
        )

        if isinstance(cont, dict):
            cont = cont.get("contenido") or cont.get("texto") or ""

        elif isinstance(cont, list):
            cont = " ".join(
                x.get("contenido", "") if isinstance(x, dict) else str(x)
                for x in cont
            )

        elif not isinstance(cont, str):
            cont = str(cont)

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
        # 🔥 BOOST SI EL NOMBRE DEL DOCUMENTO ESTÁ EN EL CHUNK
        # ----------------------------------
        doc_name = meta.get("documento_norm", "")
        if doc_name and doc_name in cont_l:
            total += 10

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
        total = (score_lex * 5.0) + (score_sem * 2.0)

        # =====================================
        # 🔥 BOOST POR NOMBRE DE DOCUMENTO
        # =====================================
        doc_name = meta.get("documento_norm", "")
        if doc_name and doc_name in preg_l:
            total += 20

        # =====================================
        # 🔥 BOOST FRASES EXACTAS
        # =====================================
        frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', preg_l)
        for f in frases:
            if f in cont_l:
                total += 60

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

        # ----------------------------------
        # 🔥 BOOST FUERTE POR INTENT + TIPO
        # ----------------------------------

        if intent == "objetivo" and tipo == "objetivo":
            total += 40

        elif intent == "requisito" and tipo in ["requisito", "postulacion"]:
            total += 35

        elif intent == "beneficiarios" and tipo in ["beneficiarios", "postulacion"]:
            total += 35

        elif intent == "resolucion" and tipo in ["resolucion", "articulo_resolucion"]:
            total += 45

        elif intent == "evaluacion" and tipo == "evaluacion":
            total += 35

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
            total -= 15

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
                "persona natural",
                "podran postular",
                "podran participar"
            ]):
                total += 40

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

        # =====================================
        # 🔥 BOOST POR ARTÍCULO
        # =====================================
        articulo_meta = meta.get("articulo")
        if articulo_meta and str(articulo_meta) in preg_l:
            total += 25

        if idx < 5:
            total += 6
        elif idx < 15:
            total += 3

        # ----------------------------------
        # 🔥 LONGITUD IDEAL
        # ----------------------------------

        length = len(safe_split(cont))

        # =====================================
        # 🔥 PENALIZAR CHUNKS MUY LARGOS
        # =====================================
        char_len = len(cont)

        if char_len > 1500:
            total -= 6
        elif char_len > 900:
            total -= 2

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

        # 🔥 boost si contiene números relevantes
        if any(w in preg_l for w in ["numero", "fecha", "monto", "duracion", "ano", "resolucion"]):
            if re.search(r'\d{2,5}[/\-]\d{2,4}', cont_l):
                total += 25

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

            if len(safe_split(cont)) < 6:
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
        key = d.get("contenido_norm", "")[:200]

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
