# LLM/preprocessing/header_processor.py

from Preprocesamiento.preprocessing.metadata_builder import (
    construir_metadata_seccion
)

from Preprocesamiento.preprocessing.section_detector import (
    normalizar_encabezado
)


def procesar_cambio_seccion(

    nueva,

    encabezado,

    metadata,

    buffer_manager,

    seccion_actual,

    guardar_buffer

):
    """
    Procesa un cambio de sección.
    """

    #
    # ¿Es realmente una nueva sección?
    #

    if nueva == seccion_actual:

        return (
            buffer_manager.metadata_actual(),
            seccion_actual,
            None,
            False
        )

    else:

        #
        # Guardar el chunk anterior si corresponde.
        #

        if buffer_manager.puede_guardarse():

            guardar_buffer()

    #
    # Normalizar el encabezado.
    #

    encabezado_original = encabezado

    encabezado = normalizar_encabezado(
        encabezado
    )

    #
    # Construir la metadata.
    #

    if not nueva:

        print(
            "[ERROR] Cambio de sección sin nombre.",
            {
                "encabezado": encabezado
            }
        )

        return (
            None,
            seccion_actual,
            None,
            False
        )

    metadata_actual = construir_metadata_seccion(

        metadata,

        nueva,

        encabezado

    )

    #
    # Depuración de la metadata generada.
    #

    #
    # Reiniciar el buffer.
    #

    buffer_manager.reiniciar(

        metadata_actual,

        nueva,

        encabezado

    )

    return (

        metadata_actual,

        nueva,

        None,

        True

    )
