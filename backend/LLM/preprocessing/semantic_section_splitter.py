# LLM/preprocessing/semantic_section_splitter.py

from LLM.preprocessing.header_detector import (
    detectar_encabezado
)

from LLM.preprocessing.subsection_detector import (
    detectar_subseccion
)

from LLM.preprocessing.buffer_manager import (
    BufferManager
)

from LLM.preprocessing.metadata_builder import (
    crear_metadata
)

from LLM.preprocessing.header_processor import (
    procesar_cambio_seccion
)

from LLM.preprocessing.subsection_processor import (
    procesar_subtitulo
)

from LLM.preprocessing.chunk_builder import (
    crear_chunks
)

from LLM.preprocessing.section_constants import (
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

            print(
                "[BUFFER] Sin metadata, no se guarda."
            )

            return

        print(

            "[BUFFER GUARDAR]",

            {

                "seccion":
                    metadata.get("seccion"),

                "subtitulo":
                    metadata.get("subtitulo"),

                "palabras":
                    len(
                        estado["buffer"]
                        .contenido()
                        .split()
                    )

            }

        )

        print(

            "[CIERRE BUFFER]",

            {

                "lineas":
                    estado["buffer"].lineas(),

                "palabras":
                    estado["buffer"].palabras(),

                "contenido":
                    estado["buffer"]
                    .contenido()[:250]

            }

        )

        print(
            "[METADATA AL GUARDAR]",
            {
                "seccion": metadata.get("seccion"),
                "titulo_padre": metadata.get("titulo_padre"),
                "titulo_hijo": metadata.get("titulo_hijo"),
                "subtitulo": metadata.get("subtitulo"),
                "encabezado_original": metadata.get("encabezado_original")
            }
        )

        chunks = crear_chunks(

            estado["buffer"].contenido(),

            metadata

        )

        print(

            "[CHUNKS CREADOS]",

            len(chunks)

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

        print("=" * 80)
        print("[PAGINA ORIGINAL]")
        print(texto)
        print("=" * 80)

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

            print(
                "[LINEA ANALIZADA]",
                {
                    "indice": i,
                    "linea": lineas[i]
                }
            )

            #
            # Detectar sección.
            #

            nueva, encabezado, usadas = detectar_encabezado(
                lineas,
                i
            )

            print(
                "[RESULTADO DETECTOR]",
                {
                    "nueva": nueva,
                    "encabezado": encabezado,
                    "lineas_consumidas": usadas
                }
            )

            if (
                nueva is None
                and lineas[i].strip()
            ):
                print(
                    "[HEADER NO RECONOCIDO]",
                    {
                        "linea": lineas[i]
                    }
                )

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

                print(
                    "[BUFFER ABIERTO]",
                    {
                        "seccion": estado["seccion_actual"],
                        "subtitulo": estado["subtitulo_actual"]
                    }
                )

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
                print(
                    "[DEBUG OBJETIVO]",
                    {
                        "subtitulo": subtitulo,
                        "encabezado": encabezado,
                        "seccion_detectada": seccion_detectada,
                        "lineas_consumidas": usadas
                    }
                )

            print(
                "[SUBSECCION DETECTADA]",
                {
                    "linea": lineas[i],
                    "subtitulo": subtitulo,
                    "encabezado": encabezado,
                    "seccion_detectada": seccion_detectada
                }
            )

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

                print(
                    "[CAMBIO SUBTITULO]",
                    {
                        "anterior": estado["subtitulo_actual"],
                        "nuevo": subtitulo_actual,
                        "buffer_vacio":
                            estado["buffer"].lineas() == 0
                    }
                )

                print(
                    "[METADATA SUBTITULO]",
                    {
                        "seccion": metadata_actual.get("seccion"),
                        "titulo_padre": metadata_actual.get("titulo_padre"),
                        "titulo_hijo": metadata_actual.get("titulo_hijo"),
                        "subtitulo": metadata_actual.get("subtitulo")
                    }
                )

                estado["metadata_actual"] = metadata_actual

                print(
                    "[ESTADO VS BUFFER]",
                    {
                        "estado": (
                            estado["metadata_actual"].get("seccion")
                            if estado["metadata_actual"]
                            else None
                        ),
                        "buffer": (
                            estado["buffer"].metadata_actual().get("seccion")
                            if estado["buffer"].metadata_actual()
                            else None
                        )
                    }
                )

                if metadata_actual:

                    estado["seccion_actual"] = (

                        metadata_actual.get("seccion")

                        or estado["seccion_actual"]

                    )

                estado["subtitulo_actual"] = subtitulo_actual

                print(
                    "[ESTADO ACTUAL]",
                    {
                        "seccion": estado["seccion_actual"],
                        "subtitulo": estado["subtitulo_actual"]
                    }
                )

                print(
                    "[SUBTITULO ABIERTO]",
                    {
                        "seccion": estado["seccion_actual"],
                        "subtitulo": estado["subtitulo_actual"]
                    }
                )

                i += usadas

                continue

            #
            # Línea normal.
            #

            print(
                "[LINEA NORMAL]",
                {
                    "seccion_actual": estado["seccion_actual"],
                    "texto": lineas[i]
                }
            )

            estado["buffer"].agregar_linea(
                lineas[i]
            )

            print(

                "[BUFFER +]",

                {

                    "linea": lineas[i],

                    "lineas_buffer":

                        estado["buffer"].lineas(),

                    "palabras":

                        estado["buffer"].palabras()

                }

            )

            i += 1

    #
    # Guardar el último buffer.
    #

    guardar_buffer()

    return resultado
