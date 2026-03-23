def es_consulta_id(pregunta: str) -> bool:

    if not pregunta:
        return False

    p = pregunta.lower()

    palabras_clave = [
        "concurso",
        "fondos",
        "financiamiento",
        "proyecto",
        "investigacion",
        "investigación",
        "desarrollo",
        "i+d",
        "anid",
        "corfo",
        "fondecyt",
        "fondef",
        "beneficiarios",
        "postular",
        "requisitos",
        "objetivo",
        "monto",
        "duracion",
        "duración",
        "evaluacion",
        "evaluación",
        "cofinanciamiento",
        "empresa",
        "universidad",
        "trl",
        "equidad",
        "genero",
        "género",
        "bases"
    ]

    for k in palabras_clave:
        if k in p:
            return True

    return False
