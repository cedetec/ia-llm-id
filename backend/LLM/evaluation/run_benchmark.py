# LLM/evaluation/run_benchmark.py

import app.startup as startup

from LLM.evaluation.evaluation_runner import (
    EvaluationRunner
)


def main():

    #
    # Verificar RAG Nomic
    #

    if startup.rag_nomic is None:

        raise RuntimeError(
            "El RAG Nomic no está disponible."
        )

    #
    # Verificar RAG EmbeddingGemma
    #

    if startup.rag_gemma is None:

        raise RuntimeError(
            "El RAG EmbeddingGemma no está disponible."
        )

    print()
    print("=" * 80)
    print("INICIO DEL BENCHMARK")
    print("=" * 80)

    print(
        "RAG Nomic:",
        startup.rag_nomic
    )

    print(
        "RAG EmbeddingGemma:",
        startup.rag_gemma
    )

    print("=" * 80)

    #
    # Crear runner
    #

    runner = EvaluationRunner(

        rag_nomic=startup.rag_nomic,

        rag_gemma=startup.rag_gemma,

        dataset="LLM/evaluation/evaluation_dataset.json"

    )

    #
    # Ejecutar benchmark
    #

    resultados = runner.ejecutar()

    #
    # Resumen final
    #

    print()
    print("=" * 80)
    print("BENCHMARK FINALIZADO")
    print("=" * 80)

    print(
        "Cantidad de resultados:",
        len(resultados)
    )

    print("=" * 80)

    return resultados


if __name__ == "__main__":

    main()
