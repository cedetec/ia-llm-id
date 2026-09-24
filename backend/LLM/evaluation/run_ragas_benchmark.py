# LLM/evaluation/run_ragas_benchmark.py

import argparse
import copy
import json
import math
import time

from pathlib import Path

from LLM.evaluation.ragas_metrics import (
    RagasMetrics
)

from LLM.evaluation.report_generator import (
    ReportGenerator
)


# ============================================================
# RUTAS
# ============================================================

BENCHMARK = Path(
    "/app/evaluation/results/benchmark.json"
)

REFERENCIAS = Path(
    "/app/LLM/evaluation/evaluation_dataset_ragas.json"
)

SALIDA = Path(
    "/app/evaluation/results/benchmark_ragas.json"
)

LOG = Path(
    "/app/evaluation/results/ragas_benchmark_log.json"
)


# ============================================================
# MÉTRICAS
# ============================================================

NOMBRES_METRICAS = (

    "context_precision",

    "context_recall",

    "faithfulness",

    "answer_relevancy"

)


# ============================================================
# UTILIDADES
# ============================================================

def cargar_json(ruta):

    if not ruta.exists():

        raise FileNotFoundError(
            f"No existe: {ruta}"
        )

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


def guardar_json(
    ruta,
    datos
):

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            indent=4,
            ensure_ascii=False,
            allow_nan=False
        )


def limpiar_valor(valor):

    if isinstance(
        valor,
        float
    ):

        if (
            math.isnan(valor)
            or math.isinf(valor)
        ):

            return None

    return valor


def limpiar_metricas(metricas):

    resultado = {}

    for nombre in NOMBRES_METRICAS:

        resultado[nombre] = limpiar_valor(
            metricas.get(
                nombre
            )
        )

    return resultado


def metricas_pendientes(
    registro,
    metrica_forzada=None
):

    ragas = registro.get(
        "ragas",
        {}
    )

    if metrica_forzada is not None:

        if (
            ragas.get(
                metrica_forzada
            )
            is None
        ):

            return [
                metrica_forzada
            ]

        return []

    return [

        nombre

        for nombre in NOMBRES_METRICAS

        if ragas.get(nombre) is None

    ]


def construir_referencias(dataset):

    referencias = {}

    for caso in dataset:

        documento = caso.get(
            "documento"
        )

        pregunta = caso.get(
            "pregunta"
        )

        respuesta = caso.get(
            "respuesta"
        )

        if not documento:
            raise ValueError(
                "Referencia sin documento."
            )

        if not pregunta:
            raise ValueError(
                "Referencia sin pregunta."
            )

        if not respuesta or not respuesta.strip():
            raise ValueError(
                "Referencia vacía para: "
                f"{pregunta}"
            )

        clave = (
            documento,
            pregunta
        )

        if clave in referencias:

            raise ValueError(
                "Referencia duplicada para: "
                f"{clave}"
            )

        referencias[clave] = respuesta

    return referencias


# ============================================================
# EVALUACIÓN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Evalúa las respuestas ya generadas "
            "del benchmark con RAGAS."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Procesar como máximo N registros "
            "pendientes."
        )
    )

    parser.add_argument(
        "--metric",
        choices=NOMBRES_METRICAS,
        default=None,
        help=(
            "Evaluar únicamente esta métrica."
        )
    )

    parser.add_argument(
        "--record",
        type=int,
        default=None,
        help=(
            "Evaluar únicamente este registro "
            "(1-48)."
        )
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print("BENCHMARK RAGAS")
    print("=" * 80)

    # --------------------------------------------------------
    # Cargar benchmark original.
    # --------------------------------------------------------

    benchmark = cargar_json(
        BENCHMARK
    )

    if not isinstance(
        benchmark,
        list
    ):

        raise ValueError(
            "benchmark.json no contiene una lista."
        )

    if len(benchmark) != 48:

        raise ValueError(
            "Se esperaban 48 resultados y "
            f"se encontraron {len(benchmark)}."
        )

    print(
        "Resultados benchmark:",
        len(benchmark)
    )

    # --------------------------------------------------------
    # Cargar referencias.
    # --------------------------------------------------------

    dataset = cargar_json(
        REFERENCIAS
    )

    if not isinstance(
        dataset,
        list
    ):

        raise ValueError(
            "evaluation_dataset_ragas.json "
            "no contiene una lista."
        )

    if len(dataset) != 6:

        raise ValueError(
            "Se esperaban 6 referencias y "
            f"se encontraron {len(dataset)}."
        )

    referencias = construir_referencias(
        dataset
    )

    print(
        "Referencias RAGAS:",
        len(referencias)
    )

    # --------------------------------------------------------
    # Recuperar checkpoint si existe.
    #
    # El benchmark.json ORIGINAL nunca se modifica.
    # --------------------------------------------------------

    if SALIDA.exists():

        print(
            "\n[RESUME] Cargando checkpoint:",
            SALIDA
        )

        resultados = cargar_json(
            SALIDA
        )

        if len(resultados) != 48:

            raise ValueError(
                "El checkpoint no contiene "
                "exactamente 48 resultados."
            )

    else:

        resultados = copy.deepcopy(
            benchmark
        )

    # --------------------------------------------------------
    # Asegurar estructura RAGAS.
    # --------------------------------------------------------

    for registro in resultados:

        registro.setdefault(
            "ragas",
            {
                nombre: None
                for nombre in NOMBRES_METRICAS
            }
        )

    # --------------------------------------------------------
    # Crear evaluador RAGAS UNA sola vez.
    # --------------------------------------------------------

    ragas = RagasMetrics()

    pendientes = [

        indice

        for indice, registro
        in enumerate(
            resultados
        )

        if metricas_pendientes(
            registro,
            args.metric
        )

    ]

    if args.record is not None:

        if (
            args.record < 1
            or args.record > len(resultados)
        ):
            raise ValueError(
                "--record debe estar entre 1 y "
                f"{len(resultados)}."
            )

        indice_record = args.record - 1

        if indice_record not in pendientes:

            print(
                f"[INFO] El registro {args.record} "
                "no tiene métricas pendientes "
                "para esta ejecución."
            )

            pendientes = []

        else:

            pendientes = [
                indice_record
            ]

        print(
            "Registro solicitado:",
            args.record
        )

    print(
        "Registros pendientes:",
        len(pendientes)
    )

    if args.limit is not None:

        if args.limit <= 0:

            raise ValueError(
                "--limit debe ser mayor que 0."
            )

        pendientes = pendientes[
            :args.limit
        ]

        print(
            "Límite solicitado:",
            args.limit
        )

    print()

    log = []

    # --------------------------------------------------------
    # Procesar registros.
    # --------------------------------------------------------

    for posicion, indice in enumerate(
        pendientes,
        start=1
    ):

        registro = resultados[
            indice
        ]

        documento = registro.get(
            "documento"
        )

        pregunta = registro.get(
            "pregunta"
        )

        respuesta = registro.get(
            "respuesta",
            ""
        )

        clave = (
            documento,
            pregunta
        )

        referencia = referencias.get(
            clave
        )

        print()
        print("=" * 80)
        print(
            f"REGISTRO {indice + 1}/48 "
            f"({posicion}/{len(pendientes)})"
        )
        print("=" * 80)

        print(
            "RAG:",
            registro.get("rag")
        )

        print(
            "Modelo:",
            registro.get("modelo")
        )

        print(
            "Pregunta:",
            pregunta
        )

        print(
            "Chunks:",
            len(
                registro.get(
                    "contextos_ragas",
                    []
                )
            )
        )

        if referencia is None:

            error = (
                "No existe referencia para "
                f"{clave}"
            )

            print(
                "[ERROR]",
                error
            )

            log.append(
                {
                    "registro": indice + 1,
                    "rag": registro.get("rag"),
                    "modelo": registro.get("modelo"),
                    "documento": documento,
                    "pregunta": pregunta,
                    "resultado": "error",
                    "error": error
                }
            )

            continue

        contextos = registro.get(
            "contextos_ragas",
            []
        )

        if not isinstance(
            contextos,
            list
        ):

            error = (
                "contextos_ragas no es una lista."
            )

            print(
                "[ERROR]",
                error
            )

            log.append(
                {
                    "registro": indice + 1,
                    "rag": registro.get("rag"),
                    "modelo": registro.get("modelo"),
                    "documento": documento,
                    "pregunta": pregunta,
                    "resultado": "error",
                    "error": error
                }
            )

            continue

        pendientes_registro = metricas_pendientes(

            registro,

            args.metric

        )

        print(
            "[RAGAS] Métricas pendientes:",
            ", ".join(
                pendientes_registro
            )
        )

        for nombre in pendientes_registro:

            print()
            print(
                f"===== RAGAS: {nombre} ====="
            )

            inicio = time.perf_counter()

            try:

                valor = ragas.evaluar_metrica(

                    nombre=nombre,

                    pregunta=pregunta,

                    respuesta=respuesta,

                    contextos=contextos,

                    referencia=referencia

                )

                registro.setdefault(
                    "ragas",
                    {}
                )

                registro["ragas"][
                    nombre
                ] = limpiar_valor(
                    valor
                )

                duracion = (
                    time.perf_counter()
                    - inicio
                )

                log.append(
                    {
                        "registro": indice + 1,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            documento,

                        "pregunta":
                            pregunta,

                        "metrica":
                            nombre,

                        "resultado":
                            "ok",

                        "valor":
                            registro["ragas"][
                                nombre
                            ],

                        "tiempo_s":
                            round(
                                duracion,
                                2
                            )
                    }
                )

            except Exception as e:

                duracion = (
                    time.perf_counter()
                    - inicio
                )

                registro.setdefault(
                    "ragas",
                    {}
                )

                registro["ragas"][
                    nombre
                ] = None

                print(
                    "[RAGAS ERROR]",
                    type(e).__name__,
                    str(e)
                )

                log.append(
                    {
                        "registro": indice + 1,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            documento,

                        "pregunta":
                            pregunta,

                        "metrica":
                            nombre,

                        "resultado":
                            "error",

                        "error":
                            str(e),

                        "tiempo_s":
                            round(
                                duracion,
                                2
                            )
                    }
                )

            # ---------------------------------------------
            # CHECKPOINT POR MÉTRICA
            # ---------------------------------------------

            guardar_json(
                SALIDA,
                resultados
            )

            guardar_json(
                LOG,
                log
            )

            print(
                "\n[CHECKPOINT] "
                f"Registro {indice + 1}/48 "
                f"— métrica {nombre} guardada."
            )

        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        guardar_json(
            SALIDA,
            resultados
        )

        guardar_json(
            LOG,
            log
        )

        metricas_totales = (
            len(resultados)
            * len(NOMBRES_METRICAS)
        )

        metricas_completadas = sum(
            1
            for registro in resultados
            for nombre in NOMBRES_METRICAS
            if registro.get(
                "ragas",
                {}
            ).get(nombre) is not None
        )

        print()
        print(
            "[CHECKPOINT]",
            f"{metricas_completadas}/"
            f"{metricas_totales} métricas completas."
        )

    # --------------------------------------------------------
    # Reportes finales.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("GENERANDO REPORTES RAGAS")
    print("=" * 80)

    ReportGenerator.generar(

        resultados,

        Path(
            "/app/evaluation/results"
        ),

        nombre_base="benchmark_ragas",

        incluir_json=True

    )

    # --------------------------------------------------------
    # Resumen.
    # --------------------------------------------------------

    metricas_totales = (
        len(resultados)
        * len(NOMBRES_METRICAS)
    )

    metricas_completadas = sum(

        1

        for registro in resultados

        for nombre in NOMBRES_METRICAS

        if registro.get(
            "ragas",
            {}
        ).get(nombre) is not None

    )

    print(
        "Métricas RAGAS completadas:",
        f"{metricas_completadas}/"
        f"{metricas_totales}"
    )

    print(
        "Métricas RAGAS pendientes:",
        metricas_totales
        - metricas_completadas
    )

    print()
    print(
        "Salida JSON:",
        SALIDA
    )

    print(
        "Log:",
        LOG
    )

    print("=" * 80)


if __name__ == "__main__":

    main()
