from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
print("📡 Conectando a MongoDB en:", MONGO_URI)

client = MongoClient(MONGO_URI)
db = client["asistenteID"]


def limpiar_regex(texto: str) -> str:
    """
    Limpia caracteres que rompen las expresiones regulares.
    Evita errores como 'nothing to repeat' en búsquedas de MongoDB.
    """
    if not isinstance(texto, str):
        return ""
    texto = texto.strip()
    # escapamos símbolos especiales de regex: * + ? [ ] ( ) { } | ^
    return re.escape(texto)


def buscar_fondos_relevantes(pregunta: str, limite: int = 10):
    """
    Busca registros relevantes en la colección fondos_historicos.
    Ahora:
    - limpia la pregunta antes de usarla como regex
    - evita errores por campos None
    - usa matching difuso más flexible
    """
    try:
        if not pregunta:
            return []

        tokens = [t for t in pregunta.split() if len(t) > 2]

        regex_list = [
            {"$regex": re.escape(t), "$options": "i"}
            for t in tokens
        ]

        filtro = {
            "$or": [
                {campo: {"$all": regex_list}}
                for campo in campos_busqueda
            ]
        }

        resultados = list(
            db["fondos_historicos"]
            .find(filtro, {"_id": 0})
            .limit(limite)
        )

        # Seguridad: evitar None o valores vacíos
        resultados_limpios = [
            {k: (v if v is not None else "") for k, v in r.items()}
            for r in resultados
        ]

        return resultados_limpios

    except Exception as e:
        print(f"❌ Error al buscar fondos históricos: {e}")
        return []
