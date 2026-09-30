# LLM/preprocessing/chunk_builder.py

from Preprocesamiento.preprocessing.chunk_factory import (
    crear_documento
)

from Preprocesamiento.preprocessing.chunk_splitter import (
    dividir_subchunks
)

from Preprocesamiento.preprocessing.chunk_filter import (
    mantener_chunk
)

from Preprocesamiento.preprocessing.chunk_formatter import (

    inyectar_metadata,

    agregar_prefijo

)

from Preprocesamiento.validators.section_splitter_validator import (
    validar_chunk
)


def crear_chunks(

    texto,

    metadata

):

    documento = crear_documento(

        texto,

        metadata

    )

    subchunks = dividir_subchunks(

        documento

    )

    if len(subchunks) > 1:

        palabras = len(texto.split())

        if palabras < 500:

            print(

                "[WARNING] División inesperada",

                {

                    "palabras": palabras,

                    "subchunks": len(subchunks)

                }

            )

    resultado = []

    for chunk in subchunks:

        #
        # Copiar metadata.
        #

        chunk = inyectar_metadata(

            chunk,

            metadata

        )

        #
        # Comparar metadata original vs metadata del chunk.
        #

        for campo in (

            "documento",

            "pagina",

            "page",

            "source",

            "numero_seccion",

            "tipo",

            "seccion",

            "titulo_padre",

            "titulo_hijo",

            "subtitulo",

            "encabezado_original"

        ):

            if chunk.metadata.get(campo) != metadata.get(campo):

                print(

                    "[WARNING] Metadata modificada",

                    {

                        "campo": campo,

                        "original": metadata.get(campo),

                        "chunk": chunk.metadata.get(campo)

                    }

                )

        #
        # Verificar campos inexistentes o con valor None.
        #

        for campo in (

            "documento",

            "pagina",

            "page",

            "source",

            "numero_seccion",

            "tipo",

            "seccion",

            "titulo_padre",

            "titulo_hijo",

            "subtitulo",

            "encabezado_original"

        ):

            if campo not in chunk.metadata:

                print(

                    "[ERROR] Campo inexistente",

                    campo

                )

            elif chunk.metadata.get(campo) is None:

                print(

                    "[ERROR] Campo con valor None",

                    campo

                )

        #
        # Validaciones existentes.
        #

        if not chunk.metadata.get("seccion"):

            print(

                "[ERROR] Chunk sin sección."

            )

        if not chunk.metadata.get("titulo_hijo"):

            print(

                "[ERROR] Chunk sin título."

            )

        if not chunk.metadata.get("encabezado_original"):

            print(

                "[WARNING] Chunk sin encabezado original."

            )

        #
        # Filtrar.
        #

        if not mantener_chunk(chunk):

            continue

        #
        # Agregar contexto.
        #

        chunk = agregar_prefijo(

            chunk,

            metadata

        )

        #
        # Validación.
        #

        validar_chunk(

            chunk

        )

        resultado.append(

            chunk

        )

    return resultado
