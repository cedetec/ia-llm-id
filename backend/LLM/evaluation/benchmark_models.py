# LLM/evaluation/benchmark_models.py

from dataclasses import dataclass

from LLM.rag.rag_service import RAGService


MODELOS = [

    "mistral:latest",

    "qwen2.5:latest",

    "deepseek-r1:8b",

    "gemma4:e2b"

]


@dataclass
class BenchmarkResult:

    modelo: str

    pregunta: str

    respuesta: str

    retrieval: dict

    rerank: dict

    answer: dict

    context_text: str

    contextos_ragas: list[str]


def ejecutar_modelo(

    modelo,

    pregunta,

    documento,

    documentos_relevantes=None,

    rag_service: RAGService = None

):

    rag_service.cambiar_modelo(modelo)

    respuesta = rag_service.invoke(

        pregunta,

        documento=documento,

        documentos_relevantes=documentos_relevantes

    )

    print("\n===== RESPUESTA RAG =====")

    print(respuesta.keys())

    print("\n===== MÉTRICAS =====")

    print(respuesta["metricas"])

    return BenchmarkResult(

        modelo=modelo,

        pregunta=pregunta,

        respuesta=respuesta["answer"],

        retrieval=respuesta["metricas"]["retrieval"],

        rerank=respuesta["metricas"]["rerank"],

        answer=respuesta["metricas"]["respuesta"],

        context_text=respuesta["context_text"],

        contextos_ragas=respuesta["contextos_ragas"]

    )