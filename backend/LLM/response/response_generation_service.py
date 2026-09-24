# LLM/response/response_generation_service.py

from LLM.translators.translation_policy import (
    usar_traduccion
)

from LLM.translators.argos_translator import (
    translator
)

from LLM.evaluation.ragas_metrics import (
    RagasMetrics
)


def generar_respuesta(

    rag_chain,

    pregunta,

    referencia=None,

    calcular_ragas=False

):

    #
    # Traducir solo si el modelo lo requiere.
    #

    if usar_traduccion():

        pregunta_llm = translator.es_a_en(
            pregunta
        )

    else:

        pregunta_llm = pregunta

    print(

        "[LLM QUESTION]",

        pregunta_llm

    )

    #
    # Ejecutar el RAG usando la pregunta correspondiente.
    #

    respuesta = rag_chain.invoke(

        pregunta_llm

    )

    print("\n================ MODELO ACTUAL ================\n")

    try:

        print(
            "LLM object:",
            rag_chain.llm
        )

        print(
            "LLM model:",
            getattr(
                rag_chain.llm,
                "model",
                "NO DISPONIBLE"
            )
        )

    except Exception as e:

        print(
            "[MODEL DEBUG ERROR]",
            repr(e)
        )

    print(
        "\n================ RESPUESTA GENERADA ================\n"
    )

    print(
        respuesta["answer"]
    )

    #
    # Traducir la respuesta nuevamente al español
    # solo cuando corresponda.
    #

    if usar_traduccion():

        print(
            "[ANTES TRADUCCION]",
            respuesta["answer"]
        )

        respuesta["answer"] = translator.en_a_es(
            respuesta["answer"]
        )

        print(
            "[DESPUES TRADUCCION]",
            respuesta["answer"]
        )

    #
    # Métricas RAGAS.
    #
    # Por defecto NO se calculan durante /chat.
    # Se habilitan solamente desde el flujo
    # de evaluación dedicado usando calcular_ragas=True.
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

            ragas = RagasMetrics()

            contextos = respuesta.get(
                "contextos_ragas",
                respuesta.get(
                    "context",
                    []
                )
            )

            metricas_ragas = ragas.evaluar(

                pregunta=pregunta,

                respuesta=respuesta["answer"],

                contextos=contextos,

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
    # Exponer las métricas RAGAS en la respuesta.
    #

    respuesta["ragas"] = metricas_ragas

    print(
        "[RAG]",
        {
            "chunks": len(
                respuesta["context"]
            )
        }
    )

    for i, doc in enumerate(
        respuesta["context"]
    ):

        print(
            "[RAG CHUNK]",
            {
                "pagina": doc.metadata.get(
                    "pagina"
                ),

                "longitud": len(
                    doc.page_content
                )
            }
        )

    for i, doc in enumerate(
        respuesta["context"]
    ):

        print("=" * 80)

        print(
            f"Documento {i}"
        )

        print(
            "Documento:",
            doc.metadata.get(
                "documento"
            )
        )

        print(
            "Página:",
            doc.metadata.get(
                "pagina"
            )
        )

        print(
            "Longitud:",
            len(
                doc.page_content
            )
        )

        for campo in (

            "seccion",

            "titulo_padre",

            "titulo_hijo",

            "subtitulo"

        ):

            if not doc.metadata.get(campo):

                print(
                    f"[WARNING] {campo} vacío"
                )

        if not doc.page_content.strip():

            print(
                "[WARNING] Chunk vacío."
            )

        print("\nContenido:\n")

        print(
            doc.page_content
        )

    print(
        "\n================ RESPUESTA DEL LLM ================\n"
    )

    print(
        respuesta["answer"]
    )

    return respuesta
