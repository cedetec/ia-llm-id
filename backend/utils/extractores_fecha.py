#extractores_fecha.py
import re

PATRONES_FECHA = [
    r"\b\d{1,2}/\d{1,2}/(19|20)\d{2}\b",
    r"\b\d{1,2}\.\d{1,2}\.(19|20)\d{2}\b",
    r"\b\d{1,2}\s+de\s+\w+\s+de\s+(19|20)\d{2}\b"
]

def extraer_fecha_resolucion(texto: str) -> str | None:
    if not texto:
        return None

    for patron in PATRONES_FECHA:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            return m.group(0)

    return None
