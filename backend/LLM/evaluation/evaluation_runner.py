# LLM/evaluation/evaluation_runner.py

import json

from pathlib import Path

from LLM.evaluation.ground_truth_loader import (
    GroundTruthLoader
)

from LLM.evaluation.evaluation_pipeline import (
    EvaluationPipeline
)

from LLM.evaluation.benchmark_models import (
    MODELOS
)

from LLM.evaluation.model_ranking import (
    ModelRanking
)

from LLM.evaluation.report_generator import (
    ReportGenerator
)


class EvaluationRunner:

    def __init__(

        self,

        rag_nomic,

        rag_gemma,

        dataset="LLM/evaluation/evaluation_dataset.json"

    ):

        self.pipeline = EvaluationPipeline(

            rag_nomic,

            rag_gemma

        )

        self.loader = GroundTruthLoader(
            dataset
        )

        self.ranking = (
            ModelRanking()
        )

    def _cargar_resultados_existentes(self):

        path = Path(
            "evaluation/results/benchmark.json"
        )

        if not path.exists():
            return []

        try:

            with open(
                path,
                "r",
                encoding="utf8"
            ) as f:

                datos = json.load(f)

            if not isinstance(datos, list):
                return []

            return datos

        except Exception as e:

            print(
                "[WARNING] No se pudieron cargar "
                "los resultados existentes:",
                repr(e)
            )

            return []

    def ejecutar(self):

        datos = self.loader.cargar()

        resultados = self._cargar_resultados_existentes()

        existentes = {
            (
                r.get("rag"),
                r.get("modelo"),
                r.get("pregunta"),
                r.get("documento")
            )
            for r in resultados
        }

        print(
            f"[RESUME] Resultados existentes: "
            f"{len(resultados)}"
        )

        for caso in datos:

            print()

            print("=" * 80)

            print(
                "Documento:",
                caso["documento"]
            )

            print(
                "Pregunta:",
                caso["pregunta"]
            )

            print("=" * 80)

            #
            # Ejecutar benchmark para TODOS
            # los modelos.
            #

            combinaciones_pendientes = {

                (
                    rag,
                    modelo
                )

                for rag in (
                    "NOMIC",
                    "EMBEDDINGGEMMA"
                )

                for modelo in MODELOS

                if (
                    rag,
                    modelo,
                    caso["pregunta"],
                    caso["documento"]
                ) not in existentes

            }

            if not combinaciones_pendientes:

                print(
                    "[RESUME] Caso ya completo. "
                    "Se omite."
                )

                continue

            print(
                "[RESUME] Combinaciones pendientes:",
                len(combinaciones_pendientes)
            )

            benchmark = self.pipeline.ejecutar(

                pregunta=caso["pregunta"],

                documento=caso["documento"],

                documentos_relevantes=caso.get(
                    "documentos_relevantes"
                ),

                combinaciones_pendientes=(
                    combinaciones_pendientes
                )

            )

            #
            # Cada modelo obtiene
            # sus propias métricas.
            #

            for resultado in benchmark:

                #
                # ============================
                # MÉTRICAS RAGAS se calculan posteriormente
                # ============================
                #

                ragas = {
                    "context_precision": None,
                    "context_recall": None,
                    "faithfulness": None,
                    "answer_relevancy": None
                }

                #
                # Guardar documento.
                #

                resultado["documento"] = (
                    caso["documento"]
                )

                #
                # Guardar métricas RAGAS.
                #

                resultado["precision"] = (
                    ragas["context_precision"]
                )

                resultado["recall"] = (
                    ragas["context_recall"]
                )

                resultado["faithfulness"] = (
                    ragas["faithfulness"]
                )

                resultado["answer_relevance"] = (
                    ragas["answer_relevancy"]
                )

                resultado["ragas"] = ragas

                print(
                    "\n===== MÉTRICAS RAGAS ====="
                )

                print(
                    "Context Precision:",
                    resultado["precision"]
                )

                print(
                    "Context Recall   :",
                    resultado["recall"]
                )

                print(
                    "Faithfulness     :",
                    resultado["faithfulness"]
                )

                print(
                    "Answer Relevance :",
                    resultado["answer_relevance"]
                )

                print(
                    "\n===== RESULTADO FINAL ====="
                )

                print(
                    resultado
                )

                resultados.append(
                    resultado
                )

            ReportGenerator.generar(
                resultados,
                Path("evaluation/results")
            )

            print(
                "[CHECKPOINT] Resultados guardados:",
                len(resultados)
            )

        #
        # Ranking global
        #

        ranking = self.ranking.ordenar(
            resultados
        )

        #
        # Reportes
        #

        carpeta = Path(
            "evaluation/results"
        )

        carpeta.mkdir(

            parents=True,

            exist_ok=True

        )

        ReportGenerator.generar(

            ranking,

            carpeta

        )

        return ranking
