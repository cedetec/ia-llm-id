import pdfplumber
import re


def limpiar_texto_pdf(texto: str) -> str:

    if not texto:
        return ""

    # -------------------------------------------------
    # NORMALIZAR SALTOS
    # -------------------------------------------------

    texto = texto.replace("\r", "\n")

    # -------------------------------------------------
    # UNIR LETRAS SEPARADAS POR OCR (F O N D E C Y T)
    # -------------------------------------------------

    texto = re.sub(r'\b([A-Z])\s+([A-Z])\b', r'\1\2', texto)

    # repetir varias veces por seguridad
    texto = re.sub(r'\b([A-Z])\s+([A-Z])\b', r'\1\2', texto)

    # -------------------------------------------------
    # UNIR PALABRAS CORTADAS POR SALTO DE LÍNEA
    # -------------------------------------------------

    # ejemplo:
    # investiga-
    # ción
    texto = re.sub(r'(\w)-\n(\w)', r'\1\2', texto)

    # unir líneas que no terminan en punto
    texto = re.sub(r'(?<![\.:\;])\n', ' ', texto)

    # -------------------------------------------------
    # CORRECCIONES OCR FRECUENTES
    # -------------------------------------------------

    texto = re.sub(r'\b[Tt]os\s+', 'Los ', texto)
    texto = re.sub(r'\b[Aa]ción\b', 'Acción', texto)

    # palabras deformadas
    texto = re.sub(r'deformación', 'de formación', texto)

    # FONDECYT separado
    texto = re.sub(r'f\s*o\s*n\s*d\s*e\s*c\s*y\s*t', 'FONDECYT', texto, flags=re.I)

    # RESOLUCION separado
    texto = re.sub(r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n', 'Resolución', texto, flags=re.I)

    # -------------------------------------------------
    # LIMPIEZA DE METADATOS PDF
    # -------------------------------------------------

    texto = re.sub(r'Página\s+\d+\s+de\s+\d+', '', texto, flags=re.I)
    texto = re.sub(r'https?://\S+', '', texto)

    # -------------------------------------------------
    # NORMALIZAR ESPACIOS
    # -------------------------------------------------

    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()


def extraer_texto_pdf(ruta_pdf: str) -> str:

    texto_total = []

    try:

        with pdfplumber.open(ruta_pdf) as pdf:

            for page in pdf.pages:

                txt = page.extract_text()

                if txt:

                    txt = limpiar_texto_pdf(txt)

                    texto_total.append(txt)

    except Exception:
        return ""

    return "\n\n".join(texto_total)