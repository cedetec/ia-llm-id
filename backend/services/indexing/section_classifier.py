#section_classsifier.py
import re
import unicodedata


def _normalize(t: str) -> str:
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.upper()


def clasificar_seccion(texto: str) -> str:

    if not texto:
        return "general"

    t = _normalize(texto)
    inicio = t[:1200]

    # -------------------------------------------------
    # RESOLUCIONES
    # -------------------------------------------------

    if re.search(r'\bRESUELV[OE]\b|\bRESOLUCION\b', inicio):
        return "resolucion"

    # -------------------------------------------------
    # OBJETIVO
    # -------------------------------------------------

    if re.search(r'\bOBJETIVO\b|\bFINALIDAD\b|\bPROPOSITO\b', inicio):
        return "objetivo"

    # -------------------------------------------------
    # POSTULACIÓN (ANTES QUE REQUISITOS)
    # -------------------------------------------------

    if re.search(
        r'\bPOSTUL|\bPUEDEN\s+POSTULAR|\bPODRAN\s+POSTULAR|\bINVESTIGADOR\s+RESPONSABLE',
        inicio
    ):
        return "postulacion"

    # -------------------------------------------------
    # REQUISITOS
    # -------------------------------------------------

    if re.search(
        r'\bREQUISIT|\bCERTIFIC|\bAUTORIZA|\bCONDICION|\bDEBERAN\s+CUMPLIR',
        inicio
    ):
        return "requisitos"

    # -------------------------------------------------
    # EVALUACIÓN
    # -------------------------------------------------

    if re.search(r'\bEVALUAC', inicio):
        return "evaluacion"

    # -------------------------------------------------
    # FINANCIAMIENTO
    # -------------------------------------------------

    if re.search(
        r'\bFINANCI|\bMONTO|\bSUBSIDIO|\bRECURSOS',
        inicio
    ) and not re.search(
        r'\bCERTIFIC|\bAUTORIZA|\bREQUISIT',
        inicio
    ):
        return "financiamiento"

    # -------------------------------------------------
    # BENEFICIARIOS
    # -------------------------------------------------

    if re.search(r'\bBENEFICI', inicio):
        return "beneficiarios"

    # -------------------------------------------------
    # PLAZOS
    # -------------------------------------------------

    if re.search(r'\bPLAZO\b|\bFECHA\b', inicio):
        return "plazos"

    return "general"