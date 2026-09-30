#!/usr/bin/env bash

set -euo pipefail

# ==============================================================
# BENCHMARK 10 CONSULTAS
#
# 10 consultas
# x 2 embeddings
# x 4 modelos LLM
# = 80 evaluaciones RAGAS
#
# Ejecutar desde:
# backend/
# ==============================================================

OUTPUT="/app/evaluation/results/comparacion_10_consultas_rag_llm.json"

echo "=============================================================="
echo " BENCHMARK 10 CONSULTAS"
echo "=============================================================="

docker exec -i chatbot_backend python - <<'PY'

import json
from pathlib import Path

from RAG.startup.startup_service import (
    crear_rag_service
)

from RAG.evaluation.benchmark_models import (
    ejecutar_modelo,
    MODELOS
)

from RAG.evaluation.ragas_metrics import (
    RagasMetrics
)

from app.core.paths import (
    CHROMA_NOMIC_DIR,
    CHROMA_GEMMA_DIR
)


# ==============================================================
# CONSULTAS
# ==============================================================

CONSULTAS = [

    {
        "id": 1,

        "documento":
            "ACCESO-A-EMBARCACIONES-PARA-INVESTIGACIÓN-CIENTÍFICA-2022.pdf",

        "pregunta":
            "¿Cuál es el objetivo general del concurso?",

        "referencia":
            "El objetivo de la línea de financiamiento para acceso a embarcaciones "
            "es apoyar el desarrollo de proyectos de investigación, con financiamiento "
            "público vigente, en cualquier área del conocimiento en que este uso sea "
            "requerido para el cumplimiento de objetivos científicos dentro de los proyectos."
    },

    {
        "id": 2,

        "documento":
            "ACCESO-A-EMBARCACIONES-PARA-INVESTIGACIÓN-CIENTÍFICA-2022.pdf",

        "pregunta":
            "¿Cuáles son los objetivos específicos del concurso?",

        "referencia":
            "Los objetivos específicos son facilitar la realización de investigación "
            "científica y tecnológica para la cual es imprescindible el uso de "
            "embarcaciones; incentivar el entrenamiento de investigadores recientemente "
            "formados y la formación de estudiantes de pre y postgrado incluidos en el "
            "proyecto albergante mediante su participación activa en el equipo que accederá "
            "al uso de la embarcación; y promover redes internacionales de cooperación "
            "con otros equipos de investigación extranjeros similares."
    },

    {
        "id": 3,

        "documento":
            "ACCESO-A-EMBARCACIONES-PARA-INVESTIGACIÓN-CIENTÍFICA-2022.pdf",

        "pregunta":
            "¿Qué requisitos debe cumplir el proyecto albergante para postular al concurso?",

        "referencia":
            "El o los proyectos albergantes deben tener una vigencia mínima hasta "
            "diciembre de 2023 y contar con financiamiento para el posterior análisis "
            "de las muestras y/o datos obtenidos, así como para su utilización en la "
            "puesta a prueba de hipótesis y el cumplimiento de objetivos precisos."
    },

    {
        "id": 4,

        "documento":
            "ACCESO-A-EMBARCACIONES-PARA-INVESTIGACIÓN-CIENTÍFICA-2022.pdf",

        "pregunta":
            "¿Cuál es el monto máximo de financiamiento y cuál es la duración del proyecto?",

        "referencia":
            "ANID financiará los proyectos con un tope de 416.000.000 de pesos, "
            "entregados en una única cuota a la Institución Beneficiaria según la "
            "disponibilidad presupuestaria del servicio. El proyecto tendrá una duración "
            "de 12 meses."
    },

    {
        "id": 5,

        "documento":
            "ACCESO-A-EMBARCACIONES-PARA-INVESTIGACIÓN-CIENTÍFICA-2022.pdf",

        "pregunta":
            "¿Qué condiciones básicas de admisibilidad se exigen para la postulación?",

        "referencia":
            "Entre las condiciones básicas de admisibilidad se exige que el coordinador "
            "o coordinadora del proyecto sea chileno o extranjero con residencia en Chile, "
            "que los formularios se presenten completos y correctamente y que exista al "
            "menos un proyecto albergante financiado con fondos públicos y con vigencia suficiente."
    },

    {
        "id": 6,

        "documento":
            "ASIGNACIÓN-DE-TIEMPO-OCEANOGRÁFICO-CABO-DE-HORNOS-2020.pdf",

        "pregunta":
            "¿Cuál es el objetivo general del concurso?",

        "referencia":
            "El concurso tiene por objetivo asignar tiempos de uso del Buque Cabo de "
            "Hornos durante el período comprendido entre el 9 y el 28 de noviembre de 2020."
    },

    {
        "id": 7,

        "documento":
            "ASIGNACIÓN-DE-TIEMPO-OCEANOGRÁFICO-CABO-DE-HORNOS-2020.pdf",

        "pregunta":
            "¿Qué objetivo de investigación debe justificar el uso del Buque Cabo de Hornos?",

        "referencia":
            "La postulación debe justificar la necesidad del uso del buque para realizar "
            "investigación científica y tecnológica que requiera esta infraestructura y "
            "equipamiento mayor."
    },

    {
        "id": 8,

        "documento":
            "ASIGNACIÓN-DE-TIEMPO-OCEANOGRÁFICO-CABO-DE-HORNOS-2020.pdf",

        "pregunta":
            "¿Qué requisito de vigencia debe tener el proyecto albergante para la postulación?",

        "referencia":
            "Debe existir al menos un proyecto albergante financiado con fondos públicos "
            "con una duración o vigencia de al menos hasta junio de 2021."
    },

    {
        "id": 9,

        "documento":
            "ASIGNACIÓN-DE-TIEMPO-OCEANOGRÁFICO-CABO-DE-HORNOS-2020.pdf",

        "pregunta":
            "¿Qué criterios utiliza la Comisión para determinar la factibilidad de los proyectos?",

        "referencia":
            "La Comisión determina la factibilidad considerando la ruta, los requisitos, "
            "el personal y los tiempos solicitados."
    },

    {
        "id": 10,

        "documento":
            "ASIGNACIÓN-DE-TIEMPO-OCEANOGRÁFICO-CABO-DE-HORNOS-2020.pdf",

        "pregunta":
            "¿Qué institución organiza el concurso y a través de qué programa se realiza?",

        "referencia":
            "La Agencia Nacional de Investigación y Desarrollo (ANID), a través del "
            "Programa de Investigación Asociativa, llama al concurso."
    }

]


# ==============================================================
# RAGS
# ==============================================================

RAGS = [

    {
        "nombre": "NOMIC",
        "embedding_model": "nomic-embed-text",
        "persist_directory": CHROMA_NOMIC_DIR,
        "collection_name": "anid_nomic"
    },

    {
        "nombre": "EMBEDDINGGEMMA",
        "embedding_model": "embeddinggemma",
        "persist_directory": CHROMA_GEMMA_DIR,
        "collection_name": "anid_gemma"
    }

]


# ==============================================================
# RESULTADOS
# ==============================================================

resultados = []

evaluador = RagasMetrics()


# ==============================================================
# EJECUCIÓN
# ==============================================================

for configuracion_rag in RAGS:

    nombre_rag = configuracion_rag["nombre"]

    print()
    print("=" * 80)
    print(f" RAG: {nombre_rag}")
    print("=" * 80)

    rag = crear_rag_service(

        embedding_model=
            configuracion_rag["embedding_model"],

        persist_directory=
            configuracion_rag["persist_directory"],

        collection_name=
            configuracion_rag["collection_name"]

    )

    for consulta in CONSULTAS:

        numero = consulta["id"]
        documento = consulta["documento"]
        pregunta = consulta["pregunta"]
        referencia = consulta["referencia"]

        print()
        print("=" * 80)
        print(f" CONSULTA {numero}/10")
        print("=" * 80)

        print("Pregunta:")
        print(pregunta)

        print()

        for modelo in MODELOS:

            print()
            print("-" * 80)
            print(f"RAG       : {nombre_rag}")
            print(f"MODELO    : {modelo}")
            print(f"CONSULTA  : {numero}/10")
            print("-" * 80)

            resultado = ejecutar_modelo(

                rag=nombre_rag,

                modelo=modelo,

                pregunta=pregunta,

                respuesta_esperada=referencia,

                documento=documento,

                rag_service=rag

            )

            print()
            print("===== RESPUESTA =====")
            print(resultado.respuesta)

            print()
            print("===== MÉTRICAS RAGAS =====")

            try:

                metricas = evaluador.evaluar(

                    pregunta=pregunta,

                    respuesta=resultado.respuesta,

                    contextos=resultado.contextos_ragas,

                    referencia=referencia

                )

                print(
                    "Context Precision:",
                    metricas["context_precision"]
                )

                print(
                    "Context Recall   :",
                    metricas["context_recall"]
                )

                print(
                    "Faithfulness     :",
                    metricas["faithfulness"]
                )

                print(
                    "Answer Relevance :",
                    metricas["answer_relevancy"]
                )

            except Exception as e:

                print()
                print(
                    "[RAGAS ERROR]",
                    repr(e)
                )

                metricas = {

                    "context_precision": None,

                    "context_recall": None,

                    "faithfulness": None,

                    "answer_relevancy": None

                }

            # --------------------------------------------------
            # Guardar resultado
            # --------------------------------------------------

            resultados.append(
                {
                    "consulta_id": numero,

                    "documento": documento,

                    "rag": nombre_rag,

                    "modelo_llm": modelo,

                    "pregunta": pregunta,

                    "respuesta_referencia": referencia,

                    "respuesta": resultado.respuesta,

                    "retrieval": resultado.retrieval,

                    "rerank": resultado.rerank,

                    "metricas_ragas": {
                        "context_precision":
                            metricas["context_precision"],

                        "context_recall":
                            metricas["context_recall"],

                        "faithfulness":
                            metricas["faithfulness"],

                        "answer_relevancy":
                            metricas["answer_relevancy"]
                    }
                }
            )
            )


# ==============================================================
# GUARDAR JSON
# ==============================================================

ruta = Path(
    "/app/evaluation/results/comparacion_10_consultas_rag_llm.json"
)

ruta.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    ruta,
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(

        resultados,

        archivo,

        indent=4,

        ensure_ascii=False

    )


# ==============================================================
# RESUMEN
# ==============================================================

print()
print("=" * 80)
print(" BENCHMARK TERMINADO")
print("=" * 80)

print(
    "Consultas:",
    len(CONSULTAS)
)

print(
    "RAG:",
    len(RAGS)
)

print(
    "Modelos:",
    len(MODELOS)
)

print(
    "Evaluaciones esperadas:",
    len(CONSULTAS)
    * len(RAGS)
    * len(MODELOS)
)

print(
    "Resultados guardados:",
    len(resultados)
)

print(
    "Archivo:",
    ruta
)

print("=" * 80)

PY