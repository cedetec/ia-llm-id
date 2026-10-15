# LLM/preprocessing/semantic_section_splitter.py

from PREPROCESSING.preprocessing.header_detector import (
    detectar_encabezado
)

from PREPROCESSING.preprocessing.subsection_detector import (
    detectar_subseccion
)

from PREPROCESSING.preprocessing.buffer_manager import (
    BufferManager
)

from PREPROCESSING.preprocessing.metadata_builder import (
    crear_metadata
)

from PREPROCESSING.preprocessing.header_processor import (
    procesar_cambio_seccion
)

from PREPROCESSING.preprocessing.subsection_processor import (
    procesar_subtitulo
)

from PREPROCESSING.preprocessing.chunk_builder import (
    crear_chunks
)

from PREPROCESSING.preprocessing.section_constants import (
    GENERAL
)


def dividir_por_secciones(documentos):

    resultado = []

    estado = {

        "documento_actual": None,

        "seccion_actual": GENERAL,

        "subtitulo_actual": None,

        "metadata_actual": None,

        "buffer": BufferManager()

    }

    #
    # Guardar el contenido actual del buffer.
    #

    def guardar_buffer():

        if not estado["buffer"].puede_guardarse():
            return

        #
        # Obtener la metadata una sola vez.
        #

        metadata = estado["buffer"].metadata_actual()

        if metadata is None:


            return




        chunks = crear_chunks(

            estado["buffer"].contenido(),

            metadata

        )


        resultado.extend(

            chunks

        )

        estado["buffer"].vaciar()

    #
    # Recorrer documentos.
    #

    for pagina in documentos:

        texto = pagina.page_content


        metadata = pagina.metadata

        #
        # Cambio de documento.
        #

        if metadata.get("source") != estado["documento_actual"]:

            guardar_buffer()

            estado["documento_actual"] = metadata.get("source")

            estado["seccion_actual"] = GENERAL

            estado["subtitulo_actual"] = None

            estado["metadata_actual"] = crear_metadata(
                metadata
            )

        elif estado["buffer"].metadata_actual() is not None:

            #
            # Cambio de página dentro del mismo documento.
            #
            # Se cierra el contenido anterior y se actualizan
            # únicamente los datos físicos de página.
            # La sección y jerarquía actual se conservan.
            #

            guardar_buffer()

            estado["buffer"].actualizar_pagina(
                metadata
            )

            estado["metadata_actual"] = (
                estado["buffer"].metadata_actual()
            )

        lineas = texto.splitlines()

        i = 0

        while i < len(lineas):


            #
            # Detectar sección.
            #

            nueva, encabezado, usadas = detectar_encabezado(
                lineas,
                i
            )


            if (
                nueva is None
                and lineas[i].strip()
            ):
                pass

            if nueva:

                (

                    metadata_actual,

                    seccion_actual,

                    _,

                    _

                ) = procesar_cambio_seccion(

                    nueva,

                    encabezado,

                    metadata,

                    estado["buffer"],

                    estado["seccion_actual"],

                    guardar_buffer

                )

                estado["metadata_actual"] = metadata_actual

                estado["seccion_actual"] = seccion_actual

                estado["subtitulo_actual"] = None


                i += usadas

                continue

            #
            # Detectar subtítulo.
            #

            subtitulo, encabezado, seccion_detectada, usadas = detectar_subseccion(
                lineas,
                i
            )

            if (
                "OBJETIVO" in lineas[i].upper()
                or
                "TIENE POR OBJETIVO" in lineas[i].upper()
            ):
                pass


            if subtitulo:

                (

                    metadata_actual,

                    subtitulo_actual,

                    _

                ) = procesar_subtitulo(

                        subtitulo,

                        encabezado,

                        seccion_detectada,

                        metadata,

                        estado["buffer"],

                        estado["seccion_actual"],

                        estado["subtitulo_actual"],

                        guardar_buffer

                    )



                estado["metadata_actual"] = metadata_actual


                if metadata_actual:

                    estado["seccion_actual"] = (

                        metadata_actual.get("seccion")

                        or estado["seccion_actual"]

                    )

                estado["subtitulo_actual"] = subtitulo_actual



                i += usadas

                continue

            #
            # Línea normal.
            #


            estado["buffer"].agregar_linea(
                lineas[i]
            )


            i += 1

    #
    # Guardar el último buffer.
    #

    guardar_buffer()

    return resultado
