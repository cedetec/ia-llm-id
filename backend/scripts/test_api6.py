import requests

preguntas = [
    "¿Cuál es el objetivo general del concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2023?",
    "¿Cuáles son los objetivos específicos del concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2023?",
    "¿Quién organiza el concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2023?"
]

for pregunta in preguntas:

    print("=" * 80)
    print("Pregunta:", pregunta)

    respuesta = requests.post(
        "http://localhost:8000/chat",
        json={"pregunta": pregunta}
    )

    print("Código HTTP:", respuesta.status_code)
    print("Content-Type:", respuesta.headers.get("content-type"))
    print("Respuesta:")
    print(respuesta.text)
    print()