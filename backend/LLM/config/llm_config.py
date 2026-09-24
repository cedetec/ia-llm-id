# config/llm_config.py

MODELOS = {

    "deepseek-r1:8b": {

        "traducir": True,

        "idioma": "en"

    },

    "gemma4:e2b": {

        "traducir": False,

        "idioma": "es"

    },

    "mistral:latest": {

        "traducir": False,

        "idioma": "es"

    },

    "qwen2.5:latest": {

        "traducir": False,

        "idioma": "es"

    }

}

MODELO_ACTUAL = "gemma4:e2b"

def cambiar_modelo(modelo: str):

    global MODELO_ACTUAL

    if modelo not in MODELOS:

        raise ValueError(
            f"Modelo no registrado: {modelo}"
        )

    MODELO_ACTUAL = modelo

    print(
        f"[LLM CONFIG] Modelo activo -> {MODELO_ACTUAL}"
    )


def obtener_modelo():

    return MODELO_ACTUAL


def obtener_configuracion():

    return MODELOS[MODELO_ACTUAL]
