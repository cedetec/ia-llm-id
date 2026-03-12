# services/indexing/legal_reconstructor.py

from backend.services.chunking_juridico import reconstruir_secciones


def reconstruir_documento(fragmentos):
    nuevos_chunks = reconstruir_secciones(fragmentos)

    if not nuevos_chunks:
        return fragmentos

    return nuevos_chunks