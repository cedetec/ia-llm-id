# LLM/validators/retrieval_validator.py

from LLM.config.debug_settings import (
    DEBUG_RETRIEVER
)


def validar_retriever(

    etapa,

    pregunta,

    documentos

):

    if not DEBUG_RETRIEVER:
        return

    print(f"\n========== {etapa} ==========\n")

    print("Pregunta:")

    print(pregunta)

    print()

    print(f"Cantidad de documentos: {len(documentos)}")

    print()

    for i, doc in enumerate(documentos):

        print("=" * 80)

        print(f"Documento {i+1}")

        print("Metadata:")

        print(doc.metadata)

        print()

        print("Contenido:")

        print(doc.page_content[:350])