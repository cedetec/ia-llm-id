import re
import unicodedata

PALABRAS_JURIDICAS = [
    "RESOLUCION",
    "REX",
    "OBJETIVO",
    "OBJETIVOS",
    "REQUISITOS",
    "ADMISIBILIDAD",
    "POSTULAR",
    "POSTULANTES",
    "BENEFICIARIOS",
    "FINANCIAMIENTO",
    "EVALUACION",
    "ADJUDICACION",
    "BASES",
    "CONCURSO",
    "FONDECYT",
    "ANID",
]

def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper()

def extraer_keywords_boost(pregunta: str) -> list[str]:
    pregunta_n = _normalizar(pregunta)

    encontrados = [
        palabra
        for palabra in PALABRAS_JURIDICAS
        if re.search(rf"\b{re.escape(palabra)}\b", pregunta_n)
    ]

    # ordenar por aparición real en texto
    encontrados.sort(key=lambda w: pregunta_n.find(w))

    return encontrados[:5]