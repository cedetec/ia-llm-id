# bonus_calculator.py

from RAG.reranker.rerank_rules import (
    obtener_bonificacion
)

from RAG.rag.context_patterns import (
    PATRONES_ADMINISTRATIVOS
)

BONUS_DOCUMENTO = 0.50
BONUS_ANIO = 0.50

def calcular_bonus(

    doc,

    categoria,

    seccion,

    titulo_hijo,

    encabezado,

    subtitulo,

    score_original,

    tipo_consulta,

    documento_pregunta,

    anio_pregunta,

    tipos_consulta=None

):

    score_final = score_original

    bonus_categoria = 0

    penalizacion = 0

    #
    # Penalizaciones
    #

    if seccion == "GENERAL":

        longitud = len(doc.page_content.split())

        #
        # No penalizar si el chunk ya fue
        # clasificado como objetivo general
        # u objetivos específicos.
        #

        if categoria in (

            "OBJETIVO_GENERAL",

            "OBJETIVOS_ESPECIFICOS"

        ):

            pass

        else:

            encabezado_admin = any(

                patron in encabezado

                for patron in PATRONES_ADMINISTRATIVOS

            )

            if encabezado_admin:

                penalizacion = -1.0

            elif longitud < 40:

                penalizacion = -0.25

        score_final += penalizacion

    #
    # Bonus por categoría
    #

    tipo_bonus = tipos_consulta or tipo_consulta

    bonus_categoria = obtener_bonificacion(

        tipo_bonus,

        categoria

    )

    score_final += bonus_categoria

    #
    # Bonus por documento
    #

    documento = doc.metadata.get(
        "documento",
        ""
    ).upper()

    bonus_documento = 0

    if documento_pregunta:

        if documento_pregunta in documento:

            bonus_documento += BONUS_DOCUMENTO

            if (

                anio_pregunta

                and

                anio_pregunta in documento

            ):

                bonus_documento += BONUS_ANIO

    score_final += bonus_documento

    #
    # Debug
    #


    return {

        "score_final": score_final,

        "bonus_categoria": bonus_categoria,

        "penalizacion": penalizacion

    }
