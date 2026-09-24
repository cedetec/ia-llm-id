# LLM/validators/retriever_config_validator.py

from LLM.config.debug_settings import (
    DEBUG_RETRIEVER
)


def validar_configuracion_retriever(config):

    if not DEBUG_RETRIEVER:
        return

    print("\n========== CONFIGURACIÓN DEL RETRIEVER ==========\n")

    print(f"Tipo            : {config['search_type']}")
    print(f"k               : {config['k']}")
    print(f"fetch_k         : {config['fetch_k']}")
    print(f"lambda_mult     : {config['lambda_mult']}")
    print(f"score_threshold : {config['score_threshold']}")

    print()