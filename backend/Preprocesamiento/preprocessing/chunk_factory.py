# LLM/preprocessing/chunk_factory.py

from langchain_core.documents import Document


def crear_documento(

    texto,

    metadata

):

    return Document(

        page_content=texto,

        metadata=metadata

    )
