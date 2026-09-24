# LLM/preprocessing/chunk_builder.py

from LLM.preprocessing.chunk_factory import (
    crear_documento
)

from LLM.preprocessing.chunk_splitter import (
    dividir_subchunks
)

from LLM.preprocessing.chunk_filter import (
    mantener_chunk
)

from LLM.preprocessing.chunk_formatter import (

    inyectar_metadata,

    agregar_prefijo

)

from LLM.validators.section_splitter_validator import (
    validar_chunk
)


def crear_chunks(

    texto,

    metadata

):

    print(

        "[CHUNK METADATA ENTRADA]",

        {

            "documento": metadata.get("documento"),

            "pagina": metadata.get("pagina"),

            "page": metadata.get("page"),

            "source": metadata.get("source"),

            "numero_seccion": metadata.get("numero_seccion"),

            "tipo": metadata.get("tipo"),

            "seccion": metadata.get("seccion"),

            "titulo_padre": metadata.get("titulo_padre"),

            "titulo_hijo": metadata.get("titulo_hijo"),

            "subtitulo": metadata.get("subtitulo"),

            "encabezado_original": metadata.get(
                "encabezado_original"
            )

        }

    )

    print(

        "[BUFFER RECIBIDO]",

        {

            "palabras": len(texto.split()),

            "lineas": len(texto.splitlines()),

            "inicio": " | ".join(

                texto.splitlines()[:5]

            )

        }

    )

    documento = crear_documento(

        texto,

        metadata

    )

    subchunks = dividir_subchunks(

        documento

    )

    if len(subchunks) > 1:

        palabras = len(texto.split())

        print(

            "[CHUNK DIVIDIDO]",

            {

                "seccion": metadata.get("seccion"),

                "subtitulo": metadata.get("subtitulo"),

                "encabezado": metadata.get("encabezado_original"),

                "cantidad": len(subchunks),

                "palabras": palabras

            }

        )

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

        print(
            "[ANTES DE INYECTAR]",
            {
                "documento": metadata.get("documento"),
                "pagina": metadata.get("pagina"),
                "page": metadata.get("page"),
                "source": metadata.get("source")
            }
        )

        chunk = inyectar_metadata(

            chunk,

            metadata

        )

        print(
            "[DESPUÉS DE INYECTAR]",
            {
                "documento": chunk.metadata.get("documento"),
                "pagina": chunk.metadata.get("pagina"),
                "page": chunk.metadata.get("page"),
                "source": chunk.metadata.get("source")
            }
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

        print(

            "[CHUNK METADATA COPIADA]",

            {

                "documento": chunk.metadata.get("documento"),

                "pagina": chunk.metadata.get("pagina"),

                "page": chunk.metadata.get("page"),

                "source": chunk.metadata.get("source"),

                "numero_seccion": chunk.metadata.get("numero_seccion"),

                "tipo": chunk.metadata.get("tipo"),

                "seccion": chunk.metadata.get("seccion"),

                "titulo_padre": chunk.metadata.get("titulo_padre"),

                "titulo_hijo": chunk.metadata.get("titulo_hijo"),

                "subtitulo": chunk.metadata.get("subtitulo"),

                "encabezado_original": chunk.metadata.get("encabezado_original")

            }

        )

        #
        # Filtrar.
        #

        if not mantener_chunk(chunk):

            print(
                "[CHUNK DESCARTADO]",
                {
                    "seccion": chunk.metadata.get("seccion"),
                    "subtitulo": chunk.metadata.get("subtitulo"),
                    "palabras": len(chunk.page_content.split())
                }
            )

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

        print(

    "[CHUNK FINAL]",

        {

            "seccion": chunk.metadata.get("seccion"),

            "titulo_padre": chunk.metadata.get(
                "titulo_padre"
            ),

            "titulo_hijo": chunk.metadata.get(
                "titulo_hijo"
            ),

            "subtitulo": chunk.metadata.get(
                "subtitulo"
            ),

            "encabezado_original": chunk.metadata.get(
                "encabezado_original"
            ),

            "pagina": chunk.metadata.get("pagina"),

            "palabras": len(
                chunk.page_content.split()
            ),

            "inicio": " ".join(
                chunk.page_content.split()[:20]
            ),

            "fin": " ".join(
                chunk.page_content.split()[-20:]
            )

        }

    )

    return resultado
