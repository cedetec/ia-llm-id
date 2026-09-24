# LLM/validators/document_filter_validator.py

from LLM.config.debug_settings import (
    DEBUG_DOCUMENT_FILTER
)


def validar_filtro_documental(

    pregunta,
    documento,
    anio,
    documentos_antes,
    documentos_despues

):

    if not DEBUG_DOCUMENT_FILTER:
        return

    print("\n========== FILTRO DOCUMENTAL ==========\n")

    print("Pregunta:")
    print(pregunta)
    print()

    print("Documento detectado:")
    print(documento)
    print()

    print("Año detectado:")
    print(anio)
    print()

    print(f"Chunks antes : {len(documentos_antes)}")
    print(f"Chunks después: {len(documentos_despues)}")
    print()

    for i, doc in enumerate(documentos_despues):

        print("=" * 80)

        print(f"Chunk {i+1}")

        print(doc.metadata)

        print()

        print(doc.page_content[:300])

        print()