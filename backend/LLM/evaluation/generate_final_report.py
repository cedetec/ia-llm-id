# LLM/evaluation/generate_final_report.py

import json

from pathlib import Path

from LLM.evaluation.report_generator import (
    ReportGenerator
)


RESULTADOS = Path(
    "evaluation/results/benchmark_repaired.json"
)

CARPETA_SALIDA = Path(
    "evaluation/results"
)


def main():

    with RESULTADOS.open(
        "r",
        encoding="utf-8"
    ) as archivo:

        resultados = json.load(
            archivo
        )

    print()
    print("=" * 80)
    print("GENERACIÓN DEL INFORME FINAL")
    print("=" * 80)

    print(
        "Archivo fuente:",
        RESULTADOS
    )

    print(
        "Registros:",
        len(resultados)
    )

    ReportGenerator.generar(

        resultados,

        CARPETA_SALIDA,

        nombre_base="benchmark_final",

        nombre_markdown="benchmark_final.md",

        incluir_json=False

    )

    print()
    print("Archivos generados:")

    print(
        CARPETA_SALIDA /
        "benchmark_final.xlsx"
    )

    print(
        CARPETA_SALIDA /
        "benchmark_final.csv"
    )

    print(
        CARPETA_SALIDA /
        "benchmark_final.md"
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()