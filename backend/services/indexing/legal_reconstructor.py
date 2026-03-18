# services/indexing/legal_reconstructor.py

from backend.services.chunking_juridico import reconstruir_secciones


def reconstruir_documento(fragmentos):

    nuevos_chunks = reconstruir_secciones(fragmentos)

    if not nuevos_chunks:
        return fragmentos

    # convertir dict → texto
    resultado = []

    for c in nuevos_chunks:

        if isinstance(c, dict):
            resultado.append(c.get("contenido", ""))
        else:
            resultado.append(c)

    return resultado
