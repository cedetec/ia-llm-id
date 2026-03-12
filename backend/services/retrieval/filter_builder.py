#filter_builder.py
import re
from backend.services.retrieval_text_utils import tokens
from backend.services.retrieval.doc_utils import normalizar_nombre_doc


SECCIONES_MAP = {
    "objetivo": "objetivo",
    "objetivos": "objetivo",

    "requisito": "requisitos",
    "requisitos": "requisitos",

    "postular": "postulacion",
    "postulación": "postulacion",

    "financiamiento": "financiamiento",
    "financiar": "financiamiento",

    "beneficio": "beneficios",
    "beneficios": "beneficios",

    "evaluacion": "evaluacion",
    "evaluación": "evaluacion"
}


def construir_filtro_inicial(pregunta: str, nombre_doc: str | None):

    filtro = {}
    condiciones = []

    # --------------------------------------
    # 1 DOCUMENTO
    # --------------------------------------

    if nombre_doc:

        nombre_doc_norm = normalizar_nombre_doc(nombre_doc)

        condiciones.append({
            "metadata.documento_norm": {
                "$regex": re.escape(nombre_doc_norm),
                "$options": "i"
            }
        })

    # --------------------------------------
    # 2 FRASES ENTRE COMILLAS
    # --------------------------------------

    frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    if frases:

        regex = "|".join(
            re.escape(f.strip())
            for f in frases
            if len(f.strip()) > 3
        )

        if regex:
            condiciones.append({
                "contenido": {
                    "$regex": regex,
                    "$options": "i"
                }
            })

    # --------------------------------------
    # 3 TOKENS
    # --------------------------------------

    toks = tokens(pregunta)

    toks = [
        t for t in toks
        if len(t) > 2
    ][:6]

    if toks:

        regex = "|".join(
            re.escape(t)
            for t in toks
        )

        condiciones.append({
            "contenido": {
                "$regex": regex,
                "$options": "i"
            }
        })

    # --------------------------------------
    # 4 SECCION
    # --------------------------------------

    pregunta_lower = pregunta.lower()

    for palabra, seccion in SECCIONES_MAP.items():

        if palabra in pregunta_lower:

            condiciones.append({
                "metadata.seccion": seccion
            })

            break

    if condiciones:
        filtro["$and"] = condiciones

    return filtro
