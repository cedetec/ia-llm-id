# LLM/rag/context_builder.py

import logging

logger = logging.getLogger(__name__)

MAX_CARACTERES = 12000


def _formatear_chunk(
    indice,
    documento
):
    """
    Genera el bloque de texto que se enviará al LLM
    para un chunk determinado.
    """

    return f"""
Documento {indice}: {documento.metadata.get("documento", "")}
Sección: {documento.metadata.get("seccion", "")}
Página: {documento.metadata.get("pagina", "")}
Encabezado: {documento.metadata.get("encabezado_original", "")}

{documento.page_content}

---
"""


def construir_contexto(
    documentos,
    tipo_consulta=None
):
    """
    Construye el contexto final que será enviado al LLM.
    El orden de los documentos ya viene determinado por
    RetrievalPipeline y el reranker.
    """

    documentos = list(documentos)

    logger.info(
        "Construyendo contexto con %s documentos.",
        len(documentos)
    )

    contexto = ""

    firmas_vistas = set()

    indice = 1

    longitud_actual = 0

    documento_actual = None

    for doc in documentos:

        firma = (

            doc.metadata.get("documento"),

            doc.metadata.get("pagina"),

            doc.metadata.get("titulo_hijo"),

            doc.metadata.get("subtitulo"),

            hash(doc.page_content)

        )

        if firma in firmas_vistas:
            continue

        firmas_vistas.add(firma)

        if doc.metadata.get("documento") != documento_actual:

            documento_actual = doc.metadata.get(
                "documento"
            )

            contexto += (
                "\n"
                "==============================\n"
                f"DOCUMENTO: {documento_actual}\n"
                "==============================\n\n"
            )

        longitud_chunk = len(doc.page_content)

        if longitud_actual + longitud_chunk > MAX_CARACTERES:
            continue

        longitud_actual += longitud_chunk

        logger.debug(
            "Chunk %s | Página %s | %s caracteres",
            indice,
            doc.metadata.get("pagina"),
            longitud_chunk
        )

        bloque = _formatear_chunk(
            indice,
            doc
        )

        contexto += bloque

        indice += 1

    logger.info(
        "Contexto generado (%s documentos, %s caracteres).",
        indice - 1,
        len(contexto)
    )

    return contexto
