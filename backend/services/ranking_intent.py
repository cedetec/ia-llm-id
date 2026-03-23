# ranking_intent.py
import re
from backend.services.retrieval_text_utils import normalizar


def detectar_intent(preg):

    preg = normalizar(preg)

    # -------------------------------------------------
    # 🔥 PRIORIDAD 1: RESOLUCIONES (muy distintivo)
    # -------------------------------------------------

    if re.search(r'\b(resolucion|resuelv|rex|acto administrativo)\b', preg):
        return "resolucion"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 2: OBJETIVO
    # -------------------------------------------------

    if re.search(
        r'\b(objetivo|finalidad|proposito|para que|que busca|que pretende)\b',
        preg
    ):
        return "objetivo"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 3: REQUISITOS
    # -------------------------------------------------

    if re.search(
        r'\b(requisito(s)?|condiciones|que se necesita|que debo|que debo cumplir)\b',
        preg
    ):
        return "requisitos"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 4: POSTULACIÓN / BENEFICIARIOS
    # -------------------------------------------------

    if re.search(
        r'\b(postular|postulacion|postulante(s)?|beneficiario(s)?|quien(es)? puede(n)? postular|quien(es)? puede(n)? participar)\b',
        preg
    ):
        return "postulacion"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 5: FINANCIAMIENTO
    # -------------------------------------------------

    if re.search(
        r'\b(financiamiento|financia|monto|recursos|cuanto financia|cuanto dinero)\b',
        preg
    ):
        return "financiamiento"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 6: EVALUACIÓN
    # -------------------------------------------------

    if re.search(
        r'\b(evaluacion|criterios de evaluacion|como se evalua)\b',
        preg
    ):
        return "evaluacion"

    # -------------------------------------------------
    # 🔥 PRIORIDAD 7: BASES
    # -------------------------------------------------

    if re.search(r'\bbases\b', preg):
        return "bases"

    return None


def detectar_pregunta_beneficiarios(preg):

    preg = normalizar(preg)

    patrones = [
        r'quien(es)? puede(n)? postular',
        r'quien(es)? puede(n)? participar',
        r'quien(es)? son beneficiarios',
        r'a quien(es)? va dirigido',
        r'quienes participan'
    ]

    for p in patrones:
        if re.search(p, preg):
            return True

    return False
