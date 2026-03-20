#ranking_pipeline.py
import re

from services.embedding_service import embed_text
from services.retrieval_scoring import score_chunk
from services.rerank_legal import rerank_legal_chunks

from services.ranking_utils import (
    cosine,
    normalizar_txt,
)

from services.ranking_intent import (
    detectar_intent,
    detectar_pregunta_beneficiarios
)

from services.ranking_boosts import (
    boost_frase,
    boost_posicion,
    penalizar_repeticion
)

from services.ranking_heuristicas_legales import heuristicas_juridicas
from services.ranking_filters import es_texto_administrativo
from services.retrieval.ranking_boosts_anid import aplicar_boosts_anid


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
        d["contenido_norm"] = cont_l

        titulo = normalizar_txt(meta.get("titulo", ""))

        # ----------------------------------
        # FILTRO: eliminar basura administrativa
        # ----------------------------------

        #if es_texto_administrativo(cont_l):
        #    continue

        # ----------------------------------
        # 🔥 FILTRO: eliminar anexos y tablas
        # ----------------------------------

        seccion = (meta.get("seccion") or "").lower()

        if any(x in seccion for x in [
            "anexo", "tabla", "referencias", "bibliografia", "apendice"
        ]):
            continue

        # ----------------------------------
        # SIMILITUD SEMÁNTICA (EMBEDDING)
        # ----------------------------------

        emb = d.get("embedding")

        # --- score léxico ---
        score_lex = float(score_chunk(cont, toks, modo_cita=modo_cita))

        total = score_lex

        for t in toks:
            if len(t) > 4 and t in titulo:
                total += 3

        # --- score semántico ---
        score_sem = 0.0
        if q_emb is not None and emb is not None:
            try:
                score_sem = cosine(q_emb, emb)
            except:
                score_sem = 0.0

        # 🔥 SCORE HÍBRIDO ROBUSTO

        score_sem = score_sem if score_sem > 0 else 0

        total = (
            (score_lex * 2.0) +     # 👈 léxico domina
            (score_sem * 10.0)      # 👈 semántico fuerte si existe
        )

        # ----------------------------------
        # 🔥 PRE-SCORE (NUEVO NIVEL)
        # ----------------------------------

        d["pre_score"] = 0

        # ----------------------------------
        # 🔥 BOOST POR POSICIÓN
        # ----------------------------------

        idx = (meta.get("chunk_index") or 0)

        if idx < 5:
            d["pre_score"] += 3

        elif idx > 50:
            d["pre_score"] -= 1

        # ----------------------------------
        # 🔥 INICIO DOCUMENTO = ALTA PRIORIDAD
        # ----------------------------------

        if meta.get("chunk_index", 999) < 10:
            total += 8

        # ----------------------------------
        # 🔥 BOOST POR LONGITUD
        # ----------------------------------

        length = len(cont.split()) if isinstance(cont, str) else 0

        if 80 <= length <= 250:
            d["pre_score"] += 3

        elif length < 40:
            d["pre_score"] -= 2

        # aplicar al total
        total += d["pre_score"]

        # --- boosts ---
        total += boost_frase(pregunta, cont_l) * 0.5
        total += heuristicas_juridicas(cont_l) * 0.3

        # --- clamp final (menos agresivo) ---
        total = max(total, 0)

        # ----------------------------------
        # 🧠 BOOST POR TIPO DE CHUNK (CLAVE)
        # ----------------------------------

        tipo = meta.get("tipo_chunk", "")

        if tipo == "articulo_resolucion":
            total += 10

        elif tipo == "resolucion":
            total += 8

        elif tipo == "considerando":
            total += 5

        elif tipo == "bases_concurso":
            total += 4

        elif tipo == "definicion":
            total += 3

        # ----------------------------------
        # 🧠 INTENCIÓN JURÍDICA
        # ----------------------------------

        if intent == "resolucion":
            if tipo in ["resolucion", "articulo_resolucion"]:
                total += 20
            elif "resuelv" in cont_l:
                total += 25

        elif intent == "objetivo":
            if tipo in ["bases_concurso", "definicion"]:
                total += 12
            if "objetivo" in cont_l:
                total += 20

        elif intent == "fundamento" and tipo == "considerando":
            total += 6

        elif intent == "objetivo" and tipo in ["bases_concurso", "definicion"]:
            total += 5

        # ----------------------------------
        # 🧠 ARTÍCULO ESPECÍFICO
        # ----------------------------------

        m = re.search(r'art[ií]culo\s+(\d+)', preg_l)

        if m:

            art_obj = int(m.group(1))
            art_meta = meta.get("articulo")

            if art_meta:

                m2 = re.search(r'(\d+)', str(art_meta))

                if m2:
                    art_chunk = int(m2.group(1))

                    if art_chunk == art_obj:
                        total += 12
                    elif abs(art_chunk - art_obj) == 1:
                        total += 5

        # ----------------------------------
        # 🧹 PENALIZAR TEXTO MUY LARGO (ruido)
        # ----------------------------------

        if len(cont_l) > 2000:
            total -= 4

        # ----------------------------------
        # 🧹 PENALIZAR OCR BASURA
        # ----------------------------------

        if re.search(r'(tabla|figura|ranking|editorial|impacto|scopus)', cont_l):
            total -= 15

        if sum(c.isdigit() for c in cont_l) > 60:
            total -= 5

        # ----------------------------------
        # 🔥 BOOST ENCABEZADOS LEGALES
        # ----------------------------------

        if re.search(r'\bresuelv[eo]\b', cont_l):
            total += 25

        if re.search(r'\baprueb[ae]\b', cont_l):
            total += 20

        if re.search(r'\bobjetivo(s)?\b', cont_l):
            total += 15

        if re.search(r'\bart[ií]culo\s+\d+', cont_l):
            total += 10

        # ❌ penalizar contexto negativo
        if "no se aprueb" in cont_l:
            total -= 6

        # ----------------------------------
        # BOOSTS ESPECIALES ANID
        # ----------------------------------

        seccion = meta.get("seccion", "")
        inicio = cont[:300].lower()
        preg_benef = detectar_pregunta_beneficiarios(preg_l)

        boost_anid = aplicar_boosts_anid(
            0,  # 👈 importante: partir desde 0
            cont_l,
            inicio,
            seccion,
            intent,
            preg_benef
        )

        # aplicar con peso controlado
        total += boost_anid * 0.35

        # ----------------------------------
        # 🔥 BOOST FINAL (post-normalización real)
        # ----------------------------------

        boost_final = 0

        if tipo == "articulo_resolucion":
            total += 3
        elif tipo == "resolucion":
            total += 2

        total += boost_final

        # cambio clave 🔥
        base_score = float(total)

        boost = 0
        if tipo == "articulo_resolucion":
            boost += 5
        elif tipo == "resolucion":
            boost += 4

        d["score"] = base_score + boost

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
