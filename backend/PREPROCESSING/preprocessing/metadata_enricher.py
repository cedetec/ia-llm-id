# LLM/preprocessing/metadata_enricher.py

import os

from PREPROCESSING.preprocessing.section_constants import (
    GENERAL
)


def enriquecer_metadata(fragmentos):

    for doc in fragmentos:

        #
        # Documento
        #

        fuente = os.path.basename(

            doc.metadata.get(
                "source",
                ""
            )

        )

        #
        # Página
        #

        pagina = doc.metadata.get(
            "page",
            0
        )

        doc.metadata["documento"] = fuente

        #
        # LangChain usa páginas desde 0.
        #

        doc.metadata["pagina"] = pagina + 1

        #
        # Metadata estructural.
        # Solo inicializar si aún no existe.
        #

        doc.metadata.setdefault(
            "seccion",
            GENERAL
        )

        doc.metadata.setdefault(
            "titulo_padre",
            GENERAL
        )

        doc.metadata.setdefault(
            "titulo_hijo",
            GENERAL
        )

        #
        # Nuevo: subtítulo
        #

        doc.metadata.setdefault(
            "subtitulo",
            ""
        )

        #
        # Encabezado original detectado
        #

        doc.metadata.setdefault(
            "encabezado_original",
            ""
        )

        doc.metadata.setdefault(
            "numero_seccion",
            ""
        )

    return fragmentos

