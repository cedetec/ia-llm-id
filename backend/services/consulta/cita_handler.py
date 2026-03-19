# cita_handler.py

from backend.services.consulta_extract_frases import (
    extraer_frase_con_patron,
    recortar_frase_limpia,
)

from backend.services.consulta_utils_text import score_semantico

import re


def manejar_cita(pregunta_low, contexto, pregunta):

    # -------------------------------------------------
    # VALIDACIÓN INICIAL (FIX BUG dict.split)
    # -------------------------------------------------

    if isinstance(contexto, dict):
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

    if "resol" in pregunta_low:
        patrones += [
            "resolucion",
            "resolucion exenta",
            "resuelvo",
            "resuelve",
            "rex",
            "res n",
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

            if len(sub) < 60:
                continue

            for pat in patrones:

                if pat in sub.lower():

                    frases.append(sub)
                    break

            # fallback: si no hay patrón, igual guardar algunas
            if not patrones and len(sub) > 100:
                frases.append(sub)

    frases = list(dict.fromkeys(frases))

    if not frases:
        return None

    # -------------------------------------------------
    # FILTROS
    # -------------------------------------------------

    frases = [
        f for f in frases
        if len(f.split()) > 6 and len(f) > 60
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

        s_sem = score_semantico(f, pregunta)

        s_pat = sum(
            1 for p in patrones_norm
            if p in f.lower()
        )

        s_legal = 0

        if "resuelvo" in f.lower():
            s_legal += 0.5

        if "apruebase" in f.lower():
            s_legal += 0.6

        if "objetivo del concurso" in f.lower():
            s_legal += 0.5

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

    score_lex = sum(
        1 for t in pregunta_low.split()
        if t in mejor.lower()
    )

    # -------------------------------------------------
    # LIMPIEZA FINAL
    # -------------------------------------------------

    respuesta = recortar_frase_limpia(mejor)

    respuesta = re.sub(r'\s+', ' ', respuesta)
    respuesta = re.sub(r'([a-z])([A-Z])', r'\1 \2', respuesta)

    return {
        "respuesta": respuesta.strip(),
        "fuente": "RAG (extracción directa)",
        "score_semantico": round(score_sem, 3),
        "score_lexico": score_lex,
    }
