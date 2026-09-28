# LLM/response/response_generation_service.py

from LLM.validators.llm_validator import (
    validar_llm
)

from LLM.translators.translation_policy import (
    usar_traduccion
)

from LLM.translators.argos_translator import (
    translator
)


def procesar_respuesta(
    resultado_rag,
    pregunta,
    respuesta_llm,
    referencia=None,
    calcular_ragas=False
):

    #
    # =====================================================
    # Datos provenientes del RAG
    # =====================================================
    #

    contexto = resultado_rag.get(
        "context_text",
        ""
    )

    contextos_ragas = resultado_rag.get(
        "contextos_ragas",
        []
    )

    #
    # =====================================================
    # Respuesta generada por Ollama
    # =====================================================
    #

    texto_respuesta = respuesta_llm.content

    print(
        "\n================ RESPUESTA DE OLLAMA ================\n"
    )

    print(
        texto_respuesta
    )

    #
    # =====================================================
    # Traducción de salida
    # =====================================================
    #

    if usar_traduccion():

        print(
            "[ANTES TRADUCCION]",
            texto_respuesta
        )

        texto_respuesta = translator.en_a_es(
            texto_respuesta
        )

        print(
            "[DESPUES TRADUCCION]",
            texto_respuesta
        )

    #
    # =====================================================
    # Validación
    # =====================================================
    #

    validar_llm(
        pregunta,
        contexto,
        texto_respuesta
    )

    #
    # =====================================================
    # RAGAS
    # =====================================================
    #

    metricas_ragas = {

        "context_precision": None,

        "context_recall": None,

        "faithfulness": None,

        "answer_relevancy": None

    }

    if calcular_ragas:

        print(
            "\n================ RAGAS ================\n"
        )

        try:

            from LLM.evaluation.ragas_metrics import (
                RagasMetrics
            )

            ragas = RagasMetrics()

            metricas_ragas = ragas.evaluar(

                pregunta=pregunta,

                respuesta=texto_respuesta,

                contextos=contextos_ragas,

                referencia=referencia

            )

            print(
                "Context Precision:",
                metricas_ragas.get(
                    "context_precision"
                )
            )

            print(
                "Context Recall:",
                metricas_ragas.get(
                    "context_recall"
                )
            )

            print(
                "Faithfulness:",
                metricas_ragas.get(
                    "faithfulness"
                )
            )

            print(
                "Answer Relevance:",
                metricas_ragas.get(
                    "answer_relevancy"
                )
            )

        except Exception as e:

            print(
                "[RAGAS ERROR]",
                repr(e)
            )

    #
    # =====================================================
    # Resultado final
    # =====================================================
    #

    resultado = dict(
        resultado_rag
    )

    resultado["answer"] = texto_respuesta

    resultado["ragas"] = metricas_ragas

    return resultado


def generar_respuesta(
    resultado_rag,
    pregunta,
    respuesta_llm,
    referencia=None,
    calcular_ragas=False
):

    return procesar_respuesta(
        resultado_rag=resultado_rag,
        pregunta=pregunta,
        respuesta_llm=respuesta_llm,
        referencia=referencia,
        calcular_ragas=calcular_ragas
    )
