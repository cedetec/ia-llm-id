import re
from backend.services.retrieval_text_utils import safe_split

def extraer_numero_resolucion(contexto):

    if isinstance(contexto, dict):
        contexto = contexto.get("contenido") or contexto.get("texto") or ""
    elif isinstance(contexto, list):
        contexto = " ".join(
            x.get("contenido", "") if isinstance(x, dict) else str(x)
            for x in contexto
        )
    elif not isinstance(contexto, str):
        contexto = str(contexto or "")

    texto = contexto.lower()

    patrones = [
        r'resolucion\s*(exenta|exento)?\s*(n[°ºo]|nº|n°|numero)?\s*\d{1,5}',
        r'\bn[°ºo]?\s*\d{1,5}[/\-]\d{2,4}',
        r'\bresolucion\s*n\s*\d{1,5}'
    ]

    for p in patrones:
        m = re.search(p, texto, re.I)
        if m:
            return m.group(0)

    return None
