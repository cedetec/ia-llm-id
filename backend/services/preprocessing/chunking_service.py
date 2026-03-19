# chunking_service.py
import re
from backend.services.preprocessing.config import FALLBACK_CHUNK_SIZE


# ------------------------------------------------
# PATRONES JURÍDICOS IMPORTANTES
# ------------------------------------------------

PATRON_NUMERAL = re.compile(
r'\n\s*(?:\d{1,2}|[IVX]+)\s*(?:\.|\-)?\s*'
r'(OBJETIVO|FINALIDAD|PROPOSITO|'
r'REQUISITOS?|REQUISITOS\s+DE\s+POSTULACION|'
r'QUIENES\s+PUEDEN\s+POSTULAR|'
r'POSTULACION|POSTULANTES?|'
r'EVALUACION|EVALUACION\s+DE\s+PROYECTOS|'
r'FINANCIAMIENTO|'
r'BENEFICIARIOS|'
r'PLAZOS?|'
r'ADJUDICACION|'
r'FORMALIZACION)',
re.IGNORECASE
)

PATRON_RESOLUCION = re.compile(
    r'RESOLUCI[ÓO]N\s*\n*\s*EXENT[AO]\s*\n*\s*N[°º]?\s*\d+',
    re.IGNORECASE
)

PATRON_ESTRUCTURA_RESOL = re.compile(
    r'\n\s*(VISTO|VISTOS|CONSIDERANDO|RESUELVO|RESUELVE)\s*:?',
    re.IGNORECASE
)


# ------------------------------------------------
# LIMPIEZA OCR PROFESIONAL
# ------------------------------------------------

def limpiar_ocr(texto: str) -> str:

    texto = re.sub(r'-\n', '', texto)
    texto = re.sub(r'\n(?=[a-záéíóúñ])', ' ', texto)
    texto = re.sub(r'\s+\n', '\n', texto)

    texto = re.sub(r'\n{2,}', '\n', texto)

    # reparar palabras cortadas por OCR
    texto = re.sub(r'POS-\s*TUL', 'POSTUL', texto, flags=re.I)
    texto = re.sub(r'INVES-\s*TIG', 'INVESTIG', texto, flags=re.I)

    # reparar encabezados comunes
    texto = re.sub(
        r'QUIENES\s*\n\s*PUEDEN\s*\n\s*POSTULAR',
        'QUIENES PUEDEN POSTULAR',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'REQUISITOS\s*\n\s*DE\s*\n\s*POSTULACION',
        'REQUISITOS DE POSTULACION',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'APRUEBA\s*\n\s*LAS\s*\n\s*BASES',
        'APRUEBA LAS BASES',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'RES\s*U\s*E\s*L\s*V\s*O',
        'RESUELVO',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'C\s*O\s*N\s*S\s*I\s*D\s*E\s*R\s*A\s*N\s*D\s*O',
        'CONSIDERANDO',
        texto,
        flags=re.I
    )

    return texto


# ------------------------------------------------
# DIVISIÓN DE BLOQUES JURÍDICOS GRANDES
# ------------------------------------------------

def subdividir_bloque(texto, max_chars=900):

    if len(texto) <= max_chars:
        return [texto]

    OVERLAP = 120

    partes = []

    for i in range(0, len(texto), max_chars - OVERLAP):
        partes.append(texto[i:i + max_chars].strip())

    return partes

# ------------------------------------------------
# MERGE DE CHUNKS PEQUEÑOS
# ------------------------------------------------

def merge_chunks(chunks):

    merged_chunks = []
    buffer = ""

    MAX_CHARS = 2200

    for chunk in chunks:

        if len(chunk) < 200:
            buffer += " " + chunk
            continue

        if buffer:
            chunk = buffer + " " + chunk
            buffer = ""

        if len(chunk) > MAX_CHARS:

            partes = [
                chunk[i:i + MAX_CHARS]
                for i in range(0, len(chunk), MAX_CHARS)
            ]

            merged_chunks.extend(partes)

        else:
            merged_chunks.append(chunk)

    return merged_chunks

# ------------------------------------------------
# CHUNKING PRINCIPAL
# ------------------------------------------------

def chunkear(texto: str) -> list[str]:

    texto = re.split(
        r'(JOURNAL|SCOPUS|IMPACT FACTOR|WEB OF SCIENCE|PRODUCTIVIDAD CIENTIFICA)',
        texto,
        flags=re.IGNORECASE
    )[0]

    texto = limpiar_ocr(texto)

    # ------------------------------------------------
    # CHUNKING PARA ESTRUCTURA DE RESOLUCIONES
    # ------------------------------------------------

    matches_res = list(PATRON_ESTRUCTURA_RESOL.finditer(texto))

    if len(matches_res) >= 2:

        chunks = []

        for i, m in enumerate(matches_res):

            start = m.start()

            if i + 1 < len(matches_res):
                end = matches_res[i + 1].start()
            else:
                end = len(texto)

            bloque = texto[start:end].strip()

            if len(bloque) < 200:
                continue

            partes = subdividir_bloque(bloque)

            chunks.extend(partes)

        if chunks:
            return merge_chunks(chunks)

    matches = list(PATRON_NUMERAL.finditer(texto))

    # ------------------------------------------------
    # CHUNKING POR SECCIONES JURÍDICAS
    # ------------------------------------------------

    if len(matches) >= 2:

        chunks = []

        for i, m in enumerate(matches):

            start = m.start()

            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(texto)

            bloque = texto[start:end].strip()

            if len(bloque) < 400:
                continue

            partes = subdividir_bloque(bloque)

            chunks.extend(partes)

        return merge_chunks(chunks)

    # ------------------------------------------------
    # FALLBACK CHUNKING
    # ------------------------------------------------

    CHUNK_SIZE = max(FALLBACK_CHUNK_SIZE, 900)
    CHUNK_OVERLAP = 150

    step = CHUNK_SIZE - CHUNK_OVERLAP

    chunks = []

    for i in range(0, len(texto), step):

        chunk = texto[i:i + CHUNK_SIZE].strip()

        if len(chunk) < 350:
            continue

        if len(chunk.split()) < 60:
            continue

        if len(chunk) > 2200:
            chunk = chunk[:2200]

        chunks.append(chunk)
