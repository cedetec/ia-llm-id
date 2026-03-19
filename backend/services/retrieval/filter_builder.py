# filter_builder.py

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
    "beneficio": "beneficios",
    "beneficios": "beneficios",
    "evaluacion": "evaluacion",
    "evaluación": "evaluacion"
}


def construir_filtro_inicial(pregunta: str, nombre_doc: str | None):

    condiciones_and = []
    condiciones_or = []

    # --------------------------------------
    # 1️⃣ DOCUMENTO (filtro fuerte)
    # --------------------------------------

    if nombre_doc:

        nombre_doc_norm = normalizar_nombre_doc(nombre_doc)

        condiciones_and.append({
            "$or": [
                {
                    "metadata.documento_norm": {
                        "$regex": re.escape(nombre_doc_norm),
                        "$options": "i"
                    }
                },
                {
                    "metadata.documento": {
                        "$regex": re.escape(nombre_doc_norm),
                        "$options": "i"
                    }
                }
            ]
        })

    # --------------------------------------
    # 2️⃣ FRASES EXACTAS (alta precisión)
    # --------------------------------------

    frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    for f in frases:
        f = f.strip()
        if len(f) > 3:
            condiciones_or.append({
                "contenido": {
                    "$regex": re.escape(f),
                    "$options": "i"
                }
            })

    # --------------------------------------
    # 3️⃣ TOKENS (recall flexible)
    # --------------------------------------

    toks = tokens(pregunta)

    toks = [t for t in toks if len(t) > 3][:6]

    for t in toks:
        condiciones_or.append({
            "contenido": {
                "$regex": re.escape(t),
                "$options": "i"
            }
        })

    # --------------------------------------
    # 4️⃣ SECCIÓN (NO BLOQUEANTE)
    # --------------------------------------

    pregunta_lower = pregunta.lower()

    for palabra, seccion in SECCIONES_MAP.items():

        if palabra in pregunta_lower:

            condiciones_or.append({
                "metadata.seccion": seccion
            })

            break

    # --------------------------------------
    # 🔥 CONSTRUCCIÓN FINAL
    # --------------------------------------

    filtro = {}

    if condiciones_and and condiciones_or:
        filtro = {
            "$and": [
                *condiciones_and,
                {"$or": condiciones_or}
            ]
        }

    elif condiciones_and:
        filtro = {"$and": condiciones_and}

    elif condiciones_or:
        filtro = {"$or": condiciones_or}

    return filtro
