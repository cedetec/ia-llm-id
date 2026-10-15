# document_priority.py

from RAG.rag.context_utils import (
    es_objetivo_general
)

from RAG.rag.context_patterns import (

    PATRONES_OBJETIVO_GENERAL,

    PATRONES_OBJETIVOS_ESPECIFICOS,

    PATRONES_ADMINISTRATIVOS

)

SECCIONES_PRIORITARIAS = {
    "OBJETIVO_GENERAL": {
        "OBJETIVO_GENERAL",
        "OBJETIVO_PROPUESTA",
        "OBJETIVOS",
    },

    "OBJETIVOS_ESPECIFICOS": "OBJETIVOS_ESPECIFICOS",

    "REQUISITOS": "REQUISITOS",

    "FINANCIAMIENTO": "FINANCIAMIENTO",

    "BENEFICIOS": "BENEFICIOS",

    "EVALUACION": "EVALUACION",

}

PRIORIDAD_EXACTA = 5
PRIORIDAD_SECUNDARIA = 90
PENALIZACION_ADMINISTRATIVA = 50
PRIORIDAD_TITULO_HIJO = 120
PRIORIDAD_SECCION = 110
PRIORIDAD_DETECTOR = 100
PRIORIDAD_ENCABEZADO = 60
PRIORIDAD_OBJETIVOS_CONCURSO = 125

def encabezado_contiene_patron(encabezado, patrones):
    return any(
        patron in encabezado
        for patron in patrones
    )

PATRONES_OBJETIVOS_CONCURSO = (
    "OBJETIVOS DEL CONCURSO",
    "OBJETIVOS DEL INSTRUMENTO",
)

def calcular_prioridad(

    doc,

    tipo_consulta

):

    seccion = (
        doc.metadata.get(
            "seccion",
            ""
        ).upper()
    )

    titulo_hijo = (
        doc.metadata.get(
            "titulo_hijo",
            ""
        ).upper()
    )

    subtitulo = str(
        doc.metadata.get(
            "subtitulo",
            ""
        )
    )

    encabezado = (
        doc.metadata.get(
            "encabezado_original",
            ""
        ).upper()
    )

    score = 0

    if tipo_consulta == "OBJETIVO_GENERAL":

        if titulo_hijo == "OBJETIVO_GENERAL":
            score += PRIORIDAD_TITULO_HIJO

        elif (
            seccion == "OBJETIVOS"
            and encabezado_contiene_patron(
                encabezado,
                PATRONES_OBJETIVOS_CONCURSO
            )
        ):
            score += PRIORIDAD_OBJETIVOS_CONCURSO

        elif seccion == "OBJETIVO_GENERAL":
            score += PRIORIDAD_SECCION

        elif es_objetivo_general(doc):
            score += PRIORIDAD_DETECTOR

        elif seccion == "PROPOSITO_CONVOCATORIA":
            score += PRIORIDAD_SECUNDARIA

        elif encabezado_contiene_patron(
            encabezado,
            PATRONES_OBJETIVO_GENERAL
        ):
            score += PRIORIDAD_ENCABEZADO
            

    elif tipo_consulta == "OBJETIVOS_ESPECIFICOS":

        if titulo_hijo == "OBJETIVOS_ESPECIFICOS":
            score += PRIORIDAD_TITULO_HIJO

        elif seccion == "OBJETIVOS_ESPECIFICOS":
            score += PRIORIDAD_SECCION

        elif (
            seccion == "OBJETIVOS"
            and
            encabezado_contiene_patron(
                encabezado,
                PATRONES_OBJETIVOS_ESPECIFICOS
            )
        ):
            score += PRIORIDAD_SECUNDARIA

        elif encabezado_contiene_patron(
            encabezado,
            PATRONES_OBJETIVOS_ESPECIFICOS
        ):
            score += PRIORIDAD_ENCABEZADO

    elif tipo_consulta == "REQUISITOS":

        if titulo_hijo == "REQUISITOS":

            score += PRIORIDAD_EXACTA

    if any(

        palabra in encabezado

        for palabra in PATRONES_ADMINISTRATIVOS

    ):

        score -= PENALIZACION_ADMINISTRATIVA


    return score


def existe_seccion_prioritaria(

    documentos,

    tipo_consulta

):
    """
    Indica si entre los documentos recuperados
    existe al menos un chunk perteneciente
    a la sección prioritaria del tipo de consulta.
    """

    seccion_prioritaria = SECCIONES_PRIORITARIAS.get(
        tipo_consulta
    )

    if not seccion_prioritaria:

        return False

    if isinstance(seccion_prioritaria, set):

        return any(

            doc.metadata.get(
                "titulo_hijo",
                ""
            ).upper() in seccion_prioritaria

            or

            doc.metadata.get(
                "seccion",
                ""
            ).upper() in seccion_prioritaria

            for doc in documentos

        )

    return any(

        doc.metadata.get(
            "titulo_hijo",
            ""
        ).upper() == seccion_prioritaria

        or

        doc.metadata.get(
            "seccion",
            ""
        ).upper() == seccion_prioritaria

        for doc in documentos

    )
