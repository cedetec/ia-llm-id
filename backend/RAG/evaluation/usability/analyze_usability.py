import csv
from pathlib import Path
from statistics import mean


BASE = Path(__file__).resolve().parent

TASK_RESULTS = BASE / "task_results.csv"
SURVEY_RESULTS = BASE / "survey_results.csv"
OUTPUT = BASE / "usability_report.md"


def cargar_csv(ruta):
    if not ruta.exists():
        raise FileNotFoundError(f"No existe: {ruta}")

    with ruta.open("r", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def main():
    tareas = cargar_csv(TASK_RESULTS)
    encuestas = cargar_csv(SURVEY_RESULTS)

    if not tareas:
        raise ValueError("No existen resultados de tareas.")

    if not encuestas:
        raise ValueError("No existen resultados de encuestas.")

    participantes = sorted(
        {
            fila["participant_id"]
            for fila in encuestas
        }
    )

    metricas_tareas = []

    for tarea_id in sorted(
        {fila["task_id"] for fila in tareas}
    ):
        filas = [
            fila
            for fila in tareas
            if fila["task_id"] == tarea_id
        ]

        completadas = [
            int(fila["completed"])
            for fila in filas
        ]

        tiempos = [
            float(fila["time_seconds"])
            for fila in filas
            if float(fila["time_seconds"]) >= 0
        ]

        ayudas = [
            int(fila["help_requested"])
            for fila in filas
        ]

        metricas_tareas.append(
            {
                "task_id": tarea_id,
                "n": len(filas),
                "success_rate": mean(completadas),
                "mean_time": mean(tiempos),
                "help_rate": mean(ayudas),
            }
        )

    nombres = [
        f"U{i}"
        for i in range(1, 9)
    ]

    promedios = {}

    for nombre in nombres:
        promedios[nombre] = mean(
            float(fila[nombre])
            for fila in encuestas
        )

    promedio_usabilidad = mean(
        promedios.values()
    )

    tiempo_global = mean(
        float(fila["time_seconds"])
        for fila in tareas
    )

    tasa_exito_global = mean(
        int(fila["completed"])
        for fila in tareas
    )

    tasa_ayuda_global = mean(
        int(fila["help_requested"])
        for fila in tareas
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as archivo:

        archivo.write(
            "# Resultados de evaluación de usabilidad\n\n"
        )

        archivo.write(
            f"Participantes: {len(participantes)}\n\n"
        )

        archivo.write(
            "## Resultados de tareas\n\n"
        )

        archivo.write(
            "| Tarea | Participantes | "
            "Tasa de éxito | Tiempo medio (s) | "
            "Tasa de ayuda |\n"
        )

        archivo.write(
            "|---|---:|---:|---:|---:|\n"
        )

        for fila in metricas_tareas:
            archivo.write(
                f"| {fila['task_id']} | "
                f"{fila['n']} | "
                f"{fila['success_rate'] * 100:.2f}% | "
                f"{fila['mean_time']:.2f} | "
                f"{fila['help_rate'] * 100:.2f}% |\n"
            )

        archivo.write(
            "\n## Resultados del cuestionario\n\n"
        )

        archivo.write(
            "| Criterio | Promedio (1-5) |\n"
        )

        archivo.write(
            "|---|---:|\n"
        )

        for nombre, valor in promedios.items():
            archivo.write(
                f"| {nombre} | {valor:.2f} |\n"
            )

        archivo.write(
            f"| **Promedio general de usabilidad** | "
            f"**{promedio_usabilidad:.2f}** |\n"
        )

        archivo.write(
            "\n## Indicadores globales\n\n"
        )

        archivo.write(
            f"- Tasa global de éxito: "
            f"{tasa_exito_global * 100:.2f}%\n"
        )

        archivo.write(
            f"- Tiempo medio global por tarea: "
            f"{tiempo_global:.2f} s\n"
        )

        archivo.write(
            f"- Tasa de tareas que requirieron ayuda: "
            f"{tasa_ayuda_global * 100:.2f}%\n"
        )

    print(f"Reporte generado: {OUTPUT}")


if __name__ == "__main__":
    main()
