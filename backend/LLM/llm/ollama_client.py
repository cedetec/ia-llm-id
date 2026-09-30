# LLM/llm/ollama_client.py

from langchain_ollama import ChatOllama

from LLM.config import llm_config

import os

from RAG.config.embedding_settings import (
    DEFAULT_OLLAMA_HOST
)


def crear_llm():

    return ChatOllama(

        model=llm_config.MODELO_ACTUAL,

        base_url=os.getenv(
            "OLLAMA_HOST",
            DEFAULT_OLLAMA_HOST
        ),

        temperature=0,

        num_ctx=4096,

        num_predict=768,

        reasoning=False

    )
