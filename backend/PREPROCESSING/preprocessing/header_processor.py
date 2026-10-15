# LLM/preprocessing/header_processor.py

from PREPROCESSING.preprocessing.metadata_builder import (
    construir_metadata_seccion
)

from PREPROCESSING.preprocessing.section_detector import (
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

        else:
            pass



    #
    # Normalizar el encabezado.
    #

    encabezado_original = encabezado

    encabezado = normalizar_encabezado(
        encabezado
    )

    if encabezado_original != encabezado:
        pass


    #
    # Construir la metadata.
    #

    if not nueva:


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

    habia_contenido = buffer_manager.reiniciar(

        metadata_actual,

        nueva,

        encabezado

    )


    #
    # Solo para depuración.
    #

    if habia_contenido:
        pass


    return (

        metadata_actual,

        nueva,

        None,

        True

    )
