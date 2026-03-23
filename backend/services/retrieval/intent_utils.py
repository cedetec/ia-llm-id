# backend/services/retrieval/intent_utils.py

import re

def detectar_seccion_simple(pregunta: str):

    p = pregunta.lower()

    # -------------------------
    # BENEFICIARIOS
    # -------------------------
    if re.search(r'quien(es)? puede(n)? (postular|participar)', p):
        return "beneficiarios"

    if any(x in p for x in [
        "quienes pueden postular",
        "pueden postular",
        "podran postular",
        "beneficiarios",
        "quien puede postular",
    ]):
        return "beneficiarios"

    # -------------------------
    # OBJETIVO
    # -------------------------
    if any(x in p for x in [
        "objetivo del concurso",
        "objetivo general",
        "finalidad",
        "proposito",
        "propósito",
        "para que es el concurso",
    ]):
        return "objetivo"

    # -------------------------
    # REQUISITOS
    # -------------------------
    if any(x in p for x in [
        "requisitos",
        "requisito",
        "condiciones",
        "que se necesita",
        "como postular",
    ]):
        return "requisito"

    # -------------------------
    # RESOLUCIÓN
    # -------------------------
    if any(x in p for x in [
        "resolucion",
        "resolución",
        "resuelve",
        "rex",
        "numero de resolucion",
        "n°",
    ]):
        return "resolucion"

    # fallback suave
    if "objetivo" in p:
        return "objetivo"
    
    if re.search(r'cual(es)? es|que es', p) and "objetivo" in p:
        return "objetivo"

    return None


def detectar_modo_cita(pregunta: str) -> bool:

    p = pregunta.lower()

    if re.search(r'\b(cita|citar|textual|literal)\b', p):
        return True

    if any(x in p for x in [
        "frase textual",
        "extrae una frase",
        "responde con una frase",
    ]):
        return True

    return False
