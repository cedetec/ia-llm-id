# services/indexing/document_classifier.py

import re


def detectar_tipo_documento(nombre_doc: str | None, texto: str | None) -> str:

    n = (nombre_doc or "").lower()
    t = (texto or "").upper()

    # Resolución administrativa
    if (
        "RESUELVO" in t
        or "CONSIDERANDO" in t
        or "VISTO:" in t
        or "RESOLUCIÓN EXENTA" in t
        or "TÓMESE RAZÓN" in t
        or "rex" in n
    ):
        return "resolucion_aprobatoria"

    # Bases
    if (
        "OBJETIVO GENERAL" in t
        or "QUIÉNES PUEDEN POSTULAR" in t
        or "REQUISITOS DE POSTULACIÓN" in t
        or "CRITERIOS DE EVALUACIÓN" in t
        or re.search(r"CAP[IÍ]TULO\s+\d+", t)
        or "bases" in n
    ):
        return "bases"

    return "otro"