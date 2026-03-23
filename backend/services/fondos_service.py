#fondos_service.py
from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv
from backend.services.retrieval_text_utils import safe_split
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

campos_busqueda = [
    "nombre",
    "descripcion",
    "objetivo",
    "beneficiarios",
    "requisitos",
    "financiamiento",
    "cofinanciamiento",
    "trl",
    "equidad_genero",
    "duracion",
    "monto_maximo"
]


def buscar_fondos_relevantes(pregunta: str, limite: int = 10):

    try:
        if not pregunta:
            return []

        tokens = [t for t in safe_split(pregunta) if len(t) > 2]

        if not tokens:
            return []

        filtro = {
            "$and": [
                {
                    "$or": [
                        {campo: {"$regex": t, "$options": "i"}}
                        for campo in campos_busqueda
                    ]
                }
                for t in tokens
            ]
        }

        resultados = list(
            db["fondos_historicos"]
            .find(filtro, {"_id": 0})
            .limit(limite)
        )

        resultados_limpios = [
            {k: (v if v is not None else "") for k, v in r.items()}
            for r in resultados
        ]

        return resultados_limpios

    except Exception as e:
        print(f"❌ Error al buscar fondos históricos: {e}")
        return []
