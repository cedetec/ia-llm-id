# subsection_processor.py

from PREPROCESSING.preprocessing.metadata_builder import (
    construir_metadata_subtitulo
)

from PREPROCESSING.preprocessing.section_detector import (
    normalizar_encabezado
)

from PREPROCESSING.preprocessing.section_constants import (
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
        pass
            

    #
    # Guardar el buffer anterior si corresponde.
    #

    buffer_manager.guardar_si_corresponde(
        guardar_buffer
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


    #
    # Reiniciar buffer.
    #

    buffer_manager.reiniciar(

        metadata_actual,

        seccion_subtitulo,

        encabezado_original

    )


    return (

        metadata_actual,

        subtitulo,

        True

    )

