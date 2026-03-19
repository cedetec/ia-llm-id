import re

PATRON_RESOLUCION = re.compile(
    r'(?:resolucion\s*(?:exent[ao])?\s*(?:n[°ºo\.:\-]*)?\s*)'
    r'(\d{1,6}\s*[/\-.]\s*\d{2,4})',
    re.IGNORECASE
)

def extraer_numero_resolucion(texto):

    # 🔥 NORMALIZACIÓN ROBUSTA
    if isinstance(texto, list):
        partes = []
        for t in texto:
            if isinstance(t, dict):
                val = t.get("contenido") or t.get("texto")
                if isinstance(val, str):
                    partes.append(val)
            elif isinstance(t, str):
                partes.append(t)
        texto = " ".join(partes)

    elif isinstance(texto, dict):
        texto = texto.get("contenido") or texto.get("texto") or ""

    if not isinstance(texto, str) or not texto.strip():
        return None

    # 🔧 FIX OCR
    texto = texto.replace("l", "1")

    m = PATRON_RESOLUCION.search(texto)
    if m:
        return m.group(1).strip()

    return None
