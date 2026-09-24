# LLM/evaluation/evaluation_pipeline.py

from datetime import datetime

from LLM.evaluation.benchmark_models import (
    MODELOS,
    ejecutar_modelo
)

from LLM.evaluation.latency_metrics import (
    LatencyMetrics
)

from LLM.evaluation.memory_metrics import (
    MemoryMetrics
)


from LLM.evaluation.sustainability_metrics import (
    SustainabilityMetrics
)


class EvaluationPipeline:

    def __init__(
        self,
        rag_nomic,
        rag_gemma
    ):

        self.rag_nomic = rag_nomic

        self.rag_gemma = rag_gemma

    def ejecutar(
        self,
        pregunta,
        documento,
        documentos_relevantes=None,
        combinaciones_pendientes=None
    ):

        resultados = []

        for rag_nombre, rag_service in (

            ("NOMIC", self.rag_nomic),

            ("EMBEDDINGGEMMA", self.rag_gemma)

        ):

            print(
                f"\n========== RAG: {rag_nombre} ==========\n"
            )

            if rag_service is None:

                print(
                    f"[WARNING] {rag_nombre} no está disponible."
                )

                continue

            for modelo in MODELOS:

                if (
                    combinaciones_pendientes is not None
                    and (rag_nombre, modelo)
                    not in combinaciones_pendientes
                ):

                    print(
                        f"[RESUME] Omitiendo "
                        f"{rag_nombre} | {modelo}"
                    )

                    continue

                print(
                    f"\n========== MODELO: {modelo} ==========\n"
                )

                sustainability = SustainabilityMetrics()

                sustainability.iniciar()

                latency = LatencyMetrics()

                memory = MemoryMetrics()

                latency.iniciar("total")

                memory.iniciar()

                try:

                    resultado = ejecutar_modelo(

                        modelo=modelo,

                        pregunta=pregunta,

                        documento=documento,

                        documentos_relevantes=documentos_relevantes,

                        rag_service=rag_service

                    )

                except Exception as e:

                    print(
                        f"[ERROR] Falló "
                        f"{rag_nombre} | {modelo}:",
                        repr(e)
                    )

                    continue

                finally:

                    sustainability.terminar()

                    memory.terminar()

                    latency.terminar("total")

                resultados.append(

                    {

                        "rag": rag_nombre,

                        "modelo": modelo,

                        "pregunta": pregunta,

                        "documento": documento,

                        "respuesta": resultado.respuesta,

                        "timestamp":
                            datetime.now().isoformat(),

                        "latencia":
                            latency.resumen(),

                        "memoria":
                            memory.resumen(),

                        "sustainability":
                            sustainability.resumen(),

                        "retrieval":
                            resultado.retrieval,

                        "rerank":
                            resultado.rerank,

                        "respuesta_metricas":
                            resultado.answer,

                        "context_text":
                            resultado.context_text,

                        "contextos_ragas":
                            resultado.contextos_ragas

                    }

                )

        print("\n===== RESULTADOS =====")

        for r in resultados:

            print(r)

        return resultados
