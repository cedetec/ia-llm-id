# LLM/preprocessing/keywords/proposal.py

from PREPROCESSING.preprocessing.section_constants import (

    PRESENTACION_CENTRO,
    OBJETIVO_PROPUESTA,
    PROPUESTA_TECNICA,
    PLAN_CONTINUIDAD

)


PROPOSAL_KEYWORDS = {

    PRESENTACION_CENTRO: [

        "presentación del centro",
        "centro",
        "institución",
        "trayectoria",
        "historia",
        "capacidades",
        "infraestructura"

    ],

    OBJETIVO_PROPUESTA: [

        "objetivo de la propuesta",
        "objetivo del proyecto",
        "objetivo principal",
        "objetivo general",
        "propuesta"

    ],

    PROPUESTA_TECNICA: [

        "propuesta técnica",
        "descripción de la propuesta",
        "plan de trabajo",
        "actividades",
        "metodología",
        "ejecución"

    ],

    PLAN_CONTINUIDAD: [

        "plan de continuidad",
        "continuidad",
        "sostenibilidad",
        "proyección",
        "mantención"

    ]

}