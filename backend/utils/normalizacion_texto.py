#normalizacion_texto.py
import re
import unicodedata


def normalizar(texto: str) -> str:
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKC", texto)
    texto = texto.lower()

    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()
