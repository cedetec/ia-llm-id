# LLM/preprocessing/contextual_chunk_service.py

from PREPROCESSING.preprocessing.section_detector import (
    obtener_titulo_padre
)

from PREPROCESSING.preprocessing.heading_classifier import (
    parece_encabezado
)

from PREPROCESSING.preprocessing.section_keywords import (
    PALABRAS_CLAVE
)

from PREPROCESSING.preprocessing.embedding_builder import (
    construir_texto_embedding
)

from PREPROCESSING.preprocessing.section_constants import (
    GENERAL
)

from RAG.rag.context_patterns import (
    PATRONES_ENCABEZADO_OBJETIVO_GENERAL,
    PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS
)

from RAG.rag.context_categories import (
    CATEGORIAS_VALIDAS
)

import re


TIPO_DOCUMENTO = "Concurso ANID"

CAMPOS_METADATA = (

    "seccion",

    "titulo_padre",

    "titulo_hijo",

    "encabezado_original",

)


def extraer_subtitulo(texto):

    if not texto:

        return ""

    lineas = texto.splitlines()

    if not lineas:

        return ""

    match = re.match(

        r"\s*(\d+(?:\.\d+)*)",

        lineas[0]

    )

    if match:

        return match.group(1)

    return ""


def obtener_subtitulo(doc, texto, encabezado_original):
    """
    Obtiene el subtítulo respetando un orden de prioridad.
    """

    fuentes = [

        doc.metadata.get("subtitulo"),

        encabezado_original,

        doc.metadata.get("encabezado_original"),

        texto

    ]

    for fuente in fuentes:

        if not fuente:
            continue

        subtitulo = extraer_subtitulo(fuente)

        if subtitulo:

            return subtitulo

    return ""


def enriquecer_chunks(fragmentos):

    documento_actual = None

    for doc in fragmentos:

        documento = doc.metadata.get(
            "documento",
            ""
        )

        texto = doc.page_content

        faltantes = [
            campo
            for campo in CAMPOS_METADATA
            if not doc.metadata.get(campo)
        ]

        if faltantes:
            pass


        #
        # 1. Priorizar la sección creada por el splitter
        #

        #
        # Recuperar primero el encabezado original.
        #

        encabezado_original = (
            doc.metadata.get("encabezado_original")
            or ""
        )


        seccion = (
            doc.metadata.get("seccion")
            or GENERAL
        )

        titulo_padre = (
            doc.metadata.get("titulo_padre")
            or obtener_titulo_padre(seccion)
        )

        titulo_hijo = (
            doc.metadata.get("titulo_hijo")
            or seccion
        )

        subtitulo = (
            doc.metadata.get("subtitulo")
            or obtener_subtitulo(
                doc,
                texto,
                encabezado_original
            )
        )

        if (

            titulo_hijo == GENERAL

            and subtitulo

        ):
            pass


        pagina = (
            doc.metadata.get("pagina")
            or ""
        )

        palabras_clave = ", ".join(

            PALABRAS_CLAVE.get(

                seccion,

                []

            )

        )

        #
        # Guardar metadata
        #

        doc.metadata["tipo"] = TIPO_DOCUMENTO or ""

        doc.metadata.setdefault(
            "seccion",
            GENERAL
        )

        if (

            doc.metadata.get("titulo_padre")

            and

            doc.metadata["titulo_padre"] != titulo_padre

        ):
            pass


        if not doc.metadata.get("titulo_padre"):

            doc.metadata["titulo_padre"] = titulo_padre

        if (

            doc.metadata.get("titulo_hijo")

            and

            doc.metadata["titulo_hijo"] != titulo_hijo

        ):
            pass


        if not doc.metadata.get("titulo_hijo"):

            doc.metadata["titulo_hijo"] = titulo_hijo

        #
        # Conservar siempre el encabezado detectado por el splitter.
        #

        doc.metadata["encabezado_original"] = (

            doc.metadata.get("encabezado_original")

            or encabezado_original

            or ""

        )

        if not doc.metadata.get("encabezado_original"):


            primera = texto.splitlines()[0].strip()

            #
            # Debe comenzar con numeración
            #

            if primera and parece_encabezado(primera):

                doc.metadata["encabezado_original"] = primera

                encabezado_original = primera


        #
        # Reclasificar chunks cuya categoría todavía
        # no sea suficientemente específica.
        #

        if (

            titulo_hijo not in CATEGORIAS_VALIDAS

            and

            encabezado_original

        ):

            encabezado = encabezado_original.upper()

            categoria_original = titulo_hijo

            if any(

                patron in encabezado

                for patron in PATRONES_ENCABEZADO_OBJETIVO_GENERAL

            ):

                titulo_hijo = "OBJETIVO_GENERAL"

            elif any(

                patron in encabezado

                for patron in PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS

            ):

                titulo_hijo = "OBJETIVOS_ESPECIFICOS"

            #
            # Si hubo reclasificación,
            # actualizar toda la jerarquía.
            #

            if titulo_hijo != categoria_original:

                titulo_padre = obtener_titulo_padre(
                    titulo_hijo
                )

                #
                # Actualizar la metadata.
                #

                doc.metadata["titulo_hijo"] = titulo_hijo

                doc.metadata["titulo_padre"] = titulo_padre

                #
                # Sincronizar las variables locales
                # con la metadata ya corregida.
                #

                titulo_hijo = doc.metadata["titulo_hijo"]

                titulo_padre = doc.metadata["titulo_padre"]



        #
        # Evitar doble enriquecimiento
        #

        if texto.startswith("DOCUMENTO:"):

            continue

        #
        # Diagnóstico temporal.
        #

        texto_upper = texto.upper()

        if (
            doc.metadata.get("seccion") == "OBJETIVOS"
            and
            "OBJETIVO GENERAL" in texto_upper
        ):
            pass


        doc.page_content = construir_texto_embedding(

            documento=documento,

            tipo=TIPO_DOCUMENTO,

            titulo_padre=titulo_padre,

            titulo_hijo=titulo_hijo,

            subtitulo=subtitulo,

            encabezado_original=encabezado_original,

            seccion=seccion,

            pagina=pagina,

            palabras_clave=palabras_clave,

            contenido=texto

        )

    return fragmentos
