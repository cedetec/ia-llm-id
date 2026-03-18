# backend/services/consulta/llm_handler.py

from backend.services.prompt_service import construir_prompt
from backend.core.llm import consultar_llm, LLMTimeoutError, LLMConnectionError, LLMHTTPError
from backend.services.consulta_utils_llm import limpiar_salida_llm, recortar_contexto_para_llm


def salida_llm_valida(respuesta, pregunta):
    """
    Evita respuestas inútiles del LLM como repetir la pregunta
    o devolver frases genéricas.
    """
    if not respuesta:
        return False

    r = respuesta.lower()
    p = pregunta.lower()

    # el LLM repite la pregunta
    if p[:40] in r:
        return False

    # respuestas genéricas
    patrones_invalidos = [
        "no se encuentra",
        "no tengo información",
        "no aparece en el contexto",
        "no puedo encontrar",
    ]

    if any(x in r for x in patrones_invalidos):
        return False

    return True


def responder_con_llm(pregunta, contexto):

    contexto_llm = recortar_contexto_para_llm(contexto, max_chars_total=3000)
    prompt = construir_prompt(pregunta, contexto_llm)

    try:
        raw = consultar_llm(prompt)
        raw = limpiar_salida_llm(raw)

        # NUEVA VALIDACIÓN
        if not salida_llm_valida(raw, pregunta):
            return {
                "respuesta": contexto_llm[:300],
                "fuente": "RAG (fallback contexto)"
            }

        return {
            "respuesta": raw,
            "fuente": "RAG + LLM"
        }

    except (LLMTimeoutError, LLMConnectionError, LLMHTTPError):

        return {
            "respuesta": contexto_llm[:300],
            "fuente": "RAG (sin LLM)",
        }
