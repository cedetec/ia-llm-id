# LLM/preprocessing/keywords/funding.py

from LLM.preprocessing.section_constants import (

    FINANCIAMIENTO,
    BENEFICIOS,
    EVALUACION

)


FUNDING_KEYWORDS = {

    FINANCIAMIENTO: [

        "financiamiento",
        "monto",
        "presupuesto",
        "aporte",
        "aporte ANID",
        "cofinanciamiento",
        "subsidio",
        "recursos"

    ],

    BENEFICIOS: [

        "beneficios",
        "subsidio",
        "apoyo",
        "financiamiento"

    ],

    EVALUACION: [

        "evaluación",
        "criterios",
        "selección",
        "comité evaluador"

    ]

}