# LLM/rag/query_type_detector.py

import re

TIPOS_CONSULTA = {

    "OBJETIVO_GENERAL": [

        "objetivo",

        "objetivo general",

        "objetivo principal",

        "finalidad",

        "proposito",

        "propósito",

        "objetivo del concurso",

        "objetivo de este concurso",

        "fin del concurso"

    ],

    "OBJETIVOS_ESPECIFICOS": [

        "objetivos especificos",

        "objetivos específicos",

        "objetivo especifico",

        "objetivo específico",

        "objetivos particulares",

        "propósitos específicos",

        "metas"

    ],

    "RESULTADOS_ESPERADOS": [

        "resultado esperado",

        "resultados esperados",

        "resultado",

        "resultados"

    ],

    "REQUISITOS": [

        "requisito",

        "requisitos",

        "elegibilidad",

        "condiciones",

        "condiciones de participación",

    ],

    "BENEFICIOS": [
        "beneficio",
        "beneficios",
        "subsidio",
        "apoyo",
        "plazo",
        "plazos",
        "duracion",
        "duración",
        "vigencia"
    ],

    "FINANCIAMIENTO": [

        "financiamiento",

        "monto",

        "presupuesto",

        "aporte"

    ],

    "EVALUACION": [

        "evaluacion",

        "evaluación",

        "criterios"

    ],

    "POSTULANTES": [

        "postulante",

        "postulantes",

        "beneficiario",

        "beneficiarios"

    ],

    "ORGANIZADOR": [

        "organiza",

        "organizador",

        "quién organiza",

        "quien organiza",

        "quién convoca",

        "quien convoca",

        "convoca",

        "convocante",

        "institución",

        "institucion",

        "institución responsable",

        "institucion responsable",

        "organismo",

        "organismo responsable",

        "responsable",

        "administra",

        "ejecuta",

        "anid",

        "ministerio"

    ]

}

#
# Prioridad utilizada únicamente cuando dos
# coincidencias tienen la misma especificidad.
#

PRIORIDAD_TIPOS = {

    "OBJETIVOS_ESPECIFICOS": 3,

    "OBJETIVO_GENERAL": 2,

    "RESULTADOS_ESPERADOS": 2,

    "REQUISITOS": 2,

    "FINANCIAMIENTO": 2,

    "BENEFICIOS": 2,

    "EVALUACION": 2,

    "POSTULANTES": 2,

    "ORGANIZADOR": 1

}


def detectar_tipo_consulta(consulta: str):

    #
    # Normalizar la consulta.
    #

    consulta = consulta.lower()

    coincidencias = []

    for tipo, triggers in TIPOS_CONSULTA.items():

        for trigger in triggers:

            patron = rf"\b{re.escape(trigger)}\b"

            if re.search(patron, consulta):

                coincidencias.append({

                    "tipo": tipo,

                    "trigger": trigger,

                    "longitud": len(trigger.split()),

                    "caracteres": len(trigger)

                })

    if not coincidencias:

        return None

    mejor = max(

        coincidencias,

        key=lambda x: (

            x["longitud"],

            x["caracteres"],

            PRIORIDAD_TIPOS.get(

                x["tipo"],

                0

            )

        )

    )

    return mejor["tipo"]


def detectar_tipos_consulta(consulta: str):

    consulta = consulta.lower()

    tipos = []

    for tipo, triggers in TIPOS_CONSULTA.items():

        for trigger in triggers:

            patron = rf"\b{re.escape(trigger)}\b"

            if re.search(patron, consulta):

                tipos.append(
                    tipo
                )

                break

    return tipos
