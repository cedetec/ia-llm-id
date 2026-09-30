# LLM/preprocessing/preprocessing_pipeline.py

from Preprocesamiento.preprocessing.semantic_section_splitter import (
    dividir_por_secciones
)

from Preprocesamiento.preprocessing.enrichment_pipeline import (
    enriquecer_fragmentos
)

from Preprocesamiento.validators.metadata_validator import (
    validar_metadata
)


from Preprocesamiento.preprocessing.english_chunk_service import (
    enriquecer_chunks_en_ingles
)


def preprocesar_documentos(documentos):

    fragmentos = dividir_por_secciones(documentos)
    fragmentos = enriquecer_fragmentos(fragmentos)
    validar_metadata(fragmentos)
    fragmentos = enriquecer_chunks_en_ingles(fragmentos)
    return fragmentos