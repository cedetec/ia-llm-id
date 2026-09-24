import csv
import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


BASE = Path(__file__).resolve().parent

TASKS_FILE = BASE / "usability_tasks.json"
CRITERIA_FILE = BASE / "task_success_criteria.md"
OUTPUT_FILE = BASE / "task_validation_results.csv"

API_URL = os.getenv(
    "USABILITY_API_URL",
    "http://127.0.0.1:8000"
)

MODEL = "gemma4:e2b"
RAG = "nomic"


def cargar_tareas():
    with TASKS_FILE.open(
        "r",
        encoding="utf-8"
    ) as archivo:
        return json.load(archivo)


def cargar_criterios():
    texto = CRITERIA_FILE.read_text(
        encoding="utf-8"
    )

    criterios = {}

    partes = re.split(
        r"(?m)^## (T[1-5]) — ",
        texto
    )

    for i in range(
        1,
        len(partes),
        2
    ):
        tarea_id = partes[i]
        contenido = partes[i + 1]

        inicio = contenido.find(
            "### Criterio de éxito"
        )

        fin = contenido.find(
            "### Se considera incompleta"
        )

        if inicio != -1 and fin != -1:
            criterios[tarea_id] = (
                contenido[
                    inicio:fin
                ].strip()
            )

    return criterios


def consultar(pregunta):
    payload = json.dumps(
        {
            "pregunta": pregunta,
            "modelo": MODEL,
            "rag": RAG
        }
    ).encode("utf-8")

    request = Request(
        f"{API_URL}/chat",
        data=payload,
        headers={
            "Content-Type":
                "application/json"
        },
        method="POST"
    )

    inicio = time.perf_counter()

    try:
        with urlopen(
            request,
            timeout=600
        ) as response:

            datos = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as exc:
        detalle = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"HTTP {exc.code}: {detalle}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"No se pudo conectar con {API_URL}: "
            f"{exc.reason}"
        ) from exc

    tiempo = (
        time.perf_counter()
        - inicio
    )

    respuesta = (
        datos.get("respuesta")
        or datos.get("answer")
        or ""
    )

    justificacion = (
        datos.get("justificacion")
        or ""
    )

    return (
        respuesta,
        justificacion,
        tiempo
    )


def pedir_entero(
    mensaje,
    minimo,
    maximo
):
    while True:
        valor = input(
            mensaje
        ).strip()

        try:
            numero = int(valor)
        except ValueError:
            print(
                "Ingrese un número válido."
            )
            continue

        if minimo <= numero <= maximo:
            return numero

        print(
            f"Ingrese un valor entre "
            f"{minimo} y {maximo}."
        )


def inicializar_csv():
    if OUTPUT_FILE.exists():
        return

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as archivo:

        writer = csv.writer(archivo)

        writer.writerow(
            [
                "task_id",
                "completed",
                "evaluation_notes",
                "system_time_seconds"
            ]
        )


def main():

    print("=" * 80)
    print("VALIDACIÓN PREVIA DE TAREAS DE USABILIDAD")
    print("=" * 80)

    print(
        f"API: {API_URL}"
    )

    print(
        f"Modelo: {MODEL}"
    )

    print(
        f"RAG: {RAG}"
    )

    print("=" * 80)

    tareas = cargar_tareas()
    criterios = cargar_criterios()

    inicializar_csv()

    with OUTPUT_FILE.open(
        "a",
        newline="",
        encoding="utf-8"
    ) as archivo:

        writer = csv.writer(
            archivo
        )

        for tarea in tareas:

            print()
            print("=" * 80)
            print(
                f"{tarea['id']} — CONSULTA"
            )
            print("=" * 80)

            print()
            print(
                tarea["pregunta"]
            )

            print()
            print(
                "Ejecutando consulta..."
            )

            try:

                (
                    respuesta,
                    justificacion,
                    tiempo
                ) = consultar(
                    tarea["pregunta"]
                )

            except Exception as exc:

                print()
                print(
                    "ERROR AL REALIZAR LA CONSULTA:"
                )
                print(exc)

                writer.writerow(
                    [
                        tarea["id"],
                        0,
                        f"Error: {exc}",
                        ""
                    ]
                )

                continue

            print()
            print("-" * 80)
            print("RESPUESTA DEL ASISTENTE")
            print("-" * 80)
            print(
                respuesta
            )

            if justificacion:
                print()
                print("-" * 80)
                print("JUSTIFICACIÓN")
                print("-" * 80)
                print(
                    justificacion
                )

            print()
            print(
                f"Tiempo de respuesta del sistema: "
                f"{tiempo:.2f} segundos"
            )

            print()
            print("-" * 80)
            print("CRITERIO DE ÉXITO")
            print("-" * 80)

            print(
                criterios.get(
                    tarea["id"],
                    "Consultar task_success_criteria.md"
                )
            )

            print()
            print("-" * 80)
            print("EVALUACIÓN DEL RESULTADO")
            print("-" * 80)

            completed = pedir_entero(
                "¿La respuesta permite cumplir "
                "el criterio de éxito? "
                "(1=Sí, 0=No): ",
                0,
                1
            )

            notes = input(
                "Observaciones sobre la respuesta: "
            ).strip()

            writer.writerow(
                [
                    tarea["id"],
                    completed,
                    notes,
                    f"{tiempo:.2f}"
                ]
            )

            archivo.flush()

    print()
    print("=" * 80)
    print("VALIDACIÓN FINALIZADA")
    print("=" * 80)

    print(
        f"Resultados guardados en:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
