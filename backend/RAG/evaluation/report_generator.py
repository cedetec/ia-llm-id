# LLM/evaluation/report_generator.py

import csv
import json

from pathlib import Path

from openpyxl import Workbook


COLUMNAS = [

    "RAG",
    "Modelo",
    "Documento",
    "Pregunta",

    "Latencia(ms)",
    "RAM(MB)",

    "Chunks",
    "Docs",

    "Score Retrieval",
    "Score Rerank",

    "Tokens",

    "Context Precision",
    "Context Recall",
    "Faithfulness",
    "Answer Relevance"

]


def _valor_ragas(valor):

    if valor is None:
        return ""

    return valor


def _fila_resultado(resultado):

    retrieval = resultado.get(
        "retrieval",
        {}
    )

    rerank = resultado.get(
        "rerank",
        {}
    )

    respuesta = resultado.get(
        "respuesta_metricas",
        {}
    )

    ragas = resultado.get(
        "ragas",
        {}
    )

    return [

        resultado.get("rag"),

        resultado.get("modelo"),

        resultado.get("documento"),

        resultado.get("pregunta"),

        resultado.get(
            "latencia",
            {}
        ).get("total"),

        resultado.get(
            "memoria",
            {}
        ).get("ram_delta_mb"),

        retrieval.get(
            "chunks"
        ),

        retrieval.get(
            "documentos_distintos"
        ),

        retrieval.get(
            "score_promedio"
        ),

        rerank.get(
            "score_mean"
        ),

        respuesta.get(
            "tokens"
        ),

        _valor_ragas(
            ragas.get(
                "context_precision"
            )
        ),

        _valor_ragas(
            ragas.get(
                "context_recall"
            )
        ),

        _valor_ragas(
            ragas.get(
                "faithfulness"
            )
        ),

        _valor_ragas(
            ragas.get(
                "answer_relevancy"
            )
        )

    ]


def _markdown_resultado(resultado):

    retrieval = resultado.get(
        "retrieval",
        {}
    )

    rerank = resultado.get(
        "rerank",
        {}
    )

    respuesta = resultado.get(
        "respuesta_metricas",
        {}
    )

    ragas = resultado.get(
        "ragas",
        {}
    )

    return f"""## {resultado.get("rag")} — {resultado.get("modelo")}

- Documento: {resultado.get("documento")}
- Pregunta: {resultado.get("pregunta")}
- Latencia: {resultado.get("latencia", {}).get("total")} ms
- RAM: {resultado.get("memoria", {}).get("ram_delta_mb")} MB
- Chunks recuperados: {retrieval.get("chunks")}
- Documentos distintos: {retrieval.get("documentos_distintos")}
- Score Retrieval: {retrieval.get("score_promedio")}
- Score Rerank: {rerank.get("score_mean")}
- Tokens respuesta: {respuesta.get("tokens")}
- Context Precision: {ragas.get("context_precision")}
- Context Recall: {ragas.get("context_recall")}
- Faithfulness: {ragas.get("faithfulness")}
- Answer Relevance: {ragas.get("answer_relevancy")}

"""


class ReportGenerator:

    @staticmethod
    def generar(

        resultados,

        carpeta: Path,

        nombre_base="benchmark",

        nombre_markdown=None,

        incluir_json=True

    ):

        carpeta.mkdir(
            parents=True,
            exist_ok=True
        )

        #
        # JSON
        #

        if incluir_json:

            with open(

                carpeta / f"{nombre_base}.json",

                "w",

                encoding="utf8"

            ) as f:

                json.dump(

                    resultados,

                    f,

                    indent=4,

                    ensure_ascii=False

                )

        #
        # CSV
        #

        with open(

            carpeta / f"{nombre_base}.csv",

            "w",

            newline="",

            encoding="utf8"

        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                COLUMNAS
            )

            for resultado in resultados:

                writer.writerow(
                    _fila_resultado(
                        resultado
                    )
                )

        #
        # Excel
        #

        wb = Workbook()

        ws = wb.active

        ws.title = "Benchmark"

        ws.append(
            COLUMNAS
        )

        for resultado in resultados:

            ws.append(
                _fila_resultado(
                    resultado
                )
            )

        ws.freeze_panes = "A2"

        ws.auto_filter.ref = (
            ws.dimensions
        )

        for columna in ws.columns:

            longitud = 0

            letra = (
                columna[0].column_letter
            )

            for celda in columna:

                if celda.value is not None:

                    longitud = max(

                        longitud,

                        len(
                            str(
                                celda.value
                            )
                        )

                    )

            ws.column_dimensions[
                letra
            ].width = min(
                longitud + 2,
                45
            )

        wb.save(

            carpeta /
            f"{nombre_base}.xlsx"

        )

        #
        # Markdown
        #

        if nombre_markdown is None:

            nombre_markdown = (
                f"{nombre_base}.md"
            )

        with open(

            carpeta /
            nombre_markdown,

            "w",

            encoding="utf8"

        ) as f:

            titulo = (
                "Benchmark de modelos"
                if nombre_base == "benchmark"
                else "Benchmark final"
            )

            f.write(
                f"# {titulo}\n\n"
            )

            f.write(
                f"Total de evaluaciones: "
                f"{len(resultados)}\n\n"
            )

            for resultado in resultados:

                f.write(
                    _markdown_resultado(
                        resultado
                    )
                )