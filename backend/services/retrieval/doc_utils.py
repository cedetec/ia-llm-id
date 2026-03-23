# backend/services/retrieval/doc_utils.py

import re
import unicodedata
from services.retrieval_text_utils import normalizar


def extraer_nombre_documento(pregunta: str):

    if not pregunta:
        return None

    pregunta = pregunta.lower()

    # detectar cualquier nombre terminado en .pdf
    match = re.search(r'([a-z0-9\-\_]+\.pdf)', pregunta)

    if match:
        return match.group(1)

    return None


def normalizar_nombre_doc(s: str) -> str:
    if not s:
        return ""

    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()

    # quitar .pdf
    s = re.sub(r'\.pdf$', '', s)

    return s.strip()
