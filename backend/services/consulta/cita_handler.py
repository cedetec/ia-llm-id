#cita_handler.py
from backend.services.consulta_extract_frases import (
    extraer_frase_con_patron,
    recortar_frase_limpia,
)

from backend.services.consulta_utils_text import score_semantico
import re


def manejar_cita(pregunta_low, contexto, pregunta):

    patrones = []

    # eliminar anexos científicos
    contexto = re.split(
        r'JOURNAL|SCOPUS|IMPACT FACTOR|PRODUCTIVIDAD CIENTIFICA',
        contexto,
        flags=re.I
    )[0]


    # normalizar OCR común
    contexto = re.sub(r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n', 'resolucion', contexto, flags=re.I)

    contexto = re.sub(
        r'\bresoluci[oó]n\b',
        'resolucion',
        contexto,
        flags=re.I
    )

    # normalizar abreviaturas comunes
    contexto = re.sub(r'\bres\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)
    contexto = re.sub(r'\bresol\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)

    # resoluciones
    if "resol" in pregunta_low:
        patrones += [
            "resolucion",
            "resolucion exenta",
            "resolucion exento",
            "res n",
            "res. n",
            "res.",
            "resol",
            "rex",
            "resuelvo",
            "resuelve",
        ]

    # aprobación de bases
    if "aprueb" in pregunta_low or "bases" in pregunta_low:
        patrones += [
            "apruebase",
            "apruebanse",
            "aprueban las bases",
            "apruebanse las bases",
            "apruebase las bases",
            "apruebanse las bases del concurso",
            "apruebase las bases del concurso",
            "bases del concurso",
            "bases concursales",
            "resuelvo",
            "aprueba las bases del concurso"
        ]

    # objetivo del concurso
    if "objetivo" in pregunta_low:
        patrones += [
            "objetivo del concurso",
            "objetivo de este concurso",
            "el objetivo del concurso",
            "el objetivo de este concurso",
            "este concurso tiene por objetivo",
            "tiene como objetivo",
            "tiene por objetivo",
            "objetivo general del concurso"
        ]

    # requisitos de postulación
    if "postular" in pregunta_low or "requisito" in pregunta_low:
        patrones += [
            "requisitos",
            "requisitos de postulacion",
            "pueden postular",
            "podran postular",
            "quienes pueden postular"
        ]

    chunks = [
        c.strip()
        for c in re.split(r"\n{2,}|--- CHUNK ---", contexto)
        if len(c.strip()) > 80
    ]

    frases = []

    for chunk in chunks:
        for pat in patrones:
            frase = extraer_frase_con_patron(chunk, pat, window=420)
            if frase:
                frases.append(frase)

    frases = list(dict.fromkeys(frases))

    patrones_norm = [p.lower() for p in patrones]

    frases = [
        f for f in frases
        if any(p in f.lower()[:120] for p in patrones_norm)
    ]

    frases = [
        f for f in frases
        if len(f.split()) > 6
    ]

    if not frases:
        return None

    # -------------------------------
    # DEBUG frases candidatas
    # -------------------------------

    print("\nCANDIDATOS CITA:")
    for f in frases[:5]:
        print("-", f[:150])

    # ranking combinado: semántico + presencia de patrón
    def score_total(f):

        s_sem = score_semantico(f, pregunta)

        s_pat = sum(
            1 for p in patrones_norm
            if p in f.lower()
        )

        return s_sem + (s_pat * 0.15)


    mejor = max(frases, key=score_total)

    score_sem = score_semantico(mejor, pregunta)

    score_lex = sum(
        1 for t in pregunta_low.split()
        if t in mejor.lower()
    )

    return {
        "respuesta": recortar_frase_limpia(mejor),
        "fuente": "RAG (extracción directa)",
        "score_semantico": round(score_sem, 3),
        "score_lexico": score_lex,
    }
