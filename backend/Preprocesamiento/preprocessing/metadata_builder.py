# LLM/preprocessing/metadata_builder.py

from copy import deepcopy

from Preprocesamiento.preprocessing.section_detector import (
    obtener_titulo_padre
)

from Preprocesamiento.preprocessing.section_constants import (
    GENERAL
)


def crear_metadata(metadata):

    nueva = deepcopy(metadata)

    nueva.setdefault("seccion", GENERAL)
    nueva.setdefault("titulo_padre", "")
    nueva.setdefault("titulo_hijo", "")
    nueva.setdefault("subtitulo", "")
    nueva.setdefault("numero_seccion", "")
    nueva.setdefault("encabezado_original", "")

    return nueva


def construir_metadata_seccion(

    metadata,

    seccion,

    encabezado

):

    metadata_actual = crear_metadata(metadata)

    metadata_actual["seccion"] = seccion

    metadata_actual["titulo_hijo"] = seccion

    metadata_actual["titulo_padre"] = (
        obtener_titulo_padre(
            seccion
        )
    )

    metadata_actual["encabezado_original"] = (
        encabezado
    )

    #
    # Una sección principal aún no tiene numeración
    # de subtítulo.
    #

    metadata_actual["subtitulo"] = ""

    metadata_actual["numero_seccion"] = ""

    return metadata_actual


def construir_metadata_subtitulo(

    metadata,

    seccion,

    subtitulo,

    encabezado

):

    metadata_actual = crear_metadata(metadata)

    if seccion:

        metadata_actual["seccion"] = seccion

    else:

        metadata_actual["seccion"] = GENERAL

    if encabezado:

        titulo_hijo = encabezado

    else:

        titulo_hijo = seccion

    metadata_actual["titulo_padre"] = (
        obtener_titulo_padre(
            metadata_actual["seccion"]
        )
    )

    metadata_actual["titulo_hijo"] = titulo_hijo

    #
    # Compatibilidad con el resto del pipeline.
    #

    metadata_actual["subtitulo"] = subtitulo

    #
    # Nuevo campo explícito.
    #

    metadata_actual["numero_seccion"] = subtitulo

    metadata_actual["encabezado_original"] = (
        encabezado or ""
    )

    return metadata_actual


def construir_metadata_chunk(

    metadata_actual,

    seccion_actual,

    subtitulo_actual

):

    metadata = deepcopy(
        metadata_actual
    )

    metadata["seccion"] = (

        metadata.get("seccion")

        or

        seccion_actual

        or

        GENERAL

    )

    metadata["titulo_padre"] = (

        metadata.get("titulo_padre")

        or

        obtener_titulo_padre(
            metadata["seccion"]
        )

    )

    metadata["titulo_hijo"] = (

        metadata.get("titulo_hijo")

        or

        metadata["seccion"]

    )

    metadata["subtitulo"] = (

        metadata.get("subtitulo")

        or

        subtitulo_actual

    )

    metadata["numero_seccion"] = (

        metadata.get("numero_seccion")

        or

        metadata["subtitulo"]

    )

    metadata["encabezado_original"] = (
        metadata.get("encabezado_original") or ""
    ).strip()

    #
    # Detectar jerarquías sospechosas.
    #

    if (
        metadata["titulo_padre"]
        == metadata["titulo_hijo"]
        and
        metadata["encabezado_original"]
    ):

        print(
            "[WARNING] Jerarquía sospechosa",
            {
                "titulo_padre": metadata["titulo_padre"],
                "titulo_hijo": metadata["titulo_hijo"],
                "encabezado": metadata["encabezado_original"],
                "seccion": metadata["seccion"]
            }
        )

    for campo in (
        "seccion",
        "titulo_padre",
        "titulo_hijo",
        "subtitulo",
        "numero_seccion",
        "encabezado_original",
    ):
        if campo not in metadata:
            print(
                "[ERROR] Campo inexistente",
                campo
            )
        elif metadata[campo] is None:
            print(
                "[ERROR] Campo None",
                campo
            )

    return metadata
