#ranking_pipeline.py
import re
import unicodedata
import numpy as np

from backend.services.embedding_service import embed_text
from backend.services.retrieval_scoring import score_chunk


# =====================================================
# UTILIDADES
# =====================================================

def cosine(a, b):
    try:
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)

        if a.shape != b.shape:
            return 0.0

        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)

        if na == 0 or nb == 0:
            return 0.0

        return float(np.dot(a, b) / (na * nb))
    except Exception:
        return 0.0


def normalizar_txt(txt):

    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)\
        .encode("ascii", "ignore")\
        .decode("ascii")\
        .lower()

    txt = re.sub(r'(?<=\b[a-z])\s+(?=[a-z]\b)', '', txt)
    txt = re.sub(r'\s+', ' ', txt)

    return txt


# =====================================================
# DETECCIÓN DE INTENT
# =====================================================

def detectar_intent(preg):

    if "resolucion" in preg:
        return "resolucion"

    if "objetivo" in preg or "finalidad" in preg:
        return "objetivo"

    if "requisito" in preg:
        return "requisitos"

    if "postular" in preg or "postulacion" in preg:
        return "postulacion"

    if "financiamiento" in preg or "monto" in preg:
        return "financiamiento"

    if "evaluacion" in preg:
        return "evaluacion"

    if "bases" in preg or "aprueba" in preg:
        return "bases"

    return None


# =====================================================
# HEURÍSTICAS JURÍDICAS
# =====================================================

def heuristicas_juridicas(texto):

    score = 0

    if "resuelvo" in texto and "bases" in texto:
        score += 350

    if "aprueb" in texto and "bases" in texto:
        score += 500

    if "bases concursales" in texto:
        score += 180

    if "resolucion exenta" in texto:
        score += 220

    if "objetivo del concurso" in texto:
        score += 850

    if "objetivo general del concurso" in texto:
        score += 900

    if "requisitos de postulacion" in texto:
        score += 320

    if "pueden postular" in texto:
        score += 300

    if "quienes pueden postular" in texto:
        score += 360

    if "apruebanse las bases" in texto:
        score += 2000

    if "apruebase las bases" in texto:
        score += 1500

    if "apruebanse las bases del concurso" in texto:
        score += 1800

    return score


# =====================================================
# FILTRO ADMINISTRATIVO
# =====================================================

def es_texto_administrativo(texto):

    return any(x in texto for x in [
        "anotese y comuniquese",
        "contralor general",
        "oficial de partes",
        "repositorio de archivo",
        "direccion nacional"
    ])


# =====================================================
# RANKING PRINCIPAL
# =====================================================

def rankear_chunks(pregunta, docs, toks, modo_cita=False):

    doc_query = re.search(r'([\w\-.]+\.pdf)', pregunta.lower())
    doc_name = doc_query.group(1) if doc_query else None

    preg_l = normalizar_txt(pregunta)

    intent = detectar_intent(preg_l)

    try:
        q_emb = embed_text(pregunta, mode="query")
    except Exception:
        q_emb = None

    safe_toks = [t for t in toks if isinstance(t, str) and len(t) > 3]

    ranked = []

    for d in docs:

        cont = str(d.get("contenido", ""))
        meta = d.get("metadata", {})
        seccion = str(meta.get("seccion", "")).lower()

        # normalizar variantes
        if "resol" in seccion:
            seccion = "resolucion"

        # bloquear anexos desde metadata
        if meta.get("seccion") == "anexo":
            continue

        emb = d.get("embedding")

        if not cont:
            continue

        cont_l = normalizar_txt(cont)

        # -----------------------------------------
        # cortar anexos científicos dentro del chunk
        # -----------------------------------------

        cont_l = re.split(
            r'journal|scopus|impact\s*factor|web\s*of\s*science|productividad\s*cientifica',
            cont_l,
            flags=re.I
        )[0]

        # ------------------------------------
        # detectar sección si viene en el texto
        # ------------------------------------

        if "seccion:" in cont_l:

            if "objetivo" in cont_l[:120]:
                meta["seccion"] = "objetivo"

            elif "requisitos" in cont_l[:120]:
                meta["seccion"] = "requisitos"

            elif "postul" in cont_l[:120]:
                meta["seccion"] = "postulacion"

            elif "evaluacion" in cont_l[:120]:
                meta["seccion"] = "evaluacion"

            elif "financ" in cont_l[:120]:
                meta["seccion"] = "financiamiento"

            elif "beneficiarios" in cont_l[:120]:
                meta["seccion"] = "beneficiarios"

        if es_texto_administrativo(cont_l):
            continue

        # ------------------------------------
        # detectar secciones numeradas ANID
        # ------------------------------------

        if re.search(r'\b1\s*[\.\-]\s*objetivo', cont_l):
            meta["seccion"] = "objetivo"

        elif re.search(r'\b2\s*[\.\-]\s*requisitos', cont_l):
            meta["seccion"] = "requisitos"

        elif re.search(r'\b3\s*[\.\-]\s*(postul|benefici)', cont_l):
            meta["seccion"] = "postulacion"

        elif re.search(r'\b3\s*(quienes\s+pueden\s+postular)', cont_l):
            meta["seccion"] = "postulacion"

        elif re.search(r'\b4\s*[\.\-]\s*evaluacion', cont_l):
            meta["seccion"] = "evaluacion"

        # bloquear anexos detectados en indexación
        if meta.get("seccion") == "anexo_evaluacion":
            continue

        # -------------------------------------------------
        # FILTRO DE ANEXOS CIENTÍFICOS (FONDECYT)
        # -------------------------------------------------

        if any(x in cont_l for x in [
            "journal",
            "statistical",
            "probability",
            "mathematical",
            "numerical",
            "annals",
            "advances in",
            "applied mathematics",
            "computational",
            "impact factor",
            "web of science",
            "scopus",
            "jcr",
            "quartile",
            "revista",
            "publicaciones informadas",
            "productividad cientifica",
            "listado de revistas",
        ]):
            continue

        # -------------------------------------------------
        # FILTRO DOMINIO ANID
        # -------------------------------------------------

        if not any(x in cont_l for x in [
            "concurso",
            "postular",
            "postulacion",
            "bases",
            "financiamiento",
            "proyecto",
            "institucion patrocinante",
            "investigador",
            "beneficiarios",
            "requisitos",
            "evaluacion",
            "anid",
            "fondecyt",
            "investigador responsable",
            "objetivo",
            "aprueba",
            "aprueban",
            "finalidad",
            "proposito",
            "convocatoria",
            "investigacion",
            "centro",
        ]):
            continue

        # ------------------------------------
        # filtrar OCR basura
        # ------------------------------------

        if len(set(cont_l.split())) < 6:
            continue

        # ---------------- SCORE BASE ----------------

        try:
            total = float(score_chunk(cont, safe_toks, modo_cita=modo_cita))
        except Exception:
            continue

        # ---------------- SEMÁNTICO ----------------

        if q_emb is not None and isinstance(emb, (list, tuple, np.ndarray)):
            sim = cosine(q_emb, emb)
            total += sim * 120

        # ---------------- LÉXICO ----------------

        for t in safe_toks:
            if normalizar_txt(t) in cont_l:
                total += 4

        # ---------------- HEURÍSTICAS ----------------

        total += heuristicas_juridicas(cont_l)

        # -------------------------------------------------
        # BOOST POR PROXIMIDAD / TITULOS SEGÚN INTENT
        # -------------------------------------------------

        inicio = cont_l[:180]

        # -------------------------------------------------
        # BOOST POR ENCABEZADOS REALES
        # -------------------------------------------------

        if re.search(r'\b1\s*\.?\s*(objetivo|finalidad)', cont_l):
            total += 4000

        if re.search(r'\b2\s*\.?\s*(requisitos?)', cont_l):
            total += 3500

        if re.search(r'\b3\s*\.?\s*(postul|benefici)', cont_l):
            total += 3200

        if re.search(r'\b4\s*\.?\s*(evaluacion)', cont_l):
            total += 3000

        if re.search(r'\b5\s*\.?\s*(financ)', cont_l):
            total += 2800

        # -------------------------------------------------
        # OBJETIVO
        # -------------------------------------------------

        if intent == "objetivo":

            if "objetivo del concurso" in inicio or "objetivo general del concurso" in inicio:
                total += 2200

            if "objetivo del concurso" in cont_l:
                total += 2000

            if re.search(r'\b1\.\s*(objetivo|finalidad|proposito)', cont_l):
                total += 2000

            if cont_l.startswith("objetivo"):
                total += 1200

            if "tiene por objetivo" in cont_l:
                total += 1000

            if "objetivo" in seccion:
                total += 2800
            else:
                total -= 700


        # -------------------------------------------------
        # REQUISITOS
        # -------------------------------------------------

        elif intent == "requisitos":

            if "requisitos de postulacion" in inicio:
                total += 2000

            if re.search(r'\b2\.\s*(requisitos?)', cont_l):
                total += 1900

            if re.search(r'^\s*requisitos', cont_l):
                total += 1200

            if "requisito" in seccion:
                total += 2500
            else:
                total -= 600


        # -------------------------------------------------
        # POSTULACIÓN
        # -------------------------------------------------

        elif intent == "postulacion":

            # penalizar texto administrativo de postulacion
            if re.search(r'notificara|notificacion|resultado|carta certificada|plataforma en linea', cont_l):
                total -= 2000

            if "pueden postular" in inicio or "quienes pueden postular" in inicio:
                total += 2000

            # variantes reales de ANID
            if re.search(r'\b(podran\s+postular|podra\s+postular|podran\s+participar|podran\s+presentar)\b', cont_l):
                total += 2500

            if "podran postular al concurso" in cont_l:
                total += 2800

            if "podran postular" in inicio:
                total += 2800

            if re.search(r'\b3\.\s*(postul|benefici)', cont_l):
                total += 1800

            if re.search(r'^\s*(postulacion|postulantes)', cont_l):
                total += 1100

            # boost fuerte para quienes pueden postular
            if re.search(r'quienes pueden postular', cont_l):
                total += 4000

            if re.search(r'\bpodran\s+postular\b', cont_l):
                total += 3800

            if re.search(r'\bpodran\s+participar\b', cont_l):
                total += 3500

            if re.search(r'\bpodran\s+presentar\b', cont_l):
                total += 3200

            if "postul" in seccion:
                total += 2400
            else:
                total -= 500


        # -------------------------------------------------
        # BASES / RESOLUCIONES
        # -------------------------------------------------

        elif intent in ["bases", "resolucion"]:

            if re.search(r'\b(resuelvo|apruebase|apruebanse|aprueba[n]?|se\s+aprueba[n]?)\b', cont_l):
                total += 4200

            if re.search(r'\bapruebanse\s+las\s+bases\s+del\s+concurso', cont_l):
                total += 4500

            if "aprueba las bases" in cont_l or "aprueban las bases" in cont_l:
                total += 4500

            if "apruebanse las bases del concurso" in cont_l:
                total += 4500

            if "bases del concurso" in cont_l:
                total += 900

            if "bases concursales" in cont_l:
                total += 700

            if seccion in ["beneficiarios", "evaluacion"]:
                total -= 900

        # -------------------------------------------------
        # BOOST RESOLUCIONES
        # -------------------------------------------------

        if intent == "resolucion":

            if "resolucion exenta" in cont_l:
                total += 1200

            if "resolucion n" in cont_l:
                total += 900

            if "resuelvo" in cont_l:
                total += 800

        # -----------------------------------------
        # SECCIONES JURIDICAS IMPORTANTES
        # -----------------------------------------

        if "resolucion" in seccion:
            total += 1200

        if "aprobacion" in seccion:
            total += 1100

        if "bases" in seccion:
            total += 900

        if "convocatoria" in seccion:
            total += 700

        # ---------------- BOOST DOCUMENTO ----------------

        if doc_name:

            meta_doc = str(meta.get("documento", "")).lower()

            if doc_name.lower() in meta_doc:
                total += 400

        # ---------------- FILTROS ----------------

        if len(cont_l) < 80:
            continue

        if len(cont_l) > 4000:
            total -= 200

        # ---------------- RESULTADO ----------------

        DEBUG_RANK = True

        if DEBUG_RANK:
            print("DEBUG CHUNK SCORE:", total)
            print(cont[:120])
            print("----")

        # evitar scores negativos extremos
        if total < -200:
            continue

        ranked.append({
            "score": float(total),
            "contenido": cont,
            "metadata": meta
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    # -------------------------------------------------
    # LIMITAR DOMINANCIA DE DOCUMENTOS
    # -------------------------------------------------

    seen_docs = {}
    filtered = []

    MAX_DOC_CHUNKS = 4   # antes 8

    for r in ranked:

        doc = r["metadata"].get("documento", "unknown")

        seen_docs.setdefault(doc, 0)

        if seen_docs[doc] < MAX_DOC_CHUNKS:

            filtered.append(r)
            seen_docs[doc] += 1

    ranked = filtered

    return ranked[:12]
