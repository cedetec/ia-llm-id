# services/preprocessing/document_classifier.py

def detectar_tipo_documento(texto: str) -> str:
    t = texto.upper()

    if "RESUELVO" in t and "APRUEBA" in t:
        return "resolucion_aprobatoria"

    if "OBJETIVO DEL CONCURSO" in t:
        return "bases"

    return "desconocido"