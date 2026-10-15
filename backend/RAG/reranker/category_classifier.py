# category_classifier.py
from RAG.rag.context_patterns import (
    PATRONES_ENCABEZADO_OBJETIVO_GENERAL,
    PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS
)

from RAG.rag.context_categories import (

    CATEGORIAS_VALIDAS,

    CATEGORIAS_PRIORITARIAS,

    SECCIONES_ADMINISTRATIVAS

)


def clasificar_categoria(doc):

    seccion = doc.metadata.get(
        "seccion",
        ""
    ).upper()

    titulo_hijo = doc.metadata.get(
        "titulo_hijo",
        ""
    ).upper()

    subtitulo = (
        doc.metadata.get("subtitulo")
        or ""
    ).strip().upper()

    encabezado = (
        doc.metadata.get(
            "encabezado_original",
            ""
        ).upper()
    )

    #
    # Priorizar la sección cuando ya corresponde
    # a una categoría importante.
    #

    if seccion in CATEGORIAS_PRIORITARIAS:

        categoria = seccion

    #
    # Si no, utilizar el título hijo cuando
    # aporte una categoría válida.
    #

    elif titulo_hijo in CATEGORIAS_VALIDAS:

        categoria = titulo_hijo

    #
    # En cualquier otra categoría (GENERAL,
    # PRESENTACION, INTRODUCCION,
    # OTRAS_SECCIONES, etc.) intentar
    # reclasificar usando el encabezado.
    #

    else:

        categoria = seccion


    if categoria not in CATEGORIAS_PRIORITARIAS:

        #
        # Objetivo general.
        #

        if any(

            patron in encabezado

            for patron in PATRONES_ENCABEZADO_OBJETIVO_GENERAL

        ):

            categoria = "OBJETIVO_GENERAL"

        #
        # Objetivos específicos.
        #

        elif any(

            patron in encabezado

            for patron in PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS

        ):

            categoria = "OBJETIVOS_ESPECIFICOS"

    return {

        "categoria": categoria,

        "seccion": seccion,

        "titulo_hijo": titulo_hijo,

        "subtitulo": subtitulo,

        "encabezado": encabezado

    }
