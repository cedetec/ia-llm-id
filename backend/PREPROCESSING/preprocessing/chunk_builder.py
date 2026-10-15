# LLM/preprocessing/chunk_builder.py

from PREPROCESSING.preprocessing.chunk_factory import (
    crear_documento
)

from PREPROCESSING.preprocessing.chunk_splitter import (
    dividir_subchunks
)

from PREPROCESSING.preprocessing.chunk_filter import (
    mantener_chunk
)

from PREPROCESSING.preprocessing.chunk_formatter import (

    inyectar_metadata,

    agregar_prefijo

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
            pass


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
                pass


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
                pass


            elif chunk.metadata.get(campo) is None:
                pass


        #
        # Validaciones existentes.
        #

        if not chunk.metadata.get("seccion"):
            pass


        if not chunk.metadata.get("titulo_hijo"):
            pass


        if not chunk.metadata.get("encabezado_original"):
            pass



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


        resultado.append(

            chunk

        )


    return resultado
