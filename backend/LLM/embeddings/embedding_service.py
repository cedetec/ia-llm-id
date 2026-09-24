# LLM/embeddings/embeddings_service.py

from langchain_ollama import (
    OllamaEmbeddings
)

from LLM.config.config_loader import (
    cargar_configuracion_embeddings
)


def crear_embeddings(modelo=None):

    config = cargar_configuracion_embeddings()

    modelo = modelo or config["model"]

    return OllamaEmbeddings(

        model=modelo,

        base_url=config["host"]

    )
