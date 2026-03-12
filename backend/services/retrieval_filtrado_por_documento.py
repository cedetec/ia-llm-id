# retrieval_filtrado_por_documento.py
import re
from backend.services.retrieval_mongo_repo import find_docs

def obtener_contexto_documento(documento: str, scan: int = 400):

    if not documento:
        return []

    filtro = {
        "metadata.documento": {
            "$regex": f"^{re.escape(documento)}$",
            "$options": "i"
        }
    }

    docs = find_docs(filtro, scan=scan)

    MAX_CHARS = 1000

    return [
        d["contenido"][:MAX_CHARS]
        for d in docs
        if isinstance(d.get("contenido"), str)
    ]