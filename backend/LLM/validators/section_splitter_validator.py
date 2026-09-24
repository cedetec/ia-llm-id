# LLM/validators/section_splitter_validator.py

from LLM.config.debug_settings import (
    DEBUG_METADATA
)


def validar_chunk(chunk):

    if not DEBUG_METADATA:
        return

    print("\n" + "=" * 90)

    print("CHUNK CREADO")

    print("=" * 90)

    print(

        "Documento :", chunk.metadata.get("documento")

    )

    print(

        "Página    :", chunk.metadata.get("pagina")

    )

    print(

        "Sección   :", chunk.metadata.get("seccion")

    )

    print(

        "Padre     :", chunk.metadata.get("titulo_padre")

    )

    print(

        "Hijo      :", chunk.metadata.get("titulo_hijo")

    )

    print(

        "Subtítulo :", chunk.metadata.get("subtitulo")

    )

    print(

        "Encabezado:",

        chunk.metadata.get("encabezado_original")

    )

    print("-" * 90)

    print(

        chunk.page_content[:300]

    )