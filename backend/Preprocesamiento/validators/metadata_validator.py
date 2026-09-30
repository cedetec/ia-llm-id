# LLM/validators/metadata_validator.py

import re

from RAG.config.debug_settings import (
    DEBUG_METADATA
)

CAMPOS_OBLIGATORIOS = [

    "documento",
    "pagina",
    "seccion"

]


def validar_metadata(documentos):

    if not DEBUG_METADATA:
        return

    print("\n================ VALIDANDO METADATA ================\n")

    errores = 0

    advertencias = 0

    for i, doc in enumerate(documentos):

        metadata = doc.metadata

        #
        # Campos obligatorios
        #

        faltantes = [

            campo

            for campo in CAMPOS_OBLIGATORIOS

            if campo not in metadata

        ]

        if faltantes:

            errores += 1

            print("=" * 80)
            print(f"Chunk {i}")
            print("Metadata incompleta")
            print(metadata)
            print(f"Faltan: {faltantes}")

        #
        # Validaciones semánticas
        #

        seccion = str(
            metadata.get(
                "seccion",
                ""
            )
        ).upper()

        titulo_padre = str(
            metadata.get(
                "titulo_padre",
                ""
            )
        ).upper()

        titulo_hijo = str(
            metadata.get(
                "titulo_hijo",
                ""
            )
        ).upper()

        subtitulo = str(
            metadata.get(
                "subtitulo",
                ""
            )
        ).strip()

        encabezado = str(
            metadata.get(
                "encabezado_original",
                ""
            )
        ).strip()

        #
        # OBJETIVO_GENERAL debería tener subtítulo.
        #

        if (

            seccion == "OBJETIVO_GENERAL"

            and not subtitulo

        ):

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "OBJETIVO_GENERAL sin subtítulo."
            )
            print(metadata)

        #
        # OBJETIVOS_ESPECIFICOS debería tener subtítulo.
        #

        if (

            seccion == "OBJETIVOS_ESPECIFICOS"

            and not subtitulo

        ):

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "OBJETIVOS_ESPECIFICOS sin subtítulo."
            )
            print(metadata)

        #
        # GENERAL sin encabezado.
        #

        if (

            seccion == "GENERAL"

            and not encabezado

        ):

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "GENERAL sin encabezado original."
            )
            print(metadata)

        #
        # Tiene subtítulo pero quedó GENERAL.
        #

        if (

            subtitulo

            and seccion == "GENERAL"

        ):

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "Tiene subtítulo pero quedó como GENERAL."
            )
            print(metadata)

        #
        # Encabezado numerado sin subtítulo.
        #

        if (

            encabezado

            and re.match(

                r"^\d+(?:\.\d+)*",

                encabezado

            )

            and not subtitulo

        ):

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "Encabezado numerado sin subtítulo."
            )
            print(metadata)

        #
        # Debe existir título hijo.
        #

        if not titulo_hijo:

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print("Título hijo vacío.")
            print(metadata)

        #
        # Debe existir título padre.
        #

        if not titulo_padre:

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print("Título padre vacío.")
            print(metadata)

        #
        # Debe existir encabezado original.
        #

        if not encabezado:

            advertencias += 1

            print("=" * 80)
            print(f"[WARNING] Chunk {i}")
            print(
                "Encabezado original vacío."
            )
            print(metadata)

        #
        # Coherencia entre sección y título hijo.
        #

        if (

            titulo_hijo

            and seccion

            and titulo_hijo != "GENERAL"

            and titulo_hijo != seccion

        ):

            print("=" * 80)
            print(f"[INFO] Chunk {i}")
            print(
                "Título hijo distinto de la sección."
            )
            print(
                f"{titulo_hijo} != {seccion}"
            )

    #
    # Resumen final
    #

    print("\n================ RESUMEN ================\n")

    if errores == 0:

        print(
            "✓ Toda la metadata obligatoria es válida."
        )

    else:

        print(
            f"⚠ {errores} errores encontrados."
        )

    if advertencias:

        print(
            f"⚠ {advertencias} advertencias semánticas."
        )

    else:

        print(
            "✓ No se detectaron advertencias semánticas."
        )

    print(
        f"Chunks revisados: {len(documentos)}"
    )
