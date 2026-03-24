def es_consulta_id(pregunta: str) -> bool:

    if not pregunta:
        return False

    p = pregunta.lower()

    # --------------------------------------------------
    # 🔥 SI MENCIONA DOCUMENTO PDF → SIEMPRE VÁLIDA
    # --------------------------------------------------
    if ".pdf" in p:
        return True

    # --------------------------------------------------
    # 🔥 PALABRAS CLAVE I+D / FONDOS
    # --------------------------------------------------
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

    # --------------------------------------------------
    # 🔥 PALABRAS CLAVE DOCUMENTOS LEGALES
    # --------------------------------------------------
    palabras_legales = [
        "resolucion",
        "resolución",
        "articulo",
        "artículo",
        "fecha",
        "tomado de razon",
        "tomado de razón",
        "resuelvo",
        "aprueba",
        "apruebase"
    ]

    for k in palabras_clave:
        if k in p:
            return True

    for k in palabras_legales:
        if k in p:
            return True

    return False
