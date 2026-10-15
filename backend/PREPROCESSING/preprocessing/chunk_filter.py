# LLM/preprocessing/chunk_filter.py

from PREPROCESSING.preprocessing.section_constants import (
    GENERAL
)

SECCIONES_CRITICAS = {

    "OBJETIVO_GENERAL",

    "PROPOSITO_CONVOCATORIA",

    "OBJETIVO_PROPUESTA",

    "OBJETIVOS_ESPECIFICOS",

    "REQUISITOS",

    "FINANCIAMIENTO",

    "RESULTADOS_ESPERADOS",

}

MIN_PALABRAS = 80


def mantener_chunk(

    chunk

):

    # Contar cuántas palabras tiene el texto real
    palabras = len(chunk.page_content.split())
    
    # 1. Filtro absoluto: Si tiene menos de 10 palabras (o es un número de página), lo descartamos siempre.
    # Un texto tan corto no le aporta ningún valor semántico al LLM.
    if palabras < 10:
        return False

    seccion = chunk.metadata.get("seccion", GENERAL)

    # 2. Si es una sección muy importante, somos más permisivos y la aceptamos 
    # siempre que haya pasado el filtro absoluto (mínimo 10 palabras).
    if seccion in SECCIONES_CRITICAS:
        return True

    # 3. Para secciones normales, exigimos que sea un fragmento más denso (MIN_PALABRAS).
    return palabras >= MIN_PALABRAS
