# backend/services/preprocessing/chunking_service.py

import re
from backend.services.preprocessing.config import FALLBACK_CHUNK_SIZE


def chunkear(texto: str) -> list[str]:

    patron = re.compile(
        r"(OBJETIVO|REQUISITOS|POSTULACI[ÓO]N|EVALUACI[ÓO]N|FINANCIAMIENTO)",
        re.IGNORECASE
    )

    partes = patron.split(texto)

    if len(partes) > 1:

        chunks = []

        for i in range(1, len(partes), 2):

            bloque = (partes[i] + partes[i+1]).strip()

            if len(bloque) > 80:
                chunks.append(bloque)

        return chunks

    # fallback con overlap
    CHUNK_SIZE = FALLBACK_CHUNK_SIZE
    CHUNK_OVERLAP = int(CHUNK_SIZE * 0.25)

    chunks = []

    for i in range(0, len(texto), CHUNK_SIZE - CHUNK_OVERLAP):

        chunk = texto[i:i + CHUNK_SIZE].strip()

        if len(chunk) > 80:
            chunks.append(chunk)

    return chunks
