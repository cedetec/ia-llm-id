# LLM/validators/llm_validator.py

from LLM.config.debug_settings import (
    DEBUG_LLM
)


def validar_llm(

    pregunta,

    contexto,

    respuesta

):

    if not DEBUG_LLM:
        return

    print("\n========== LLM ==========\n")

    print("Pregunta:")
    print(pregunta)

    print("\n========== CONTEXTO ==========\n")

    print(f"Tamaño del contexto: {len(contexto)} caracteres\n")

    print(contexto[:4000])

    if len(contexto) > 4000:

        print("\n... CONTEXTO TRUNCADO ...")

    print("\n========== RESPUESTA ==========\n")

    print(respuesta)