# backend/services/consulta_service.py

from backend.services.intent_service import (
    normalizar_pregunta,
    detectar_intent,
)

from backend.services.consulta_utils_text import modo_cita, extraer_docfile, normalizar_contexto
from backend.services.consulta.calendar_handler import manejar_calendario
from backend.services.consulta.rag_handler import recuperar_contexto

from backend.services.consulta.structured_extractors import (
    extraer_numero_resolucion_estructurado,
    extraer_fecha_si_aplica,
)

from backend.services.consulta.cita_handler import manejar_cita
from backend.services.consulta.llm_handler import responder_con_llm
from backend.services.translation_service import traducir
import re


def procesar_consulta(pregunta: str) -> dict:

    pregunta_norm = normalizar_pregunta(pregunta)

    if len(pregunta_norm.strip()) <= 4:
        return {
            "respuesta": "La consulta no es lo suficientemente específica.",
            "fuente": "Sistema"
        }

    intent = detectar_intent(pregunta_norm)

    # -------------------------------------------------
    # ROUTER PREGUNTAS ESTRUCTURADAS
    # -------------------------------------------------

    pregunta_low = pregunta_norm.lower()

    # -------------------------------------------------
    # ROUTER PREGUNTAS ESTRUCTURADAS
    # -------------------------------------------------
    
    if any(x in pregunta_low for x in [
        "numero de resolucion",
        "número de resolución",
        "fecha de resolucion",
        "fecha del documento",
        "tomado de razon",
    ]):

        # recuperar contexto mínimo
        contexto = recuperar_contexto(
            pregunta,
            True,
            extraer_docfile(pregunta)
        )

        if contexto:
            contexto = normalizar_contexto(contexto)

            # 🔍 EXTRACCIÓN
            numero = extraer_numero_resolucion_estructurado(
                pregunta_low,
                contexto
            )

            if numero:
                return {
                    "respuesta": numero,
                    "fuente": "Extracción estructurada"
                }

            fecha = extraer_fecha_si_aplica(
                pregunta_low,
                contexto
            )

            if fecha:
                return {
                    "respuesta": fecha,
                    "fuente": "Extracción estructurada"
                }

            # -------------------------------------------------
            # EXTRACCIÓN DIRECTA PARA OBJETIVO / REQUISITOS
            # -------------------------------------------------

            if any(x in pregunta_low for x in ["objetivo del concurso", "objetivo general"]):

                m = re.search(
                    r'(objetivo[^\.]{40,250}\.)',
                    contexto,
                    re.I
                )

                if m:
                    return {
                        "respuesta": m.group(1).strip(),
                        "fuente": "RAG (extracción directa)"
                    }


            if any(x in pregunta_low for x in ["requisito", "pueden postular", "quienes pueden postular"]):

                m = re.search(
                    r'((pueden|podran|quienes)\s+postular[^\.]{40,250}\.)',
                    contexto,
                    re.I
                )

                if m:
                    return {
                        "respuesta": m.group(1).strip(),
                        "fuente": "RAG (extracción directa)"
                    }

    # 1️⃣ Calendario
    resp_cal = manejar_calendario(intent, pregunta_norm)

    if resp_cal:
        return resp_cal

    # 2️⃣ RAG
    es_modo_cita = modo_cita(pregunta)
    docfile = extraer_docfile(pregunta)

    if docfile:
        docfile = docfile.lower()

    contexto = recuperar_contexto(pregunta, es_modo_cita, docfile)
    if contexto:
        print("\nTAMAÑO CONTEXTO:", len(contexto))

    if not contexto:
        return {
            "respuesta": "No se encontró información relevante en los documentos.",
            "fuente": "RAG"
        }

    pregunta_low = pregunta_norm.lower()

    # 🔥 FIX CONTEXTO
    contexto = normalizar_contexto(contexto)

    # 3️⃣ Extracción estructurada
    numero = extraer_numero_resolucion_estructurado(pregunta_low, contexto)

    if numero:
        return {
            "respuesta": numero,
            "fuente": "RAG + extracción estructurada"
        }

    fecha = extraer_fecha_si_aplica(pregunta_low, contexto)

    if fecha:
        return {
            "respuesta": fecha,
            "fuente": "RAG + extracción estructurada"
        }

    # 4️⃣ Citas
    if es_modo_cita:

        resp_cita = manejar_cita(pregunta_low, contexto, pregunta)

        if resp_cita:
            return resp_cita

        # si no se encuentra cita real
        return {
            "respuesta": "No se encontró una frase textual que coincida en el documento.",
            "fuente": "RAG (sin coincidencia)"
        }

    # 5️⃣ LLM con traducción
    prompt_en = traducir(
        f"Question:\n{pregunta}\n\nContext:\n{contexto}",
        from_code="es",
        to_code="en"
    )

    respuesta_en = responder_con_llm(prompt_en, None)

    respuesta_es = traducir(
        respuesta_en,
        from_code="en",
        to_code="es"
    )

    return {
        "respuesta": respuesta_es,
        "fuente": "RAG + LLM traducido"
    }
