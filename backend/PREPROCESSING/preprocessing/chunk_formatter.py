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

    # Retornamos un string vacío para no ensuciar el contenido del texto,
    # ya que la metadata será inyectada de forma óptima por embedding_builder.py
    return ""


def agregar_prefijo(

    chunk,

    metadata

):

    chunk.page_content = (

        construir_prefijo(metadata)

        + chunk.page_content

    )

    return chunk
