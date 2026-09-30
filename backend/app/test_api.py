import requests


URL = "http://localhost:8000/chat"


preguntas = [
    '¿Cuál es el objetivo general del concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?',
    '¿Cuáles son los objetivos específicos del concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?',
    '¿Quién organiza el concurso ACCESO A EMBARCACIONES PARA INVESTIGACIÓN CIENTÍFICA 2022?',
    '¿Cuál es el objetivo general del concurso APOYO A CENTROS CIENTÍFICOS Y TECNOLÓGICOS DE EXCELENCIA CON FINANCIAMIENTO BASAL 2023?',
    '¿Cuáles son los objetivos específicos del concurso APOYO A CENTROS CIENTÍFICOS Y TECNOLÓGICOS DE EXCELENCIA CON FINANCIAMIENTO BASAL 2023?',
    '¿Quién organiza el concurso APOYO A CENTROS CIENTÍFICOS Y TECNOLÓGICOS DE EXCELENCIA CON FINANCIAMIENTO BASAL 2023?',
    '¿Cuál es el objetivo general del concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2020?',
    '¿Cuáles son los objetivos específicos del concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2020?',
    '¿Quién organiza el concurso ASIGNACIÓN DE TIEMPO OCEANOGRÁFICO CABO DE HORNOS 2020?',
    '¿Cuál es el objetivo general del concurso Ingeniería 2030?',
    '¿Cuáles son los objetivos específicos del concurso Ingeniería 2030?',
    '¿Quién organiza el concurso Ingeniería 2030?',
 ]


for pregunta in preguntas:

    respuesta = requests.post(
        URL,
        json={
            "pregunta": pregunta,
            "modelo": "gemma4:e2b",
            "rag": "nomic",
        },
        timeout=180,
    )

    print("=" * 80)
    print("Pregunta:", pregunta)
    print("Código HTTP:", respuesta.status_code)
    print("Content-Type:", respuesta.headers.get("content-type"))
    print("Respuesta:")
    print(respuesta.text)
    print()
