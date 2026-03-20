import re
from services.retrieval_text_utils import tokens, normalizar
from services.retrieval.doc_utils import normalizar_nombre_doc


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

    pregunta_norm = normalizar(pregunta)
    pregunta_low = pregunta.lower()

    # ==================================================
    # 🔥 0️⃣ FILTRO DOCUMENTO BASE
    # ==================================================

    filtro_doc = None

    if nombre_doc:
        nombre_doc_norm = normalizar_nombre_doc(nombre_doc)

        filtro_doc = {
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
        }

    # ==================================================
    # 🔥 1️⃣ INTENCIÓN: APROBACIÓN / RESOLUCIÓN (EARLY RETURN)
    # ==================================================

    if "aprueb" in pregunta_low or "resuelve" in pregunta_low:

        condiciones = [
            {"contenido_norm": {"$regex": "aprueb", "$options": "i"}},
            {"contenido_norm": {"$regex": "apruebase", "$options": "i"}},
            {"contenido_norm": {"$regex": "resuelve", "$options": "i"}},
            {"contenido_norm": {"$regex": "resolucion", "$options": "i"}},
        ]

        if filtro_doc:
            return {"$and": [filtro_doc, {"$or": condiciones}]}

        return {"$or": condiciones}

    # ==================================================
    # 🔥 2️⃣ INTENCIÓN: NÚMERO DE RESOLUCIÓN
    # ==================================================

    if "resolucion" in pregunta_low and "numero" in pregunta_low:

        condiciones = [
            {"contenido_norm": {"$regex": r"\d{1,5}[/\-]\d{2,4}", "$options": "i"}},
            {"contenido_norm": {"$regex": "n°", "$options": "i"}},
            {"contenido_norm": {"$regex": "resolucion", "$options": "i"}},
        ]

        if filtro_doc:
            return {"$and": [filtro_doc, {"$or": condiciones}]}

        return {"$or": condiciones}

    # ==================================================
    # 🔥 3️⃣ INTENCIONES SEMÁNTICAS (SIN EARLY RETURN)
    # ==================================================

    condiciones_or = []

    if "objetivo" in pregunta_norm:
        condiciones_or.extend([
            {"contenido_norm": {"$regex": "objetivo", "$options": "i"}},
            {"contenido_norm": {"$regex": "finalidad", "$options": "i"}},
            {"metadata.seccion": "objetivo"},
        ])

    elif "requisito" in pregunta_norm:
        condiciones_or.extend([
            {"contenido_norm": {"$regex": "requisito", "$options": "i"}},
            {"contenido_norm": {"$regex": "debe", "$options": "i"}},
            {"metadata.seccion": "requisitos"},
        ])

    elif "postul" in pregunta_norm or "beneficiario" in pregunta_norm:
        condiciones_or.extend([
            {"contenido_norm": {"$regex": "postul", "$options": "i"}},
            {"contenido_norm": {"$regex": "beneficiario", "$options": "i"}},
            {"metadata.seccion": "postulacion"},
        ])

    # ==================================================
    # 🔥 4️⃣ FRASES EXACTAS (ALTA PRECISIÓN)
    # ==================================================

    frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    for f in frases:
        f = f.strip()
        if len(f) > 3:
            condiciones_or.append({
                "contenido_norm": {
                    "$regex": re.escape(f),
                    "$options": "i"
                }
            })

    # ==================================================
    # 🔥 5️⃣ TOKENS (SOLO SI NO HAY NADA)
    # ==================================================

    if not condiciones_or:

        toks = tokens(pregunta)
        toks = [t for t in toks if len(t) > 4][:5]

        for t in toks:
            condiciones_or.append({
                "contenido_norm": {
                    "$regex": re.escape(t),
                    "$options": "i"
                }
            })

    # ==================================================
    # 🔥 6️⃣ CONSTRUCCIÓN FINAL
    # ==================================================

    if filtro_doc and condiciones_or:
        return {
            "$and": [
                filtro_doc,
                {"$or": condiciones_or}
            ]
        }

    elif filtro_doc:
        return filtro_doc

    elif condiciones_or:
        return {"$or": condiciones_or}

    return {}
