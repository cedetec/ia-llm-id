# LLM/preprocessing/chunk_formatter.py

def inyectar_metadata(
    chunk,
    metadata
):
    #
    # Conservar la metadata existente del chunk
    #
    metadata_final = dict(chunk.metadata)

    #
    # Sobrescribir con toda la metadata original
    #
    metadata_final.update(metadata)

    chunk.metadata = metadata_final

    return chunk


def construir_prefijo(

    metadata

):

    contenido = ""

    contenido += (
        f"SECCIÓN: {metadata['seccion']}\n"
    )

    if metadata.get("titulo_padre"):

        contenido += (
            f"TÍTULO PADRE: "
            f"{metadata['titulo_padre']}\n"
        )

    if metadata.get("titulo_hijo"):

        contenido += (
            f"TÍTULO HIJO: "
            f"{metadata['titulo_hijo']}\n"
        )

    if metadata.get("subtitulo"):

        contenido += (
            f"SUBTÍTULO: "
            f"{metadata['subtitulo']}\n"
        )

    if metadata.get("encabezado_original"):

        contenido += (
            f"ENCABEZADO ORIGINAL: "
            f"{metadata['encabezado_original']}\n"
        )

    contenido += "\n"

    return contenido


def agregar_prefijo(

    chunk,

    metadata

):

    chunk.page_content = (

        construir_prefijo(metadata)

        + chunk.page_content

    )

    return chunk
