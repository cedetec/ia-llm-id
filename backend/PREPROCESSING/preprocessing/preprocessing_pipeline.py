# LLM/preprocessing/preprocessing_pipeline.py

from PREPROCESSING.preprocessing.semantic_section_splitter import (
    dividir_por_secciones
)

from PREPROCESSING.preprocessing.enrichment_pipeline import (
    enriquecer_fragmentos
)






def preprocesar_documentos(documentos):


    fragmentos = dividir_por_secciones(documentos)

    if fragmentos:
        pass

    fragmentos = enriquecer_fragmentos(fragmentos)



    if fragmentos:
        pass

    return fragmentos