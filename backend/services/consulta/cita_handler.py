# cita_handler.py

from backend.services.consulta_extract_frases import recortar_frase_limpia
from backend.services.consulta_utils_text import score_semantico
from backend.services.retrieval_text_utils import safe_split

import re

def asegurar_string(x):
    if isinstance(x, str):
        return x

    if isinstance(x, dict):
        return x.get("contenido") or x.get("texto") or ""

    if isinstance(x, list):
        partes = []
        for i in x:
            if isinstance(i, dict):
                partes.append(
                    i.get("contenido")
                    or i.get("texto")
                    or ""
                )
            else:
                partes.append(str(i))
        return " ".join(partes)

    return str(x or "")

# =========================================================
# NORMALIZACIÓN
# =========================================================

def normalizar_texto(s):
    if isinstance(s, dict):
        s = s.get("contenido") or s.get("texto") or ""
    elif isinstance(s, list):
        s = " ".join(
            x.get("contenido", "") if isinstance(x, dict) else str(x)
            for x in s
        )
    elif not isinstance(s, str):
        s = str(s or "")

    return (
        s.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def manejar_cita(pregunta_low, contexto, pregunta):

    # -------------------------------------------------
    # NORMALIZAR CONTEXTO (ROBUSTO)
    # -------------------------------------------------

    contexto = asegurar_string(contexto)

    if not contexto.strip():
        return None

    # -------------------------------------------------
    # LIMPIEZA FUERTE CONTEXTO
    # -------------------------------------------------

    contexto = re.split(
        r'JOURNAL|SCOPUS|IMPACT FACTOR|PRODUCTIVIDAD CIENTIFICA',
        contexto,
        flags=re.I
    )[0]

    contexto = re.sub(r'\n+', '\n', contexto)
    contexto = re.sub(r'\s{2,}', ' ', contexto)

    # OCR fixes
    contexto = re.sub(r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n', 'resolucion', contexto, flags=re.I)
    contexto = re.sub(r'\bresoluci[oó]n\b', 'resolucion', contexto, flags=re.I)
    contexto = re.sub(r'\bres\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)

    # -------------------------------------------------
    # INTENCIÓN
    # -------------------------------------------------

    pregunta_norm = normalizar_texto(pregunta_low)

    es_objetivo = "objetivo" in pregunta_norm
    es_requisito = "requisito" in pregunta_norm or "postular" in pregunta_norm
    es_resolucion = any(x in pregunta_norm for x in ["resol", "rex"])
    pide_numero = any(x in pregunta_norm for x in ["numero", "n°", "nº"])

    # -------------------------------------------------
    # DIVISIÓN EN FRASES
    # -------------------------------------------------

    chunks = [
        c.strip()
        for c in re.split(r"\n{2,}|--- CHUNK ---", contexto)
        if len(c.strip()) > 30
    ]

    frases = []

    for chunk in chunks:

        subfrases = re.split(
            r'(?<=[\.\!\?])\s+|\n+|;|:',
            chunk
        )

        for sub in subfrases:

            sub = sub.strip()
            sub_norm = normalizar_texto(sub)

            if len(sub) < 25:
                continue

            # ❌ basura administrativa fuerte
            if any(x in sub_norm for x in [
                "plazo para interponer",
                "recurso de reposicion",
                "seran notificados",
                "carta certificada",
                "dias habiles",
                "sin perjuicio",
                "de conformidad con",
            ]):
                continue

            # ❌ encabezados técnicos
            if re.match(r'^(fiscalia|juridico|sgdoc)\b', sub_norm):
                continue

            # -------------------------------------------------
            # MATCH SEGÚN INTENCIÓN
            # -------------------------------------------------

            match = False

            if es_objetivo:
                if "objetivo" in sub_norm:
                    match = True

            elif es_requisito:
                if any(x in sub_norm for x in ["requisito", "postular", "deben"]):
                    match = True

            elif es_resolucion:
                if any(x in sub_norm for x in ["resolucion", "resuelv", "aprueb"]):
                    match = True

            else:
                match = True  # fallback abierto

            if match:
                frases.append(sub)

    frases = list(dict.fromkeys(frases))

    if not frases:
        return None

    # -------------------------------------------------
    # FILTRO NÚMERO RESOLUCIÓN
    # -------------------------------------------------

    if pide_numero:
        frases = [
            f for f in frases
            if re.search(r'(n[°º]?\s*\d+|\d{2,5}[/\-]\d{2,4})', f, re.I)
        ]

        if not frases:
            return None

    # -------------------------------------------------
    # SCORING
    # -------------------------------------------------

    def score_total(f):

        f_low = normalizar_texto(f)

        # ❌ mismatch fuerte intención
        if es_objetivo and "objetivo" not in f_low:
            return -1000

        if es_requisito and not any(x in f_low for x in ["requisito", "postular"]):
            return -900

        # ❌ basura semántica
        if any(x in f_low for x in [
            "surge la necesidad",
            "se informa",
            "para efectos de",
        ]):
            return -800

        s_sem = score_semantico(f, pregunta)

        s_legal = 0

        # 🔥 objetivo fuerte
        if "objetivo del concurso" in f_low:
            s_legal += 6
        elif "objetivo" in f_low:
            s_legal += 3

        # 🔥 resolución
        if es_resolucion and any(x in f_low for x in ["resolucion", "resuelv"]):
            s_legal += 5

        # 🔥 aprobación bases SOLO si aplica
        if es_resolucion and any(x in f_low for x in ["aprueb"]):
            s_legal += 4

        # 🔥 requisitos
        if es_requisito and any(x in f_low for x in ["requisito", "deben"]):
            s_legal += 4

        # longitud ideal
        length = len(safe_split(f))
        if 12 <= length <= 60:
            s_legal += 2
        elif length < 8:
            s_legal -= 3
        elif length > 120:
            s_legal -= 4

        # boost si contiene número de resolución
        if pide_numero and re.search(r'\d', f):
            s_legal += 3

        # penalizar frases muy largas tipo considerando
        if f_low.startswith("que,"):
            s_legal -= 2

        return (s_sem * 0.5) + s_legal

    mejor = max(frases, key=score_total)

    if score_total(mejor) < 0:
        return None

    # -------------------------------------------------
    # MÉTRICAS
    # -------------------------------------------------

    score_sem = score_semantico(mejor, pregunta)

    texto_mejor = normalizar_texto(mejor)

    tokens_p = [
        t for t in safe_split(normalizar_texto(pregunta_low))
        if len(t) > 2
    ]

    score_lex = sum(1 for t in tokens_p if t in texto_mejor)

    # -------------------------------------------------
    # LIMPIEZA FINAL
    # -------------------------------------------------

    respuesta = recortar_frase_limpia(mejor)

    respuesta = re.sub(r'\s+', ' ', respuesta)
    respuesta = re.sub(r'([a-z])([A-Z])', r'\1 \2', respuesta)
    respuesta = re.sub(r'^[a-zA-Z]{1,3}\s+', '', respuesta)

    return {
        "respuesta": respuesta.strip(),
        "fuente": "RAG (extracción directa)",
        "score_semantico": round(score_sem, 3),
        "score_lexico": score_lex,
    }
