#preprocess_service.py

from database.mongo import clean_collection
import re


def preprocesar_documentos(doc=None):

    procesados = 0

    query = {"documento": doc.lower()} if doc else {}

    cursor = clean_collection.find(query)

    for row in cursor:

        texto = row.get("fragmento")

        if not texto:
            continue

        texto = texto.strip()

        # normalizar espacios
        texto = re.sub(r'\s+', ' ', texto)

        # limpieza básica
        texto = texto.replace(" ,", ",")
        texto = texto.replace(" .", ".")
        texto = texto.replace(" :", ":")

        clean_collection.update_one(
            {"_id": row["_id"]},
            {
                "$set": {
                    "fragmento": texto,
                    "preprocesado": True
                }
            }
        )

        procesados += 1

    return {
        "fragmentos_preprocesados": procesados
    }
