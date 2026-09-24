# LLM/config/config_loader.py

import os

from LLM.config.embedding_settings import (

    DEFAULT_EMBEDDING_MODEL,

    DEFAULT_OLLAMA_HOST

)

from LLM.config.retrieval_settings import (

    DEFAULT_K,

    DEFAULT_FETCH_K,

    DEFAULT_LAMBDA,

    DEFAULT_SEARCH_TYPE,

    DEFAULT_SCORE_THRESHOLD

)


def cargar_configuracion_embeddings():

    return {

        "model": os.getenv(

            "EMBEDDING_MODEL",

            DEFAULT_EMBEDDING_MODEL

        ),

        "host": os.getenv(

            "OLLAMA_HOST",

            DEFAULT_OLLAMA_HOST

        )

    }


def cargar_configuracion_retriever():

    score_threshold = os.getenv(
        "RETRIEVER_SCORE_THRESHOLD"
    )

    if score_threshold is not None:

        score_threshold = float(
            score_threshold
        )

    else:

        score_threshold = DEFAULT_SCORE_THRESHOLD

    return {

        "k": int(

            os.getenv(

                "RETRIEVER_K",

                DEFAULT_K

            )

        ),

        "fetch_k": int(

            os.getenv(

                "RETRIEVER_FETCH_K",

                DEFAULT_FETCH_K

            )

        ),

        "lambda_mult": float(

            os.getenv(

                "RETRIEVER_LAMBDA",

                DEFAULT_LAMBDA

            )

        ),

        "search_type": os.getenv(

            "RETRIEVER_TYPE",

            DEFAULT_SEARCH_TYPE

        ).lower(),

        "score_threshold": score_threshold

    }