# context_utils.py

from LLM.rag.context_patterns import (
    PATRONES_OBJETIVO,
    PATRONES_CONTENIDO_OBJETIVO_GENERAL
)

SECCIONES_OBJETIVO = {

    "OBJETIVO_GENERAL",

    "OBJETIVO_PROPUESTA",

}


def es_objetivo_general(doc):
    """
    Determina si un chunk corresponde
    al objetivo principal del concurso.
    """

    seccion = (
        doc.metadata.get(
            "seccion",
            ""
        ).upper()
    )

    titulo_hijo = (
        doc.metadata.get(
            "titulo_hijo",
            ""
        ).upper()
    )

    encabezado = (
        doc.metadata.get(
            "encabezado_original",
            ""
        ).upper()
    )

    if seccion in SECCIONES_OBJETIVO:
        return True

    if titulo_hijo in SECCIONES_OBJETIVO:
        return True

    if any(

        patron in titulo_hijo

        for patron in PATRONES_OBJETIVO

    ):
        return True

    if any(

        patron in encabezado

        for patron in PATRONES_OBJETIVO

    ):
        return True

    #
    # Último recurso:
    # buscar patrones directamente
    # dentro del contenido del chunk.
    #

    texto = doc.page_content.upper()

    if any(

        patron in texto

        for patron in PATRONES_CONTENIDO_OBJETIVO_GENERAL

    ):

        print(

            "[OBJETIVO DETECTADO POR CONTENIDO]",

            {

                "pagina": doc.metadata.get("pagina"),

                "documento": doc.metadata.get("documento"),

                "encabezado": doc.metadata.get(
                    "encabezado_original"
                )

            }

        )

        return True

    return False
