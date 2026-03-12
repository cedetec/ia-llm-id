# backend/services/retrieval/intent_utils.py

import re

def detectar_seccion_simple(pregunta: str):

    p = pregunta.lower()

    if any(k in p for k in ["objetivo", "finalidad", "propósito", "proposito"]):
        return "objetivo"

    if any(k in p for k in ["requisitos", "requisito"]):
        return "requisitos"

    if any(k in p for k in ["postular", "postulación", "postulacion", "quienes pueden"]):
        return "postulacion"

    if any(k in p for k in ["beneficiarios"]):
        return "beneficiarios"

    if any(k in p for k in ["resolución", "resolucion"]):
        return "resolucion"

    return None


def detectar_modo_cita(pregunta: str) -> bool:

    p = pregunta.lower()

    patrones = [
        "cita",
        "citar",
        "cita textual",
        "frase textual",
        "literal",
        "textualmente",
        "extrae una frase",
        "extrae una cita",
        "responde con una frase",
        "menciona una frase",
        "indica una frase",
        "muestra una frase"
    ]

    return any(x in p for x in patrones)