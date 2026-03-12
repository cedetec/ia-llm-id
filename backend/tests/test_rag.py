import re

def tipo_respuesta(pregunta: str) -> str:
    p = pregunta.lower()

    if "número de resolución" in p:
        return "numerico"

    if "fecha" in p:
        return "fecha"

    return "texto"


def evaluar_respuesta(resp: dict, pregunta: str) -> str:
    texto = (resp.get("respuesta") or "").strip()

    if not texto:
        return "FAIL_VACIO"

    low = texto.lower()

    if "no se encontró" in low:
        return "FAIL_NO_ENCONTRADO"

    if "no fue posible conectarse" in low:
        return "FAIL_ERROR_SISTEMA"

    tipo = tipo_respuesta(pregunta)

    if tipo == "numerico":
        if re.search(r"\b\d{1,6}/\d{2,4}\b", texto):
            return "PASS"
        return "FAIL_FORMATO"

    if tipo == "fecha":
        if re.search(r"\b\d{1,2}[\/\.]\d{1,2}[\/\.]\d{2,4}\b", texto):
            return "PASS"
        return "FAIL_FORMATO"

    # TEXTO
    score = float(resp.get("score_semantico", 0))
    if score < 0.40:
        return "FAIL_BAJA_RELEVANCIA"

    return "PASS"