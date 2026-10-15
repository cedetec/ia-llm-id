# LLM/rag/query_expansions.py

EXPANSIONES_TIPO = {

    "OBJETIVO_GENERAL": [

        "objetivo general del concurso",
        "objetivo del concurso",
        "objetivo de este concurso",
        "el objetivo de este concurso",
        "objetivo del instrumento",
        "objetivo principal",
        "finalidad del concurso",
        "finalidad del instrumento",
        "línea de financiamiento",
        "apoyar el desarrollo de proyectos",
        "cumplimiento de objetivos científicos",
        "desarrollo científico",
        "generación de conocimiento"

    ],

    "OBJETIVOS_ESPECIFICOS": [

        "objetivos específicos",
        "objetivos particulares",
        "metas del concurso"

    ],

    "REQUISITOS": [

        "requisitos",
        "condiciones de postulación",
        "elegibilidad"

    ],

    "ORGANIZADOR": [

        "ANID",
        "Agencia Nacional de Investigación y Desarrollo",
        "Agencia Nacional de Investigación",
        "Agencia Nacional",
        "institución responsable",
        "organismo responsable",
        "institución convocante",
        "organismo convocante",
        "quién convoca",
        "convoca",
        "convocatoria",
        "llama al concurso",
        "llama a concurso",
        "Programa de Investigación Asociativa",
        "Subdirección",
        "Subdirección de Centros",
        "Subdirección de Investigación Asociativa",
        "Departamento",
        "Ministerio de Ciencia",
        "CONICYT"

    ],

    "FINANCIAMIENTO": [

        "financiamiento",

        "monto máximo",
        "monto máximo de financiamiento",
        "tope de financiamiento",
        "recursos disponibles",
        "presupuesto",

        "duración",
        "duración de los proyectos",
        "plazo",
        "plazo de ejecución",
        "vigencia del proyecto"

    ],

}

EXPANSIONES_TIPO_DOCUMENTO = {

    "FINANCIAMIENTO_BASAL": {

        "OBJETIVO_GENERAL": [

            "objetivo",
            "fortalecer centros",
            "centros científicos",
            "financiamiento basal"

        ],

        "REQUISITOS": [

            "centros científicos",
            "postulación",
            "beneficiarios"

        ]

    }

}

MAX_EXPANSIONES_TIPO = 4
