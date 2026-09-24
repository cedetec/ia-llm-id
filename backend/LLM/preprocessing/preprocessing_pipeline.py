# LLM/preprocessing/preprocessing_pipeline.py

from LLM.preprocessing.semantic_section_splitter import (
    dividir_por_secciones
)

from LLM.preprocessing.enrichment_pipeline import (
    enriquecer_fragmentos
)

from LLM.validators.metadata_validator import (
    validar_metadata
)


from LLM.preprocessing.english_chunk_service import (
    enriquecer_chunks_en_ingles
)


def preprocesar_documentos(documentos):

    print(f"[PIPELINE] Documentos entrada: {len(documentos)}")

    fragmentos = dividir_por_secciones(documentos)
    print(f"[PIPELINE] Después de dividir_por_secciones: {len(fragmentos)}")

    if fragmentos:
        print(fragmentos[0].page_content[:300])

    fragmentos = enriquecer_fragmentos(fragmentos)
    print(f"[PIPELINE] Después de enriquecer_fragmentos: {len(fragmentos)}")

    validar_metadata(fragmentos)
    print(f"[PIPELINE] Después de validar_metadata: {len(fragmentos)}")

    fragmentos = enriquecer_chunks_en_ingles(fragmentos)
    print(f"[PIPELINE] Después de enriquecer_chunks_en_ingles: {len(fragmentos)}")

    if fragmentos:
        print("Metadata:")
        print(fragmentos[0].metadata)

    return fragmentos