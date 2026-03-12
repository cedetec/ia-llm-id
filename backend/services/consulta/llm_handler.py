# backend/services/consulta/llm_handler.py

from backend.services.prompt_service import construir_prompt
from backend.core.llm import consultar_llm, LLMTimeoutError, LLMConnectionError, LLMHTTPError
from backend.services.consulta_utils_llm import limpiar_salida_llm, recortar_contexto_para_llm


def responder_con_llm(pregunta, contexto):

    contexto_llm = recortar_contexto_para_llm(contexto, max_chars_total=3000)
    prompt = construir_prompt(pregunta, contexto_llm)

    try:
        raw = consultar_llm(prompt)
        raw = limpiar_salida_llm(raw)

        return {
            "respuesta": raw or "No encontrado en el contexto.",
            "fuente": "RAG + LLM"
        }

    except (LLMTimeoutError, LLMConnectionError, LLMHTTPError):

        return {
            "respuesta": (
                "No fue posible conectarse al modelo generativo (LLM). "
                "Sin embargo, se recuperó contexto documental relevante."
            ),
            "fuente": "RAG (sin LLM)",
        }