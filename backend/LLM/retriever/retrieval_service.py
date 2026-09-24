# LLM/retrieval/retrieval_service.py

from LLM.config.config_loader import (
    cargar_configuracion_retriever
)

from LLM.validators.retriever_config_validator import (
    validar_configuracion_retriever
)


def crear_retriever(
    vectorstore,
    tipo_consulta=None
):

    config = cargar_configuracion_retriever()

    validar_configuracion_retriever(
        config
    )

    kwargs = {
        "k": config["k"]
    }

    if tipo_consulta in {

        "OBJETIVO_GENERAL",
        "OBJETIVOS_ESPECIFICOS",
        "REQUISITOS",
        "FINANCIAMIENTO"

    }:

        kwargs["k"] = min(
            kwargs["k"],
            10
        )

    elif tipo_consulta == "ORGANIZADOR":

        kwargs["k"] = max(
            kwargs["k"],
            12
        )

    if config["search_type"] == "mmr":

        kwargs["fetch_k"] = config["fetch_k"]

        kwargs["lambda_mult"] = config["lambda_mult"]

    elif (
        config["search_type"]
        == "similarity_score_threshold"
    ):

        if config["score_threshold"] is not None:

            kwargs["score_threshold"] = (
                config["score_threshold"]
            )

    print(

        "[RETRIEVER CONFIG]",

        {

            "tipo_consulta": tipo_consulta,

            "search_type": config["search_type"],

            "k": kwargs["k"],

            "fetch_k": kwargs.get("fetch_k"),

            "lambda_mult": kwargs.get("lambda_mult"),

            "score_threshold": kwargs.get("score_threshold")

        }

    )

    print(
        "[RETRIEVER] Chunks en colección:",
        vectorstore._collection.count()
    )

    return vectorstore.as_retriever(

        search_type=config["search_type"],

        search_kwargs=kwargs

    )
