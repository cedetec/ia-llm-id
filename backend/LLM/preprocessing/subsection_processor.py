# subsection_processor.py

from LLM.preprocessing.metadata_builder import (
    construir_metadata_subtitulo
)

from LLM.preprocessing.section_detector import (
    normalizar_encabezado
)

from LLM.preprocessing.section_constants import (
    GENERAL,
    OTRAS_SECCIONES
)


def procesar_subtitulo(

    subtitulo,

    encabezado_original,

    seccion_detectada,

    metadata,

    buffer_manager,

    seccion_actual,

    subtitulo_actual,

    guardar_buffer

):
    """
    Procesa un cambio de subtítulo.
    """

    #
    # Mismo subtítulo.
    #

    if subtitulo == subtitulo_actual:

        print(
            "[INFO] Subtítulo repetido."
        )

        return (

            None,

            subtitulo_actual,

            False

        )

    #
    # Determinar sección.
    #

    encabezado_original = normalizar_encabezado(
        encabezado_original
    )

    if (
        seccion_detectada
        and
        seccion_detectada not in {
            GENERAL,
            OTRAS_SECCIONES
        }
    ):

        seccion_subtitulo = seccion_detectada

    else:

        seccion_subtitulo = seccion_actual

    encabezado_upper = encabezado_original.upper()

    if (
        "OBJETIVO GENERAL" in encabezado_upper
        and
        seccion_detectada != "OBJETIVO_GENERAL"
    ):
        print(
            "[ERROR DETECCION SUBSECCION]",
            {
                "encabezado": encabezado_original,
                "detectada": seccion_detectada,
                "actual": seccion_actual,
                "final": seccion_subtitulo
            }
        )
            
    print(
        "[SUBSECTION SECCION]",
        {
            "detectada": seccion_detectada,
            "actual": seccion_actual,
            "final": seccion_subtitulo,
            "encabezado": encabezado_original
        }
    )

    #
    # Guardar el buffer anterior si corresponde.
    #

    buffer_manager.guardar_si_corresponde(
        guardar_buffer
    )

    print(

        f"[SUBSECTION] "

        f"{subtitulo_actual} -> {subtitulo}"

    )

    #
    # Construir metadata.
    #

    metadata_actual = construir_metadata_subtitulo(

        metadata,

        seccion_subtitulo,

        subtitulo,

        encabezado_original

    )

    print(
        "[SUBSECTION METADATA]",
        {
            "seccion":
                metadata_actual.get("seccion"),

            "titulo_padre":
                metadata_actual.get("titulo_padre"),

            "titulo_hijo":
                metadata_actual.get("titulo_hijo"),

            "subtitulo":
                metadata_actual.get("subtitulo"),

            "numero_seccion":
                metadata_actual.get("numero_seccion"),

            "encabezado":
                metadata_actual.get("encabezado_original")
        }
    )

    #
    # Reiniciar buffer.
    #

    buffer_manager.reiniciar(

        metadata_actual,

        seccion_subtitulo,

        encabezado_original

    )

    print(
        "[SUBSECTION BUFFER]",
        {
            "seccion":
                buffer_manager.metadata.get("seccion"),

            "titulo_padre":
                buffer_manager.metadata.get("titulo_padre"),

            "titulo_hijo":
                buffer_manager.metadata.get("titulo_hijo"),

            "subtitulo":
                buffer_manager.metadata.get("subtitulo"),

            "encabezado":
                buffer_manager.metadata.get("encabezado_original")
        }
    )

    return (

        metadata_actual,

        subtitulo,

        True

    )

