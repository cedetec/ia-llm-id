from backend.services.consulta_extract_frases import (
    extraer_frase_con_patron,
    recortar_frase_limpia,
)

from backend.services.consulta_utils_text import score_semantico
import re


def manejar_cita(pregunta_low, contexto, pregunta):

    patrones = []

    # resoluciones
    if "resol" in pregunta_low:
        patrones += [
            "resolución",
            "resolucion",
            "rex",
            "resuelvo",
            "resuelve"
        ]

    # aprobación de bases
    if "aprueb" in pregunta_low or "bases" in pregunta_low:
        patrones += [
            "apruebanse",
            "apruebase",
            "aprueba",
            "aprueban",
            "aprueban las bases",
            "apruebanse las bases",
            "bases concursales"
        ]

    # objetivo del concurso
    if "objetivo" in pregunta_low:
        patrones += [
            "objetivo del concurso",
            "objetivo de este concurso",
            "el objetivo del concurso",
            "el presente concurso tiene por objetivo"
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
        for c in re.split(r"\n{2,}", contexto)
        if len(c.strip()) > 80
    ]

    frases = []

    for chunk in chunks:
        for pat in patrones:
            frase = extraer_frase_con_patron(chunk, pat, window=260)
            if frase:
                frases.append(frase)
                break

    frases = list(dict.fromkeys(frases))

    if not frases:
        return None

    # ranking simple por similitud semántica
    mejor = max(
        frases,
        key=lambda f: score_semantico(f, pregunta)
    )

    score_sem = score_semantico(mejor, pregunta)

    return {
        "respuesta": recortar_frase_limpia(mejor),
        "fuente": "RAG (extracción directa)",
        "score_semantico": round(score_sem, 3),
        "score_lexico": round(score_semantico(mejor, pregunta_low), 3),
    }