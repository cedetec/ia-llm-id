import unicodedata

def normalizar_basico(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.lower()

import re

def clasificar_documento_avanzado(texto: str) -> str:
    t = normalizar_basico(texto or "")

    reglas = {
        "resolucion_aprobacion": [
            r"resolucion\s+exent[ao]",
            r"t[oó]mese\s+raz[oó]n",
            r"contralor\s+general",
            r"aprueb[aean]\s+las?\s+bases"
        ],
        "bases_concurso": [
            r"bases\s+del\s+concurso",
            r"objetivo\s+del\s+concurso",
            r"requisitos?\s+de\s+postulacion"
        ],
        "convenio": [
            r"convenio\s+de\s+financiamiento",
            r"las\s+partes\s+acuerdan"
        ],
        "anexo": [
            r"\banexo\b",
            r"tabla\s+de\s+evaluacion"
        ]
    }

    scores = {}

    for tipo, patrones in reglas.items():
        score = 0
        for p in patrones:
            if re.search(p, t):
                score += 1
        if score > 0:
            scores[tipo] = score

    if not scores:
        return "desconocido"

    # devolver el tipo con mayor score
    return max(scores, key=scores.get)
