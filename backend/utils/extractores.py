#extractores.py
import re

PATRON_RESOLUCION = re.compile(
    r'(?:resolucion\s*(?:exent[ao])?\s*(?:n[°º5:]*)?\s*)(\d{1,6}/\d{2,4})',
    re.IGNORECASE
)

def extraer_numero_resolucion(texto: str):
    if not texto:
        return None

    m = PATRON_RESOLUCION.search(texto)
    if m:
        return m.group(1)
    return None
