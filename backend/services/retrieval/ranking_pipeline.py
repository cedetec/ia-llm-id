#ranking_pipeline.py
import re
import unicodedata
import numpy as np

from backend.services.embedding_service import embed_text
from backend.services.retrieval_scoring import score_chunk


# =====================================================
# COSINE SIMILARITY
# =====================================================

def cosine(a, b):

    try:
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)

        if a.size == 0 or b.size == 0:
            return 0.0

        if a.shape != b.shape:
            return 0.0

        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)

        if na == 0 or nb == 0:
            return 0.0

        return float(np.dot(a, b) / (na * nb))

    except Exception:
        return 0.0


# =====================================================
# NORMALIZACIÓN
# =====================================================

def normalizar_txt(txt):

    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)\
        .encode("ascii", "ignore")\
        .decode("ascii")\
        .lower()

    # unir letras separadas por OCR
    txt = re.sub(r'(?<=\b[a-z])\s+(?=[a-z]\b)', '', txt)

    txt = re.sub(r'\s+', ' ', txt)

    return txt


# =====================================================
# RANKING PRINCIPAL
# =====================================================

def rankear_chunks(pregunta, docs, toks, modo_cita=False):

    # -------------------------------------------------
    # EMBEDDING DE PREGUNTA
    # -------------------------------------------------

    try:
        q_emb = embed_text(pregunta, mode="query")
    except Exception:
        q_emb = None

    ranked = []

    # -------------------------------------------------
    # TOKENS SEGUROS
    # -------------------------------------------------

    if not isinstance(toks, (list, tuple, set)):
        toks = []

    safe_toks = [
        t for t in toks
        if isinstance(t, str) and len(t) > 3
    ]

    # -------------------------------------------------
    # DETECTAR INTENCION DE LA PREGUNTA
    # -------------------------------------------------

    preg_l = normalizar_txt(pregunta)

    # -------------------------------------------------
    # DETECTAR MODO CITA
    # -------------------------------------------------

    if any(k in preg_l for k in [
        "cita", "frase textual", "extrae una frase",
        "responde con una frase", "cita textual"
    ]):
        modo_cita = True

    intent = None

    if "resolucion" in preg_l or "res." in preg_l:
        intent = "resolucion"

    elif any(x in preg_l for x in [
        "objetivo",
        "finalidad",
        "proposito",
        "para que es",
        "para que sirve"
    ]):
        intent = "objetivo"

    elif "requisito" in preg_l:
        intent = "requisitos"

    elif any(x in preg_l for x in [
        "que se necesita",
        "condiciones para postular",
        "que se requiere"
    ]):
        intent = "requisitos"

    elif any(x in preg_l for x in [
        "postular",
        "postulacion",
        "postulación",
        "pueden postular",
        "quien puede postular",
        "quienes pueden postular",
        "quien puede participar",
        "quienes pueden participar",
        "participar en el concurso"
    ]):
        intent = "postulacion"

    elif "financiamiento" in preg_l or "monto" in preg_l:
        intent = "financiamiento"

    elif "evaluacion" in preg_l:
        intent = "evaluacion"

    elif "aprueba" in preg_l or "bases" in preg_l:
        intent = "bases"

    if "objetivo" in pregunta.lower():
        safe_toks.append("objetivo")

    if "requisitos" in pregunta.lower():
        safe_toks.append("requisitos")

    if "postular" in pregunta.lower():
        safe_toks.append("postular")

    if not safe_toks:
        safe_toks = [
            t for t in re.findall(r'\w+', pregunta.lower())
            if len(t) > 3
        ]
    # -------------------------------------------------
    # DOCUMENTO EN PREGUNTA
    # -------------------------------------------------

    # DOCUMENTO EN PREGUNTA
    doc_query = re.search(r'([\w\-.]+\.pdf)', pregunta.lower())
    doc_name = doc_query.group(1) if doc_query else None

    # FILTRO POR DOCUMENTO
    if doc_name:
        docs = [
            d for d in docs
            if doc_name in str(d.get("metadata", {}).get("documento", "")).lower()
        ]

    # -------------------------------------------------
    # FRASES CITADAS
    # -------------------------------------------------

    quoted = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    quoted = [normalizar_txt(q) for q in quoted]

    # -------------------------------------------------
    # FILTRO PREVIO POR SECCIÓN (optimización RAG jurídico)
    # -------------------------------------------------

    if intent:

        docs_filtrados = []

        for d in docs:

            sec = str(d.get("metadata", {}).get("seccion", "")).lower()

            if intent == "objetivo" and "objetivo" in sec:
                docs_filtrados.append(d)

            elif intent == "requisitos" and "requisito" in sec:
                docs_filtrados.append(d)

            elif intent == "postulacion" and "postul" in sec:
                docs_filtrados.append(d)

            elif intent == "financiamiento" and "financ" in sec:
                docs_filtrados.append(d)

            elif intent == "evaluacion" and "evalu" in sec:
                docs_filtrados.append(d)

            elif intent == "bases" and (
                "resolucion" in sec or
                "resuelvo" in sec or
                "aprobacion" in sec
            ):
                docs_filtrados.append(d)

        # usar filtrado solo si no queda vacío
        if len(docs_filtrados) > 3:
            docs = docs_filtrados

    # -------------------------------------------------
    # LOOP PRINCIPAL
    # -------------------------------------------------

    for d in docs:

        cont = str(d.get("contenido", ""))
        meta = d.get("metadata", {})
        seccion = str(meta.get("seccion", "")).lower()
        emb = d.get("embedding")

        if not cont:
            continue

        cont_l = normalizar_txt(cont)

        # normalizar OCR separado
        cont_l = re.sub(r'f\s*o\s*n\s*d\s*e\s*c\s*y\s*t', 'fondecyt', cont_l)
        cont_l = re.sub(r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n', 'resolucion', cont_l)
        cont_l = re.sub(r'o\s*b\s*j\s*e\s*t\s*i\s*v\s*o', 'objetivo', cont_l)
        cont_l = re.sub(r'p\s*o\s*s\s*t\s*u\s*l\s*a\s*c\s*i\s*o\s*n', 'postulacion', cont_l)
        cont_l = re.sub(r'r\s*e\s*q\s*u\s*i\s*s\s*i\s*t\s*o\s*s', 'requisitos', cont_l)

        # evitar chunks repetitivos OCR
        if cont_l.count("tomado de razon") > 2:
            continue

        # -------------------------------------------------
        # DESCARTAR TEXTO ADMINISTRATIVO PURO
        # -------------------------------------------------

        if any(x in cont_l for x in [
            "anotese y comuniquese",
            "anótese y comuníquese",
            "direccion nacional",
            "contralor general",
            "oficial de partes",
            "repositorio de archivo institucional"
        ]):
            continue

        # -------------------------------------------------
        # DESCARTAR CHUNKS MUY CORTOS
        # -------------------------------------------------

        if len(cont_l) < 80:
            continue

        # -------------------------------------------------
        # SCORE BASE
        # -------------------------------------------------

        try:

            total = score_chunk(
                cont,
                safe_toks,
                modo_cita=modo_cita
            )

            if isinstance(total, (list, tuple)):
                total = sum(total)

            total = float(total)

            if total > 200:
                total = 200

        except Exception:
            continue

        # -------------------------------------------------
        # PENALIZAR SECCIONES ADMINISTRATIVAS
        # -------------------------------------------------

        if any(x in seccion for x in [
            "resolucion",
            "vistos",
            "considerando"
        ]) and intent in ["objetivo", "requisitos", "postulacion"]:
            total -= 500

        # -------------------------------------------------
        # PENALIZAR CHUNKS DEMASIADO LARGOS
        # -------------------------------------------------

        if len(cont_l) > 4000:
            total -= 200

        # -------------------------------------------------
        # FILTRO DE RELEVANCIA
        # -------------------------------------------------

        if safe_toks:
            hits = sum(1 for t in safe_toks if normalizar_txt(t) in cont_l)
            if hits == 0:
                total -= 15

        # -------------------------------------------------
        # BOOST FRASES CITADAS
        # -------------------------------------------------

        for q in quoted:

            if q and q in cont_l:
                total += 80

        # -------------------------------------------------
        # SCORE SEMÁNTICO
        # -------------------------------------------------

        if (
            q_emb is not None
            and isinstance(q_emb, (list, tuple, np.ndarray))
            and isinstance(emb, (list, tuple, np.ndarray))
            and len(q_emb) > 10
            and len(emb) == len(q_emb)
        ):

            sim = cosine(q_emb, emb)

            if isinstance(sim, (int, float)):
                total += sim * 60

        # -------------------------------------------------
        # MATCH LÉXICO
        # -------------------------------------------------

        for t in safe_toks:

            t_norm = normalizar_txt(t)

            if t_norm in cont_l:

                if modo_cita:
                    total += 12
                else:
                    total += 4

        # -------------------------------------------------
        # BOOST DOCUMENTO
        # -------------------------------------------------

        if doc_name:

            meta_doc = str(meta.get("documento", "")).lower()

            if doc_name in meta_doc:
                total += 200

        # -------------------------------------------------
        # HEURÍSTICAS JURÍDICAS PRINCIPALES
        # -------------------------------------------------

        # resoluciones que aprueban bases

        if "resuelvo" in cont_l and "bases" in cont_l:
            total += 350

        elif "resuelvo" in cont_l:
            total += 180

        if any(x in cont_l for x in [
            "apruebanse las bases concursales",
            "apruebanse las bases",
            "aprueba las bases",
            "aprueban las bases",
            "apruebanse las bases del concurso",
            "aprueban las bases del concurso",
            "apruebanse las bases que regiran",
            "aprueban las bases que regiran",
            "transcripcion oficial integra y fiel",
            "transcripción oficial íntegra y fiel",
        ]):
            total += 420

        if "aprueb" in cont_l and "bases" in cont_l:
            total += 250

        if "bases concursales" in cont_l:
            total += 180

        # resoluciones administrativas

        if "resolucion exenta n" in cont_l:
            total += 260

        elif "resolucion exenta" in cont_l or "resolucion exento" in cont_l:
            total += 220

        elif "resolucion" in cont_l:
            total += 60

        if "vistos:" in cont_l:
            total += 100

        if "considerando:" in cont_l:
            total += 100


        # -------------------------------------------------
        # CONTENIDO DEL CONCURSO
        # -------------------------------------------------

        # objetivo

        if "objetivo del presente concurso" in cont_l:
            total += 380

        elif any(x in cont_l for x in [
            "objetivo del concurso",
            "objetivo general del concurso",
            "el objetivo del concurso es",
            "el objetivo de este concurso es",
        ]):
            total += 900

        elif "objetivo general del concurso" in cont_l:
            total += 700

        elif "objetivo general" in cont_l:
            total += 40


        # requisitos

        if "requisitos de postulacion" in cont_l:
            total += 320

        elif "deberan cumplir los siguientes requisitos" in cont_l:
            total += 380

        elif "deberan cumplir los requisitos" in cont_l:
            total += 350

        elif "requisitos" in cont_l:
            total += 160

        elif "los postulantes deberan cumplir" in cont_l:
            total += 450

        elif "los postulantes deberán cumplir" in cont_l:
            total += 450


        # postulacion

        if "postulacion" in cont_l:
            total += 60

        if "beneficiarios" in cont_l:
            total += 120


        # -------------------------------------------------
        # POSTULACIÓN
        # -------------------------------------------------

        if "postulacion debera ser efectuada por" in cont_l:
            total += 380

        elif "postulacion podra ser efectuada por" in cont_l:
            total += 360

        elif "quienes pueden postular" in cont_l:
            total += 360

        elif "quien puede postular" in cont_l:
            total += 340

        elif "podran postular" in cont_l:
            total += 320

        elif "pueden postular" in cont_l:
            total += 300

        elif "podran participar" in cont_l:
            total += 320

        elif "podrán participar" in cont_l:
            total += 320


        # -------------------------------------------------
        # SECCIONES DETECTADAS
        # -------------------------------------------------

        if "seccion:" in cont_l:
            total += 100

        if "seccion: objetivo del concurso" in cont_l:
            total += 280

        elif "seccion: objetivo general del concurso" in cont_l:
            total += 260

        elif "seccion: objetivo" in cont_l:
            total += 160

        elif "seccion: requisitos" in cont_l:
            total += 160

        elif "seccion: postulacion" in cont_l:
            total += 160

        # -------------------------------------------------
        # BOOST FUERTE POR SECCIÓN
        # -------------------------------------------------

        if intent == "objetivo" and "objetivo" in seccion:
            total += 900

        elif intent == "postulacion" and "postul" in seccion:
            total += 800

        elif intent == "requisitos" and "requisito" in seccion:
            total += 800

        elif intent == "financiamiento" and "financ" in seccion:
            total += 700


        # -------------------------------------------------
        # BOOST SEGÚN INTENCIÓN
        # -------------------------------------------------

        if intent == "resolucion":

            if "resolucion exenta" in cont_l:
                total += 600

            if "resolucion exenta n" in cont_l:
                total += 800

        if intent == "requisitos":

            if "seccion: requisitos" in cont_l:
                total += 600

            if "certificaciones" in cont_l:
                total += 200

        elif intent == "postulacion":

            if "seccion: postulacion" in cont_l:
                total += 420

            if "seccion: financiamiento" in cont_l:
                total -= 200

            if "investigador responsable podra postular" in cont_l:
                total += 380

            if "personas naturales" in cont_l:
                total += 200


        elif intent == "financiamiento":

            if "seccion: financiamiento" in cont_l:
                total += 380

            if "seccion: objetivo" in cont_l:
                total -= 150


        elif intent == "objetivo":

            if "seccion: objetivo del concurso" in cont_l:
                total += 120

            elif "seccion: objetivo general del concurso" in cont_l:
                total += 520

            elif "seccion: objetivo" in cont_l:
                total += 320

            if "objetivo del proyecto" in cont_l:
                total -= 400

            if "seccion: financiamiento" in cont_l:
                total -= 350

            if "seccion: seguimiento" in cont_l:
                total -= 320

            if "seccion: evaluacion" in cont_l:
                total -= 280

            if "objetivo de este concurso" in cont_l:
                total += 700

            if "el objetivo del concurso es" in cont_l:
                total += 750

            if "el objetivo de este concurso es" in cont_l:
                total += 800

            if "objetivo de este concurso es" in cont_l:
                total += 850

            if "este concurso tiene por objetivo" in cont_l:
                total += 900

            if "tiene por objetivo" in cont_l and "concurso" in cont_l:
                total += 850


        # -------------------------------------------------
        # DETECCIÓN DE ESTRUCTURA NUMERAL (BASES ANID)
        # -------------------------------------------------

        if re.search(r'\b\d+\.\d+\b', cont_l):
            total += 40

        if re.search(r'\n\s*\d+\.\s+[a-z]', cont_l):
            total += 25

        if re.search(r'\b\d+\.\d+\s+(certificaciones|requisitos|postul)', cont_l):
            total += 120

        if re.search(r'\b1\.\d+\s+(objetivo|finalidad)', cont_l):
            total += 150

        if re.search(r'\b\d+\.\d+\s+(evaluacion|criterios)', cont_l):
            total += 120

        if re.search(r'\b1\.\s+objetivo', cont_l):
            total += 400

        if re.search(r'\b2\.\s+requisitos', cont_l):
            total += 350

        if re.search(r'\b3\.\s+postul', cont_l):
            total += 300

        if "investigacion" in cont_l and "desarrollo" in cont_l:
            total += 20


        # -------------------------------------------------
        # TEXTO ADMINISTRATIVO
        # -------------------------------------------------

        if any(x in cont_l for x in [
            "oficial de partes",
            "repositorio de archivo",
            "comite de asignacion",
            "anotese y comuniquese",
            "anótese y comuníquese",
            "anotese y comunique",
            "anótese y comunique",
            "direccion nacional",
            "ministerio de educacion",
            "ministerio de educación",
            "contralor general",
            "tómese razón"
        ]):
            total -= 2000

        if "anotese" in cont_l and "comunique" in cont_l:
            total -= 2000

        if "direccion nacional" in cont_l:
            total -= 1500

        if "anotese y comuniquese" in cont_l:
            total -= 2000

        # -------------------------------------------------
        # PENALIZACIONES
        # -------------------------------------------------

        if 200 < len(cont) < 1200:
            total += 12

        if cont.count("cid:") > 5:
            total -= 5

        if not isinstance(total, (int, float)):
            continue

        if np.isnan(total):
            continue

        try:
            total = float(total)
        except Exception:
            continue

        # -------------------------------------------------
        # EXTRAER FRASE CITABLE
        # -------------------------------------------------

        if modo_cita:

            # limpiar OCR frecuente
            cont = re.sub(r'\b[Tt]os\s+', 'Los ', cont)
            cont = re.sub(r'\b[Aa]ción', 'Acción', cont)
            cont = re.sub(r'\b[Ii]strativo', 'Administrativo', cont)

            frases = re.split(r'(?<=[\.\!\?:;])\s+|\n{2,}', cont)

            frases_validas = [
                f.strip() for f in frases
                if 40 < len(f) < 400
            ]

            if frases_validas:

                mejor_frase = frases_validas[0]
                mejor_score = -1

                for f in frases_validas:

                    f = f.strip()

                    # evitar frases muy cortas
                    if len(f.split()) < 6:
                        continue

                    # evitar frases cortadas por OCR
                    if re.match(r'^[a-záéíóúñ]{1,4}\b', f):
                        continue

                    # evitar frases administrativas
                    f_norm = normalizar_txt(f)

                    if any(x in f_norm for x in [
                        "oficial de partes",
                        "repositorio de archivo",
                        "comite de asignacion",
                        "anotese y comuniquese",
                        "anótese y comuníquese",
                        "direccion nacional",
                        "ministerio de educacion"
                    ]):
                        continue

                    score = 0

                    # coincidencia con tokens de pregunta
                    score += sum(
                        1 for t in safe_toks
                        if normalizar_txt(t) in f_norm
                    )

                    # penalizar frases que empiezan mal
                    if f[0].islower():
                        score -= 2

                    # bonus semántico fuerte
                    if "objetivo" in f_norm:
                        score += 5

                    if "requisito" in f_norm:
                        score += 5

                    if "postular" in f_norm:
                        score += 4

                    if "bases" in f_norm:
                        score += 4

                    if "concurso" in f_norm:
                        score += 2

                    if "fondecyt" in f_norm:
                        score += 2

                    if score > mejor_score:
                        mejor_score = score
                        mejor_frase = f

                cont = mejor_frase
    
        ranked.append({
            "score": float(total),
            "contenido": cont,
            "metadata": meta
        })

    # -------------------------------------------------
    # ORDEN FINAL
    # -------------------------------------------------

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return ranked
