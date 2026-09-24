# LLM/preprocessing/header_processor.py

from LLM.preprocessing.metadata_builder import (
    construir_metadata_seccion
)

from LLM.preprocessing.section_detector import (
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

    print("=" * 80)
    print("[CAMBIO DE SECCIÓN]")
    print("Nueva:", nueva)
    print("Encabezado:", encabezado)
    print("Sección anterior:", seccion_actual)
    print("=" * 80)

    #
    # ¿Es realmente una nueva sección?
    #

    if nueva == seccion_actual:

        print(
            "[SECTION] Encabezado repetido.",
            {
                "seccion": nueva,
                "encabezado": encabezado
            }
        )

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

            print(
                "[INFO] Buffer todavía no puede guardarse."
            )

        print(
            f"[SECTION] {seccion_actual} -> {nueva}"
        )

    #
    # Normalizar el encabezado.
    #

    encabezado_original = encabezado

    encabezado = normalizar_encabezado(
        encabezado
    )

    if encabezado_original != encabezado:

        print(
            "[HEADER NORMALIZADO]",
            {
                "antes": encabezado_original,
                "despues": encabezado
            }
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

    print(

        "[HEADER METADATA]",

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
    # Reiniciar el buffer.
    #

    habia_contenido = buffer_manager.reiniciar(

        metadata_actual,

        nueva,

        encabezado

    )

    print(
        "[BUFFER REINICIADO]",
        {
            "seccion":
                buffer_manager.metadata.get("seccion"),

            "titulo_padre":
                buffer_manager.metadata.get("titulo_padre"),

            "titulo_hijo":
                buffer_manager.metadata.get("titulo_hijo"),

            "encabezado":
                buffer_manager.metadata.get("encabezado_original")
        }
    )

    #
    # Solo para depuración.
    #

    if habia_contenido:

        print(
            "[INFO] El buffer anterior fue reemplazado."
        )

    return (

        metadata_actual,

        nueva,

        None,

        True

    )
