# LLM/llm/ollama_client.py

from langchain_ollama import ChatOllama

from RAG.config import llm_config

import os

from RAG.config.embedding_settings import (
    DEFAULT_OLLAMA_HOST
)


def crear_llm(modelo=None):
    modelo = modelo or llm_config.MODELO_ACTUAL
    return ChatOllama(

        model=modelo,

        base_url=os.getenv(
            "OLLAMA_HOST",
            DEFAULT_OLLAMA_HOST
        ),

        temperature=0,

        num_ctx=4096,

        num_predict=768,

        reasoning=False,

        keep_alive=-1

    )
