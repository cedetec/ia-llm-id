# LLM/evaluation/repair_ragas_results.py

import json
import math

from pathlib import Path

from datasets import Dataset

from ragas import evaluate

from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_precision,
    context_recall
)

from ragas.exceptions import (
    RagasOutputParserException
)

from langchain_ollama import (
    ChatOllama,
    OllamaEmbeddings
)


#
# ============================================================
# CONFIGURACIÓN
# ============================================================
#

RESULTADOS_ORIGINALES = Path(
    "evaluation/results/benchmark.json"
)

RESULTADOS_REPARADOS = Path(
    "evaluation/results/benchmark_repaired.json"
)

LOG_REPARACION = Path(
    "evaluation/results/ragas_repair_log.json"
)

DATASET_REFERENCIA = Path(
    "LLM/evaluation/evaluation_dataset.json"
)


#
# Métricas utilizadas en el benchmark.
#

METRICAS = {

    "answer_relevancy":
        answer_relevancy,

    "faithfulness":
        faithfulness,

    "context_precision":
        context_precision,

    "context_recall":
        context_recall

}


#
# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
#

def es_nan(valor):

    if valor is None:
        return False

    try:

        return math.isnan(
            float(valor)
        )

    except (
        TypeError,
        ValueError
    ):

        return False


def limpiar_nan(obj):
    """
    Recorre recursivamente listas y diccionarios
    y convierte cualquier NaN / infinito en None.
    """

    if isinstance(obj, dict):

        return {
            clave: limpiar_nan(valor)
            for clave, valor in obj.items()
        }

    if isinstance(obj, list):

        return [
            limpiar_nan(valor)
            for valor in obj
        ]

    if isinstance(obj, float):

        if math.isnan(obj) or math.isinf(obj):

            return None

        return obj

    return obj


def cargar_json(ruta):

    with ruta.open(
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

    datos_limpios = limpiar_nan(
        datos
    )

    with ruta.open(
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(

            datos_limpios,

            archivo,

            indent=4,

            ensure_ascii=False,

            allow_nan=False

        )


def buscar_referencia(
    referencias,
    documento,
    pregunta
):

    clave = (
        documento,
        pregunta
    )

    return referencias.get(
        clave
    )


#
# ============================================================
# EVALUACIÓN DE UNA SOLA MÉTRICA
# ============================================================
#

def evaluar_metrica(

    metrica_nombre,

    metrica,

    pregunta,

    respuesta,

    contextos,

    referencia,

    llm,

    embeddings

):

    dataset = Dataset.from_dict(

        {

            "question": [
                pregunta
            ],

            "answer": [
                respuesta
            ],

            "contexts": [
                contextos
            ],

            "ground_truth": [
                referencia
            ]

        }

    )

    resultado = evaluate(

        dataset,

        metrics=[
            metrica
        ],

        llm=llm,

        embeddings=embeddings,

        raise_exceptions=True,

        show_progress=False

    )

    fila = (
        resultado
        .to_pandas()
        .iloc[0]
    )

    valor = fila[
        metrica_nombre
    ]

    if valor is None:

        raise ValueError(
            f"RAGAS devolvió None "
            f"para {metrica_nombre}"
        )

    valor = float(
        valor
    )

    if math.isnan(valor):

        raise ValueError(
            f"RAGAS devolvió NaN "
            f"para {metrica_nombre}"
        )

    return valor


#
# ============================================================
# MAIN
# ============================================================
#

def main():

    print()
    print("=" * 80)
    print("REPARACIÓN DE MÉTRICAS RAGAS")
    print("=" * 80)

    #
    # Cargar resultados originales.
    #

    datos = cargar_json(
        RESULTADOS_ORIGINALES
    )

    #
    # Cargar dataset de referencia.
    #

    dataset_referencia = cargar_json(
        DATASET_REFERENCIA
    )

    #
    # Crear índice:
    #
    # documento + pregunta
    #       ↓
    # respuesta esperada
    #

    referencias = {}

    for caso in dataset_referencia:

        clave = (

            caso["documento"],

            caso["pregunta"]

        )

        referencias[clave] = (
            caso["respuesta"]
        )

    print(
        "Registros originales:",
        len(datos)
    )

    #
    # Crear juez RAGAS.
    #
    # IMPORTANTE:
    # mantener la misma configuración
    # utilizada durante el benchmark.
    #

    llm = ChatOllama(

        model="mistral:latest",

        base_url="http://ollama:11434",

        temperature=0

    )

    embeddings = OllamaEmbeddings(

        model="nomic-embed-text",

        base_url="http://ollama:11434"

    )

    #
    # Contadores.
    #

    metricas_detectadas = 0

    metricas_reparadas = 0

    metricas_fallidas = 0

    registros_afectados = 0

    log = []

    #
    # Recorrer los 80 resultados.
    #

    for indice, registro in enumerate(
        datos,
        start=1
    ):

        ragas = registro.get(
            "ragas",
            {}
        )

        #
        # Detectar exclusivamente las métricas
        # que están en NaN.
        #

        pendientes = []

        for nombre in METRICAS:

            valor = ragas.get(
                nombre
            )

            if es_nan(valor):

                pendientes.append(
                    nombre
                )

        #
        # Si este registro no tiene NaN,
        # no hacer absolutamente nada.
        #

        if not pendientes:

            continue

        registros_afectados += 1

        print()
        print("=" * 80)
        print(
            f"REGISTRO {indice}"
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
            "Documento:",
            registro.get("documento")
        )

        print(
            "Pregunta:",
            registro.get("pregunta")
        )

        print(
            "Métricas pendientes:",
            ", ".join(pendientes)
        )

        #
        # Buscar respuesta de referencia.
        #

        referencia = buscar_referencia(

            referencias,

            registro.get(
                "documento"
            ),

            registro.get(
                "pregunta"
            )

        )

        if referencia is None:

            print(
                "[ERROR] "
                "No se encontró referencia."
            )

            for nombre in pendientes:

                metricas_detectadas += 1

                log.append(

                    {

                        "registro":
                            indice,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            registro.get(
                                "documento"
                            ),

                        "pregunta":
                            registro.get(
                                "pregunta"
                            ),

                        "metrica":
                            nombre,

                        "resultado":
                            "error",

                        "error":
                            "No se encontró "
                            "respuesta de referencia."

                    }

                )

                metricas_fallidas += 1

            continue

        #
        # Contextos utilizados originalmente
        # por RAGAS.
        #

        contextos = registro.get(
            "contextos_ragas",
            []
        )

        #
        # Respuesta generada originalmente.
        #

        respuesta = registro.get(
            "respuesta",
            ""
        )

        #
        # Reevaluar SOLO las métricas pendientes.
        #

        for nombre in pendientes:

            metricas_detectadas += 1

            print()
            print(
                f"[RAGAS] "
                f"Reevaluando {nombre}..."
            )

            try:

                valor = evaluar_metrica(

                    metrica_nombre=nombre,

                    metrica=METRICAS[nombre],

                    pregunta=registro[
                        "pregunta"
                    ],

                    respuesta=respuesta,

                    contextos=contextos,

                    referencia=referencia,

                    llm=llm,

                    embeddings=embeddings

                )

                #
                # Sustituir solamente el NaN.
                #

                ragas[nombre] = valor

                metricas_reparadas += 1

                print(
                    f"[RAGAS] "
                    f"{nombre} = {valor}"
                )

                log.append(

                    {

                        "registro":
                            indice,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            registro.get(
                                "documento"
                            ),

                        "pregunta":
                            registro.get(
                                "pregunta"
                            ),

                        "metrica":
                            nombre,

                        "resultado":
                            "reparada",

                        "valor":
                            valor

                    }

                )

            except RagasOutputParserException as e:

                #
                # El parser volvió a fallar.
                #
                # NO convertir a 0.
                #

                ragas[nombre] = None

                metricas_fallidas += 1

                print(
                    f"[RAGAS] "
                    f"{nombre}: "
                    "ERROR DE PARSEO"
                )

                print(
                    type(e).__name__,
                    str(e)
                )

                log.append(

                    {

                        "registro":
                            indice,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            registro.get(
                                "documento"
                            ),

                        "pregunta":
                            registro.get(
                                "pregunta"
                            ),

                        "metrica":
                            nombre,

                        "resultado":
                            "error_parser",

                        "error":
                            str(e)

                    }

                )

            except Exception as e:

                #
                # Cualquier otro error.
                #

                ragas[nombre] = None

                metricas_fallidas += 1

                print(
                    f"[RAGAS] "
                    f"{nombre}: ERROR"
                )

                print(
                    type(e).__name__,
                    str(e)
                )

                log.append(

                    {

                        "registro":
                            indice,

                        "rag":
                            registro.get(
                                "rag"
                            ),

                        "modelo":
                            registro.get(
                                "modelo"
                            ),

                        "documento":
                            registro.get(
                                "documento"
                            ),

                        "pregunta":
                            registro.get(
                                "pregunta"
                            ),

                        "metrica":
                            nombre,

                        "resultado":
                            "error",

                        "error":
                            str(e)

                    }

                )

    #
    # Guardar resultado reparado.
    #

    guardar_json(

        RESULTADOS_REPARADOS,

        datos

    )

    #
    # Guardar log de reparación.
    #

    guardar_json(

        LOG_REPARACION,

        log

    )

    #
    # Comprobación final.
    #

    nan_restantes = []

    for indice, registro in enumerate(
        datos,
        start=1
    ):

        ragas = registro.get(
            "ragas",
            {}
        )

        for nombre, valor in ragas.items():

            if es_nan(valor):

                nan_restantes.append(

                    {

                        "registro":
                            indice,

                        "metrica":
                            nombre

                    }

                )

    #
    # Resumen.
    #

    print()
    print("=" * 80)
    print("RESUMEN DE REPARACIÓN")
    print("=" * 80)

    print(
        "Registros originales:",
        len(
            datos
        )
    )

    print(
        "Registros afectados:",
        registros_afectados
    )

    print(
        "Métricas NaN detectadas:",
        metricas_detectadas
    )

    print(
        "Métricas reparadas:",
        metricas_reparadas
    )

    print(
        "Métricas fallidas:",
        metricas_fallidas
    )

    print(
        "NaN restantes:",
        len(
            nan_restantes
        )
    )

    print()
    print(
        "Resultado reparado:",
        RESULTADOS_REPARADOS
    )

    print(
        "Log de reparación:",
        LOG_REPARACION
    )

    #
    # Listar NaN que eventualmente continúen.
    #

    if nan_restantes:

        print()
        print(
            "===== MÉTRICAS SIN REPARAR ====="
        )

        for item in nan_restantes:

            print(

                "Registro:",
                item["registro"],

                "| Métrica:",
                item["metrica"]

            )

    else:

        print()
        print(
            "No quedan valores NaN."
        )

    print("=" * 80)


if __name__ == "__main__":

    main()