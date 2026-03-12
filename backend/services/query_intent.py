import re
import unicodedata

def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()

def detectar_seccion_pregunta(pregunta: str) -> str | None:
    p = _normalizar(pregunta)

    # RESOLUCIÓN (más específico primero)
    if re.search(r"\b(resolucion|resuelve|rex|res\.?\s+exenta?)\b", p):
        return "resolucion"

    # EVALUACIÓN
    if re.search(r"\b(evaluacion|criterios?)\b", p):
        return "evaluacion"

    # POSTULANTES
    if re.search(r"\b(quienes pueden|beneficiarios?|postular|postulantes?)\b", p):
        return "postulantes"

    # REQUISITOS
    if re.search(r"\b(requisitos?|documentos?|antecedentes?)\b", p):
        return "requisitos"

    # OBJETIVO
    if re.search(r"\b(objetivo|finalidad|proposito)\b", p):
        return "objetivo"

    return None