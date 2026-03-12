# services/tipo_documento.py

import re
import unicodedata


MAX_ANALISIS = 10000  # solo analizar encabezado


def _normalizar(texto: str) -> str:
    if not texto:
        return ""

    texto = texto[:MAX_ANALISIS]

    texto = unicodedata.normalize("NFKC", texto)

    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    texto = texto.upper()
    return texto


def detectar_tipo_documento(texto: str) -> str:
    """
    Clasifica el tipo jurídico del documento ANID.
    """

    t = _normalizar(texto)

    # ===============================
    # RESOLUCIÓN APROBATORIA
    # ===============================

    if (
        "RESUELVO" in t and
        re.search(r"APRUEB(A|ASE|AN|ANSE)", t)
    ):
        return "resolucion_aprobatoria"

    if (
        "RESOLUCION EXENTA" in t and
        re.search(r"APRUEB", t)
    ):
        return "resolucion_aprobatoria"

    # ===============================
    # BASES
    # ===============================

    if any(x in t for x in [
        "OBJETIVO GENERAL",
        "OBJETIVO DEL CONCURSO",
        "FINALIDAD DEL CONCURSO",
        "QUIENES PUEDEN POSTULAR",
        "REQUISITOS DE POSTULACION",
        "BASES DEL CONCURSO",
        "CONVOCATORIA"
    ]):
        return "bases"

    # ===============================
    # CALENDARIO
    # ===============================

    if "CALENDARIO" in t and "POSTULACION" in t:
        return "calendario"

    # ===============================
    # ADJUDICACIÓN
    # ===============================

    if re.search(r"ADJUDIC(A|ACION)", t):
        return "adjudicacion"

    return "desconocido"