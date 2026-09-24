# LLM/preprocessing/chunk_filter.py

from LLM.preprocessing.section_constants import (
    GENERAL
)

SECCIONES_CRITICAS = {

    "OBJETIVO_GENERAL",

    "PROPOSITO_CONVOCATORIA",

    "OBJETIVO_PROPUESTA",

    "OBJETIVOS_ESPECIFICOS",

    "REQUISITOS",

    "FINANCIAMIENTO",

    "RESULTADOS_ESPERADOS",

}

MIN_PALABRAS = 80


def mantener_chunk(

    chunk

):

    seccion = chunk.metadata.get(

        "seccion",

        GENERAL

    )

    if seccion in SECCIONES_CRITICAS:

        return True

    return (

        len(

            chunk.page_content.split()

        )

        >=

        MIN_PALABRAS

    )
