# ranking_intent.py
import re
from backend.services.ranking_utils import normalizar_txt


def detectar_intent(preg):

    preg = normalizar_txt(preg)

    if any(x in preg for x in ["resolucion","resuelvo","acto administrativo"]):
        return "resolucion"

    if any(x in preg for x in [
        "objetivo","finalidad","proposito",
        "para que","que busca","que pretende"
    ]):
        return "objetivo"

    if any(x in preg for x in [
        "requisito",
        "que se necesita",
        "condiciones para postular"
    ]):
        return "requisitos"

    if any(x in preg for x in [
        "postular",
        "quien puede postular",
        "beneficiarios"
    ]):
        return "postulacion"

    if any(x in preg for x in [
        "financiamiento",
        "monto",
        "cuanto financia"
    ]):
        return "financiamiento"

    if any(x in preg for x in [
        "evaluacion",
        "criterios de evaluacion"
    ]):
        return "evaluacion"

    if "bases" in preg:
        return "bases"

    return None


def detectar_pregunta_beneficiarios(preg):

    patrones = [
        r'quien(es)? puede(n)? postular',
        r'quien(es)? puede(n)? participar',
        r'quien(es)? son beneficiarios'
    ]

    for p in patrones:
        if re.search(p, preg):
            return True

    return False
