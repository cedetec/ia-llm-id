# cita_handler.py

from backend.services.consulta_extract_frases import (
    extraer_frase_con_patron,
    recortar_frase_limpia,
)

from backend.services.consulta_utils_text import score_semantico
from backend.services.retrieval_text_utils import safe_split

import re

def normalizar_texto(s):
    return (
        s.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

def manejar_cita(pregunta_low, contexto, pregunta):

    # -------------------------------------------------
    # VALIDACIÓN INICIAL (FIX BUG dict.split)
    # -------------------------------------------------

    # 🔥 NORMALIZACIÓN GLOBAL (FIX REAL)

    print(">>> ENTRANDO A MANEJAR_CITA")
    print(">>> CONTEXTO LENGTH:", len(contexto) if isinstance(contexto, str) else type(contexto))

    if isinstance(contexto, list):
        partes = []
        for d in contexto:
            if isinstance(d, dict):
                val = d.get("contenido") or d.get("texto")
                if isinstance(val, str):
                    partes.append(val)
            elif isinstance(d, str):
                partes.append(d)
        contexto = " ".join(partes)

    elif isinstance(contexto, dict):
        contexto = (
            contexto.get("contenido")
            or contexto.get("texto")
            or ""
        )

    if not isinstance(contexto, str) or not contexto.strip():
        return None

    patrones = []

    # -------------------------------------------------
    # LIMPIEZA CONTEXTO (OCR + ruido científico)
    # -------------------------------------------------

    contexto = re.split(
        r'JOURNAL|SCOPUS|IMPACT FACTOR|PRODUCTIVIDAD CIENTIFICA',
        contexto,
        flags=re.I
    )[0]

    # normalización OCR
    contexto = re.sub(
        r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n',
        'resolucion',
        contexto,
        flags=re.I
    )

    contexto = re.sub(r'\bresoluci[oó]n\b', 'resolucion', contexto, flags=re.I)

    # abreviaturas
    contexto = re.sub(r'\bres\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)
    contexto = re.sub(r'\bresol\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)

    # limpieza general
    contexto = re.sub(r'\n+', '\n', contexto)
    contexto = re.sub(r'\s{2,}', ' ', contexto)

    # -------------------------------------------------
    # PATRONES SEGÚN INTENCIÓN
    # -------------------------------------------------

    if "resol" in normalizar_texto(pregunta_low):
        patrones += [
            "resolucion",
            "resolución",
            "resolucion exenta",
            "resolución exenta",
            "resuelvo",
            "resuelve",
            "rex",
            "res n",
            "res.",
            "resol.",
            "resolución exenta",
        ]

    if "aprueb" in pregunta_low or "bases" in pregunta_low:
        patrones += [
            "apruebase",
            "apruebanse",
            "aprueba",
            "aprueban",
            "se aprueban",
            "aprueban las bases",
            "bases del concurso",
            "bases concursales",
        ]

    if "objetivo" in pregunta_low:
        patrones += [
            "objetivo del concurso",
            "objetivo general",
            "tiene por objetivo",
            "tiene como objetivo",
        ]

    if "postular" in pregunta_low or "requisito" in pregunta_low:
        patrones += [
            "requisitos",
            "requisitos de postulacion",
            "pueden postular",
            "podran postular",
            "investigador responsable",
            "beneficiario",
            "persona natural",
        ]

    patrones_norm = [p.lower() for p in patrones]

    # -------------------------------------------------
    # DIVIDIR CONTEXTO (MEJORADO)
    # -------------------------------------------------

    chunks = [
        c.strip()
        for c in re.split(r"\n{2,}|--- CHUNK ---", contexto)
        if len(c.strip()) > 60
    ]

    frases = []

    # -------------------------------------------------
    # EXTRACCIÓN DE FRASES
    # -------------------------------------------------

    for chunk in chunks:

        # split más inteligente
        subfrases = re.split(
            r'(?<=[\.\!\?])\s+|\n+|;|:|,\s+(?=[A-Z])',
            chunk
        )

        for sub in subfrases:

            sub = sub.strip()

            sub_norm = normalizar_texto(sub)

            if any(normalizar_texto(p) in sub_norm for p in patrones):

                if len(sub) < 40:   # 🔥 mucho más flexible
                    continue

                frases.append(sub)

            # fallback: si no hay patrón, igual guardar algunas
            if len(frases) < 3 and len(sub) > 80:
                frases.append(sub)

    frases = list(dict.fromkeys(frases))

    if not frases:
        return None

    # -------------------------------------------------
    # FILTROS
    # -------------------------------------------------

    frases = [
        f for f in frases
        if isinstance(f, str) and len(safe_split(f)) > 4 and len(f) > 40
    ]

    if not frases:
        return None

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    print("\nCANDIDATOS CITA:")
    for f in frases[:5]:
        print("-", f[:150])

    # -------------------------------------------------
    # SCORING MEJORADO
    # -------------------------------------------------

    def score_total(f):

        f_low = normalizar_texto(f) if isinstance(f, str) else ""

        s_sem = score_semantico(f, pregunta)

        s_pat = sum(
            1 for p in patrones_norm
            if p in f_low
        )

        s_legal = 0

        if "resuelvo" in f_low:
            s_legal += 0.5

        if "apruebase" in f_low:
            s_legal += 0.6

        if "objetivo del concurso" in f_low:
            s_legal += 0.5

        if "podran postular" in f_low or "pueden postular" in f_low:
            s_legal += 0.7

        if any(x in f_low for x in [
            "aprueba bases",
            "aprueban las bases",
            "apruebase",
            "apruebanse"
        ]):
            s_legal += 5.0  # 🔥 dominante

        s_len = min(len(f) / 400, 1)

        return (s_sem * 0.5) + (s_pat * 0.3) + (s_len * 0.1) + s_legal

    mejor = max(frases, key=score_total)

    # -------------------------------------------------
    # FALLBACK (CLAVE PARA TESIS)
    # -------------------------------------------------

    if score_total(mejor) < 0.15:
        mejor = frases[0]

    # -------------------------------------------------
    # MÉTRICAS
    # -------------------------------------------------

    score_sem = score_semantico(mejor, pregunta)

    texto_mejor = mejor.lower() if isinstance(mejor, str) else ""

    score_lex = sum(
        1 for t in safe_split(pregunta_low)
        if t and t in texto_mejor
    )

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
