# LLM/evaluation/export_comparison.py

import json

from pathlib import Path


RESULTADOS = Path(
    "evaluation/results/benchmark_repaired.json"
)

SALIDA = Path(
    "evaluation/results/comparacion_rag_llm_repaired.json"
)


def main():

    with RESULTADOS.open(
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    resultados = []

    for resultado in datos:

        resultados.append({

            "rag":
                resultado["rag"],

            "modelo_llm":
                resultado["modelo"],

            "pregunta":
                resultado["pregunta"],

            "documento":
                resultado["documento"],

            "respuesta":
                resultado["respuesta"],

            "latencia":
                resultado["latencia"],

            "memoria":
                resultado["memoria"],

            "sustainability":
                resultado["sustainability"],

            "retrieval":
                resultado["retrieval"],

            "rerank":
                resultado["rerank"],

            "respuesta_metricas":
                resultado["respuesta_metricas"],

            "metricas_ragas":
                resultado["ragas"]

        })

    with SALIDA.open(
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(

            resultados,

            archivo,

            indent=4,

            ensure_ascii=False,

            allow_nan=False

        )

    print(
        "Registros exportados:",
        len(resultados)
    )

    print(
        "Archivo:",
        SALIDA
    )


if __name__ == "__main__":

    main()