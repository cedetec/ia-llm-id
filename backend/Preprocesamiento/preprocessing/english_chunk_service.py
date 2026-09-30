# LLM/preprocessing/english_chunk_service.py

from LLM.translators.argos_translator import (
    translator
)


def enriquecer_chunks_en_ingles(documentos):
    """
    Genera una versión en inglés de cada chunk para
    utilizarla posteriormente en el CrossEncoder.

    La traducción se realiza únicamente durante la
    indexación.
    """

    for doc in documentos:

        #
        # Evitar volver a traducir si ya existe.
        #

        if doc.metadata.get("page_content_en"):
            continue

        try:

            doc.metadata["page_content_en"] = (
                translator.es_a_en(
                    doc.page_content
                )
            )

        except Exception:

            #
            # Respaldo.
            #

            doc.metadata["page_content_en"] = (
                doc.page_content
            )

    return documentos
