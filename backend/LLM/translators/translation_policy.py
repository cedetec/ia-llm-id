from LLM.config.llm_config import (
    MODELOS,
    MODELO_ACTUAL
)


def usar_traduccion():

    return MODELOS[MODELO_ACTUAL]["traducir"]