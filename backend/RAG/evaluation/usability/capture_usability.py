import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent

TASKS_FILE = BASE / "usability_tasks.json"
TASK_RESULTS_FILE = BASE / "task_results.csv"
SURVEY_RESULTS_FILE = BASE / "survey_results.csv"


def pedir_entero(mensaje, minimo, maximo):
    while True:
        valor = input(mensaje).strip()

        try:
            numero = int(valor)
        except ValueError:
            print("Ingrese un número válido.")
            continue

        if minimo <= numero <= maximo:
            return numero

        print(f"Ingrese un valor entre {minimo} y {maximo}.")


def inicializar_archivo(ruta, encabezado):
    if not ruta.exists():
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.writer(archivo)
            writer.writerow(encabezado)


def cargar_tareas():
    import json

    with TASKS_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def main():
    print("=" * 70)
    print("CAPTURA DE EVALUACIÓN DE USABILIDAD")
    print("=" * 70)

    participant_id = input("ID del participante: ").strip()

    if not participant_id:
        raise ValueError("El ID del participante no puede estar vacío.")

    tareas = cargar_tareas()

    inicializar_archivo(
        TASK_RESULTS_FILE,
        [
            "participant_id",
            "task_id",
            "completed",
            "time_seconds",
            "help_requested",
            "notes",
        ],
    )

    inicializar_archivo(
        SURVEY_RESULTS_FILE,
        [
            "participant_id",
            "U1",
            "U2",
            "U3",
            "U4",
            "U5",
            "U6",
            "U7",
            "U8",
            "most_useful",
            "improvement",
        ],
    )

    with TASK_RESULTS_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as archivo:

        writer = csv.writer(archivo)

        print()
        print("=== RESULTADOS DE LAS TAREAS ===")

        for tarea in tareas:

            print()
            print(f"{tarea['id']}: {tarea['pregunta']}")

            completed = pedir_entero(
                "¿Completó la tarea? (1=Sí, 0=No): ",
                0,
                1,
            )

            while True:
                tiempo = input("Tiempo empleado en segundos: ").strip()

                try:
                    tiempo = float(tiempo)

                    if tiempo >= 0:
                        break

                except ValueError:
                    pass

                print("Ingrese un número válido mayor o igual a 0.")

            help_requested = pedir_entero(
                "¿Necesitó ayuda? (1=Sí, 0=No): ",
                0,
                1,
            )

            notes = input("Observaciones: ").strip()

            writer.writerow(
                [
                    participant_id,
                    tarea["id"],
                    completed,
                    tiempo,
                    help_requested,
                    notes,
                ]
            )

    print()
    print("=== CUESTIONARIO ===")

    respuestas = [participant_id]

    for numero in range(1, 9):
        valor = pedir_entero(
            f"U{numero} (1-5): ",
            1,
            5,
        )

        respuestas.append(valor)

    respuestas.append(
        input("¿Qué aspecto le resultó más útil?: ").strip()
    )

    respuestas.append(
        input("¿Qué aspecto mejoraría?: ").strip()
    )

    with SURVEY_RESULTS_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as archivo:

        writer = csv.writer(archivo)
        writer.writerow(respuestas)

    print()
    print("Evaluación registrada correctamente.")


if __name__ == "__main__":
    main()
