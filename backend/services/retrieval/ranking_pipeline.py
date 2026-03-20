#ranking_pipeline.py
import re

from backend.services.embedding_service import embed_text
from backend.services.retrieval_scoring import score_chunk
from backend.services.rerank_legal import rerank_legal_chunks

from backend.services.ranking_utils import (
    cosine,
    normalizar_txt,
)

from backend.services.ranking_intent import (
    detectar_intent,
    detectar_pregunta_beneficiarios
)

from backend.services.ranking_boosts import (
    boost_frase,
    boost_posicion,
    penalizar_repeticion
)

from backend.services.ranking_heuristicas_legales import heuristicas_juridicas
from backend.services.ranking_filters import es_texto_administrativo
from backend.services.retrieval.ranking_boosts_anid import aplicar_boosts_anid


def rankear_chunks(pregunta, docs, toks, modo_cita=False):

    preg_l = normalizar_txt(pregunta)

    intent = detectar_intent(preg_l)

    try:
        q_emb = embed_text(pregunta)
    except:
        q_emb = None

    ranked = []

    for d in docs:

        cont = str(d.get("contenido") or "")
        meta = d.get("metadata") or {}

        if not cont:
            continue

        cont_l = d.get("contenido_norm", "")
        titulo = normalizar_txt(meta.get("titulo", ""))

        tipo = meta.get("tipo_chunk", "")
        idx = meta.get("chunk_index", 999)

        # ----------------------------------
        # 🔥 FASE 1: SCORE BASE
        # ----------------------------------

        score_lex = float(score_chunk(cont, toks, modo_cita=modo_cita))

        score_sem = 0.0
        emb = d.get("embedding")

        if q_emb is not None and emb is not None:
            try:
                score_sem = cosine(q_emb, emb)
            except:
                score_sem = 0.0

        total = (score_lex * 2.0) + (score_sem * 8.0)

        # ----------------------------------
        # 🔥 FASE 2: POSICIÓN Y LONGITUD
        # ----------------------------------

        if idx < 5:
            total += 5
        elif idx < 10:
            total += 3
        elif idx > 50:
            total -= 2

        length = len(cont.split())

        if 80 <= length <= 250:
            total += 3
        elif length < 40:
            total -= 3

        # ----------------------------------
        # 🔥 FASE 3: TIPO DE CHUNK
        # ----------------------------------

        if tipo == "articulo_resolucion":
            total += 12
        elif tipo == "resolucion":
            total += 10
        elif tipo == "considerando":
            total += 4
        elif tipo == "bases_concurso":
            total += 6

        # ----------------------------------
        # 🔥 FASE 4: INTENCIÓN (CLAVE)
        # ----------------------------------

        if intent == "resolucion":
            if tipo in ["resolucion", "articulo_resolucion"]:
                total += 25
            if "resuelv" in cont_l:
                total += 20

        elif intent == "objetivo":
            if "objetivo del concurso" in cont_l:
                total += 30
            elif "objetivo" in cont_l:
                total += 15

        elif intent == "requisito":
            if any(x in cont_l for x in ["deben", "requisito", "postular"]):
                total += 20

        elif intent == "beneficiarios":
            if any(x in cont_l for x in ["beneficiario", "postulante", "persona natural"]):
                total += 18

        # ----------------------------------
        # 🔥 FASE 5: SEÑALES LEGALES FUERTES
        # ----------------------------------

        if "aprueb" in cont_l:
            total += 15

        if "resuelv" in cont_l:
            total += 18

        if re.search(r'\bart[ií]culo\s+\d+', cont_l):
            total += 10

        # ----------------------------------
        # 🔥 FASE 6: PENALIZACIONES
        # ----------------------------------

        if len(cont_l) > 2000:
            total -= 6

        if re.search(r'(tabla|figura|ranking|editorial|impacto|scopus)', cont_l):
            total -= 20

        if sum(c.isdigit() for c in cont_l) > 80:
            total -= 6

        if "no se aprueb" in cont_l:
            total -= 10

        # ----------------------------------
        # 🔥 FASE 7: BOOSTS ANID
        # ----------------------------------

        seccion = meta.get("seccion", "")
        inicio = cont[:300].lower()
        preg_benef = detectar_pregunta_beneficiarios(preg_l)

        boost_anid = aplicar_boosts_anid(
            0,
            cont_l,
            inicio,
            seccion,
            intent,
            preg_benef
        )

        total += boost_anid * 0.3

        # ----------------------------------
        # 🔥 SCORE FINAL
        # ----------------------------------

        d["score"] = float(max(total, 0))
        ranked.append(d)

    # ----------------------------------
    # ORDENAR
    # ----------------------------------

    # 🔥 penalizar duplicados semánticos
    seen_texts = set()
    filtered = []

    for d in ranked:
        txt = d.get("contenido_norm", "")[:200]

        if txt in seen_texts:
            continue

        seen_texts.add(txt)
        filtered.append(d)

    ranked = filtered

    ranked.sort(key=lambda x: x["score"], reverse=True)

    # ----------------------------------
    # RE-RANKING FINAL (legal)
    # ----------------------------------

    ranked = rerank_legal_chunks(pregunta, ranked)

    return ranked[:15]
