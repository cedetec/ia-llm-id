# LLM/preprocessing/enrichment_pipeline.py

from LLM.preprocessing.metadata_enricher import (
    enriquecer_metadata
)

from LLM.preprocessing.contextual_chunk_service import (
    enriquecer_chunks
)


def enriquecer_fragmentos(fragmentos):

    fragmentos = enriquecer_metadata(
        fragmentos
    )

    fragmentos = enriquecer_chunks(
        fragmentos
    )

    return fragmentos