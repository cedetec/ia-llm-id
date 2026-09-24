import requests

preguntas = [
    "¿Cuál es el objetivo general del concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?",
    "¿Cuáles son los objetivos específicos del concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?",
    "¿Quién organiza el concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?"
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
