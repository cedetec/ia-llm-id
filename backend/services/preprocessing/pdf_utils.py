#pdf_utils.py
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
    texto = re.sub(r'(?<![\.:\;])\n(?!\d+\.)', '\n', texto)

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
    # REPARAR ENCABEZADOS JURÍDICOS PARTIDOS
    # -------------------------------------------------

    texto = re.sub(
        r'\bOBJETIVO\s*\n\s*DEL\s*\n\s*CONCURSO\b',
        'OBJETIVO DEL CONCURSO',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'\bREQUISITOS\s*\n\s*DE\s*\n\s*POSTULACION\b',
        'REQUISITOS DE POSTULACION',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'\bQUIENES\s*\n\s*PUEDEN\s*\n\s*POSTULAR\b',
        'QUIENES PUEDEN POSTULAR',
        texto,
        flags=re.I
    )

    # -------------------------------------------------
    # LIMPIEZA DE METADATOS PDF
    # -------------------------------------------------

    texto = re.sub(r'Página\s+\d+\s+de\s+\d+', '', texto, flags=re.I)
    texto = re.sub(r'https?://\S+', '', texto)

    # -------------------------------------------------
    # NORMALIZAR ESPACIOS
    # -------------------------------------------------

    texto = re.sub(r'[ \t]+', ' ', texto)
    return texto.strip()


def extraer_texto_pdf(ruta_pdf: str) -> str:

    texto_total = []

    try:

        with pdfplumber.open(ruta_pdf) as pdf:

            for page in pdf.pages:

                txt = page.extract_text()

                if txt:

                    texto_total.append(txt)

    except Exception:
        return ""

    texto = "\n\n".join(texto_total)
    return limpiar_texto_pdf(texto)

# services/preprocessing/section_detector.py

def detectar_seccion_legal(texto: str) -> str:
    t = texto.lower()

    if "objetivo" in t:
        return "objetivo"

    if "postular" in t or "beneficiarios" in t:
        return "postulantes"

    if "requisitos" in t:
        return "requisitos"

    if "evaluación" in t:
        return "evaluacion"

    if "financiamiento" in t and "apruebanse" not in t and "apruebase" not in t:
        return "financiamiento"

    if "resolución exenta" in t:
        return "resolucion"

    return "general"
