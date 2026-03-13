#chunking_service.py
import re
from backend.services.preprocessing.config import FALLBACK_CHUNK_SIZE


PATRON_NUMERAL = re.compile(
    r'\n\s*(?:\d{1,2}|[IVX]+)\s*(?:\.|\-)?\s*'
    r'(OBJETIVO|FINALIDAD|PROPOSITO|'
    r'REQUISITOS?|'
    r'QUIENES\s+PUEDEN\s+POSTULAR|'
    r'POSTULACION|POSTULANTES?|'
    r'EVALUACION|'
    r'FINANCIAMIENTO|'
    r'BENEFICIARIOS|'
    r'PLAZOS?)',
    re.IGNORECASE
)


def chunkear(texto: str) -> list[str]:

    texto = re.split(
        r'(JOURNAL|SCOPUS|IMPACT FACTOR|WEB OF SCIENCE|PRODUCTIVIDAD CIENTIFICA)',
        texto,
        flags=re.IGNORECASE
    )[0]

    # limpiar OCR común
    texto = re.sub(r'-\n', '', texto)
    texto = re.sub(r'\n(?=[a-z])', ' ', texto)
    texto = re.sub(r'\s+\n', '\n', texto)

    # reparar encabezados partidos por OCR
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

    # ------------------------------------------------
    # reparar frases jurídicas rotas por OCR
    # ------------------------------------------------

    texto = re.sub(
        r'PODRAN\s*\n\s*POSTULAR',
        'PODRAN POSTULAR',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'PODRAN\s*POS-\s*TULAR',
        'PODRAN POSTULAR',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'APRUEBAN\s*\n\s*SE\s*\n\s*LAS\s*\n\s*BASES',
        'APRUEBANSE LAS BASES',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'APRUEBA\s*\n\s*LAS\s*\n\s*BASES',
        'APRUEBA LAS BASES',
        texto,
        flags=re.I
    )

    matches = list(PATRON_NUMERAL.finditer(texto))

    if matches:

        chunks = []

        for i, m in enumerate(matches):

            start = m.start()

            if i + 1 < len(matches):
                end = matches[i+1].start()
            else:
                end = len(texto)

            bloque = texto[start:end].strip()

            if len(bloque) > 120:
                chunks.append(bloque)

        return chunks

    # ------------------------------------------------
    # FALLBACK CHUNKING MEJORADO
    # ------------------------------------------------

    CHUNK_SIZE = max(FALLBACK_CHUNK_SIZE, 700)
    CHUNK_OVERLAP = 120

    step = CHUNK_SIZE - CHUNK_OVERLAP

    chunks = []

    for i in range(0, len(texto), step):

        chunk = texto[i:i + CHUNK_SIZE].strip()

        # evitar basura OCR muy corta
        if len(chunk) < 200:
            continue

        # evitar fragmentos extremadamente largos
        if len(chunk) > 2500:
            chunk = chunk[:2500]

        chunks.append(chunk)

    return chunks
