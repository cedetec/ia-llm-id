# filter_builder.py
import re
from backend.services.retrieval_text_utils import tokens, normalizar
from backend.services.retrieval.doc_utils import normalizar_nombre_doc


def construir_filtro_inicial(pregunta: str, nombre_doc: str | None):

    pregunta_norm = normalizar(pregunta)
    pregunta_low = pregunta.lower()

    # ==================================================
    # 🔥 0️⃣ FILTRO DOCUMENTO (ROBUSTO)
    # ==================================================

    filtro_doc = None

    if nombre_doc:
        nombre_doc_norm = normalizar_nombre_doc(nombre_doc)

        variantes = list(set([
            nombre_doc.lower(),
            nombre_doc_norm,
            nombre_doc.replace("-", " "),
            nombre_doc.replace("-", ""),
            nombre_doc_norm[:6]  # fallback parcial (ej: 5921re)
        ]))

        regexes = [
            {
                "metadata.documento_norm": {
                    "$regex": re.escape(v),
                    "$options": "i"
                }
            }
            for v in variantes if len(v) >= 4
        ] + [
            {
                "metadata.documento": {
                    "$regex": re.escape(v),
                    "$options": "i"
                }
            }
            for v in variantes if len(v) >= 4
        ]

        filtro_doc = {"$or": regexes}

    # ==================================================
    # 🔥 1️⃣ INTENCIÓN FUERTE (RESOLUCIÓN)
    # ==================================================

    if any(x in pregunta_low for x in ["aprueb", "resuelv", "resolucion"]):

        condiciones = [
            {"contenido_norm": {"$regex": "aprueb", "$options": "i"}},
            {"contenido_norm": {"$regex": "resuelv", "$options": "i"}},
            {"contenido_norm": {"$regex": "resolucion", "$options": "i"}},
        ]

        return combinar(filtro_doc, {"$or": condiciones})

    # ==================================================
    # 🔥 2️⃣ NÚMERO DE RESOLUCIÓN
    # ==================================================

    if "numero" in pregunta_low and "resolucion" in pregunta_low:

        condiciones = [
            {"contenido_norm": {"$regex": r"\d{1,5}[/\-]\d{2,4}", "$options": "i"}},
            {"contenido_norm": {"$regex": "n°", "$options": "i"}},
        ]

        return combinar(filtro_doc, {"$or": condiciones})

    # ==================================================
    # 🔥 3️⃣ INTENCIONES SEMÁNTICAS
    # ==================================================

    condiciones_or = []

    if "objetivo" in pregunta_norm:
        condiciones_or.extend([
            {"metadata.seccion": "objetivo"},
            {"contenido_norm": {"$regex": "objetivo", "$options": "i"}},
            {"contenido_norm": {"$regex": "finalidad", "$options": "i"}},
        ])

    if "requisito" in pregunta_norm:
        condiciones_or.extend([
            {"metadata.seccion": "requisitos"},
            {"contenido_norm": {"$regex": "requisito", "$options": "i"}},
        ])

    if "postul" in pregunta_norm or "beneficiario" in pregunta_norm:
        condiciones_or.extend([
            {"metadata.seccion": "postulacion"},
            {"contenido_norm": {"$regex": "postul", "$options": "i"}},
        ])

    # ==================================================
    # 🔥 4️⃣ FRASES EXACTAS (FUERTE)
    # ==================================================

    frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    for f in frases:
        f = f.strip()
        if len(f) > 3:
            fuzzy = ".*".join(map(re.escape, f.split()))
            condiciones_or.append({
                "contenido_norm": {
                    "$regex": fuzzy,
                    "$options": "i"
                }
            })

    # ==================================================
    # 🔥 5️⃣ TOKENS (SOFT - NO BLOQUEAN)
    # ==================================================

    STOPWORDS = {
        "documento", "extrae", "frase", "textual",
        "menciona", "indique", "responde", "cita",
        "aparece", "donde", "parte", "solo"
    }

    toks = tokens(pregunta)
    toks = [t for t in toks if len(t) > 4 and t not in STOPWORDS][:3]

    condiciones_tokens = [
        {
            "contenido_norm": {
                "$regex": re.escape(t),
                "$options": "i"
            }
        }
        for t in toks
    ]

    # ==================================================
    # 🔥 6️⃣ CONSTRUCCIÓN FINAL (CLAVE)
    # ==================================================

    bloques = []

    if filtro_doc:
        bloques.append(filtro_doc)

    if condiciones_or:
        bloques.append({"$or": condiciones_or})

    # 🔥 TOKENS COMO BOOST (NO FILTRO DURO)
    if condiciones_tokens:
        bloques.append({"$or": condiciones_tokens})

    if bloques:
        return {"$and": bloques}

    return {}


# ==================================================
# 🔥 HELPER
# ==================================================

def combinar(filtro_doc, base):
    if filtro_doc:
        return {"$and": [filtro_doc, base]}
    return base
