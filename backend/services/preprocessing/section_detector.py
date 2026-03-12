# services/preprocessing/section_detector.py

def detectar_seccion_legal(texto: str) -> str:
    t = texto.lower()

    if "objetivo" in t:
        return "objetivo"

    if "postular" in t or "beneficiarios" in t:
        return "postulantes"

    if "requisitos" in t:
        return "requisitos"

    if "evaluación" in t:
        return "evaluacion"

    if "financiamiento" in t and "apruebanse" not in t and "apruebase" not in t:
        return "financiamiento"

    if "resolución exenta" in t:
        return "resolucion"

    return "general"