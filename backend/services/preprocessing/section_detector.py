import re

def detectar_seccion_legal(texto: str) -> str:
    if not texto:
        return "general"

    t = texto.lower()

    # OBJETIVO
    if re.search(r'\b(objetivo|finalidad|proposito)\b', t):
        return "objetivo"

    # POSTULANTES / BENEFICIARIOS
    if re.search(r'\b(quienes pueden postular|postulantes?|beneficiarios?)\b', t):
        return "postulantes"

    # REQUISITOS
    if re.search(r'\b(requisitos?|condiciones de postulacion)\b', t):
        return "requisitos"

    # FINANCIAMIENTO
    if re.search(r'\b(financiamiento|monto|recursos financiables)\b', t):
        return "financiamiento"

    # DURACION / PLAZOS
    if re.search(r'\b(duracion|plazo|vigencia)\b', t):
        return "duracion"

    # EVALUACION
    if re.search(r'\b(evaluacion|criterios de evaluacion|evaluacion de proyectos)\b', t):
        return "evaluacion"

    # RESOLUCIONES
    if re.search(r'\b(resolucion|resuelvo|apruebase|apruebese)\b', t):
        return "resolucion"

    # CONSIDERANDO / VISTO
    if re.search(r'\b(considerando|visto|vistos)\b', t):
        return "considerando"

    return "general"
