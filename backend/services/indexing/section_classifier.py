#section_classifier.py
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

    # solo mirar inicio del chunk
    inicio = t[:800]

    # -------------------------------------------------
    # BLOQUEAR ANEXOS CIENTÍFICOS
    # -------------------------------------------------

    if re.search(
        r'JOURNAL|NUMERICAL METHODS|STATISTICAL|INTERNATIONAL JOURNAL|IMPACT FACTOR|WEB OF SCIENCE|SCOPUS|INFORMES ACAD[ÉE]MICOS|PUBLICACIONES',
        inicio
    ):
        return "anexo"

    # -------------------------------------------------
    # DETECCIÓN DIRECTA DE MARCA "SECCION:"
    # -------------------------------------------------

    m = re.search(r'SECCION:\s*([A-Z\s]+)', inicio)

    if m:
        s = m.group(1).strip()

        if "OBJETIVO" in s:
            return "objetivo"

        if "REQUISITO" in s:
            return "requisitos"

        if "POSTUL" in s:
            return "postulacion"

        if "FINANCI" in s:
            return "financiamiento"

        if "EVALU" in s:
            return "evaluacion"

        if "BENEFICIARIO" in s:
            return "beneficiarios"

    # -------------------------------------------------
    # DETECCIÓN ESTRUCTURA NUMERAL ANID
    # -------------------------------------------------

    # OBJETIVO
    if re.search(r'\b1\.\s*(OBJETIVO|FINALIDAD)', inicio):
        return "objetivo"

    if "OBJETIVO DEL CONCURSO" in inicio:
        return "objetivo"

    # REQUISITOS
    if re.search(r'\b2\.\s*(REQUISITOS?)', inicio):
        return "requisitos"

    if "REQUISITOS DE POSTULACION" in inicio:
        return "requisitos"

    # POSTULACION
    if re.search(r'\b3\.\s*(POSTUL|BENEFICI)', inicio):
        return "postulacion"

    if "PUEDEN POSTULAR" in inicio:
        return "postulacion"

    # -------------------------------------------------
    # DETECCIÓN FUERTE DE OBJETIVO
    # -------------------------------------------------

    if re.search(r'\b1\s*\.?\s*(OBJETIVO|FINALIDAD)', inicio):
        return "objetivo"

    if re.search(r'\b2\s*\.?\s*REQUISITOS?', inicio):
        return "requisitos"

    if re.search(r'\b3\s*\.?\s*(POSTUL|BENEFICI)', inicio):
        return "postulacion"

    if re.search(r'\b4\.\s*EVALU', inicio):
        return "evaluacion"

    if re.search(r'\b5\.\s*FINAN', inicio):
        return "financiamiento"

    # -------------------------------------------------
    # TITULOS DE SECCIÓN REALES
    # (solo si aparecen al inicio del bloque)
    # -------------------------------------------------

    patrones = {

        "resolucion": r'^\s*(?:\d+(\.\d+)*\s*)?(RESUELVO|RESOLUCION)',

        "objetivo": r'^\s*(?:\d+(\.\d+)*\s*)?(OBJETIVO(\s+DEL\s+CONCURSO)?|FINALIDAD|PROPOSITO)',

        "requisitos": r'^\s*(?:\d+(\.\d+)*\s*)?(REQUISITOS?|CONDICIONES\s+DE\s+POSTULACION)',

        "postulacion": r'^\s*(?:\d+(\.\d+)*\s*)?(POSTULACION|QUIENES\s+PUEDEN\s+POSTULAR)',

        "evaluacion": r'^\s*(?:\d+(\.\d+)*\s*)?(EVALUACION|CRITERIOS\s+DE\s+EVALUACION)',

        "financiamiento": r'^\s*(?:\d+(\.\d+)*\s*)?(FINANCIAMIENTO|MONTO\s+MAXIMO|SUBSIDIO)',

        "beneficiarios": r'^\s*(?:\d+(\.\d+)*\s*)?BENEFICIARIOS(\s+DEL\s+CONCURSO)?',

        "plazos": r'^\s*(?:\d+(\.\d+)*\s*)?(PLAZOS?|FECHAS?|CALENDARIO)'
    }

    for seccion, patron in patrones.items():

        if re.search(patron, inicio):
            return seccion

    # -------------------------------------------------
    # HEURÍSTICAS SUAVES (fallback)
    # -------------------------------------------------

    if "OBJETIVO DEL CONCURSO" in inicio:
        return "objetivo"

    if "REQUISITOS DE POSTULACION" in inicio:
        return "requisitos"

    if "QUIENES PUEDEN POSTULAR" in inicio:
        return "postulacion"

    if "CRITERIOS DE EVALUACION" in inicio:
        return "evaluacion"

    # evitar clasificar menciones dentro del texto
    if "beneficiarios" in inicio and not re.search(r'^\s*(\d+\.\s*)?beneficiarios', inicio.lower()):
        return "general"

    return "general"
