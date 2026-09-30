# LLM/reranker/rerank_rules.py

BONIFICACIONES = {

    #
    # ==========================================
    # OBJETIVO GENERAL
    # ==========================================
    #

    "OBJETIVO_GENERAL": {

        #
        # Coincidencia exacta
        #

        "OBJETIVO_GENERAL": 2.0,

        #
        # Último recurso únicamente
        #

        "OBJETIVOS": 0.75

    },

    #
    # ==========================================
    # OBJETIVOS ESPECÍFICOS
    # ==========================================
    #

    "OBJETIVOS_ESPECIFICOS": {

        "OBJETIVOS_ESPECIFICOS": 2.0,

        "OBJETIVOS": 1.0

    },

    #
    # ==========================================
    # REQUISITOS
    # ==========================================
    #

    "REQUISITOS": {

        "REQUISITOS": 2.0,

        "POSTULANTES": 0.50

    },

    #
    # ==========================================
    # FINANCIAMIENTO
    # ==========================================
    #

    "FINANCIAMIENTO": {
        "FINANCIAMIENTO": 2.0,
        "BENEFICIOS": 2.0
    },

    #
    # ==========================================
    # BENEFICIOS
    # ==========================================
    #

    "BENEFICIOS": {

        "BENEFICIOS": 2.0

    },

    #
    # ==========================================
    # EVALUACIÓN
    # ==========================================
    #

    "EVALUACION": {

        "EVALUACION": 2.0

    },

    #
    # ==========================================
    # POSTULANTES
    # ==========================================
    #

    "POSTULANTES": {

        "POSTULANTES": 2.0

    },

    #
    # ==========================================
    # ORGANIZADOR
    # ==========================================
    #

    "ORGANIZADOR": {

        "INTRODUCCION": 2.0,

        "PRESENTACION_CENTRO": 2.0,

        "ANTECEDENTES_POSTULACION": 1.75

    }

}


def obtener_bonificacion(
    tipo_consulta,
    categoria
):

    if tipo_consulta is None:
        return 0

    if isinstance(
        tipo_consulta,
        str
    ):

        return BONIFICACIONES.get(
            tipo_consulta,
            {}
        ).get(
            categoria,
            0
        )

    bonus = 0

    for tipo in tipo_consulta:

        bonus_actual = BONIFICACIONES.get(
            tipo,
            {}
        ).get(
            categoria,
            0
        )

        bonus = max(
            bonus,
            bonus_actual
        )

    return bonus
