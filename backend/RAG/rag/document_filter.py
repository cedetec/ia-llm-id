# LLM/rag/document_filter.py

from RAG.rag.document_detector import (
    detectar_documento,
    detectar_documentos
)

from RAG.rag.document_matcher import (
    coincide_documento
)

from RAG.rag.query_type_detector import (
    detectar_tipo_consulta
)

from RAG.rag.document_priority import (
    calcular_prioridad,
    existe_seccion_prioritaria
)

from RAG.rag.rag_constants import (
    MIN_DOCUMENTOS,
    MAX_DOCUMENTOS
)


PALABRAS_CLAVE_CONSULTA = {

    "OBJETIVO_GENERAL": {
        "OBJETIVO",
        "FINALIDAD",
        "PROPÓSITO",
        "PROPOSITO"
    },

    "OBJETIVOS_ESPECIFICOS": {
        "OBJETIVOS ESPECÍFICOS",
        "OBJETIVOS ESPECIFICOS"
    },

    "REQUISITOS": {
        "REQUISITO",
        "POSTULANTE",
        "POSTULACIÓN",
        "POSTULACION"
    }

}


def conservar_general(
    doc,
    tipo_consulta
):

    if (
        doc.metadata.get(
            "seccion",
            ""
        ).upper()
        != "GENERAL"
    ):
        return True

    texto = " ".join(
        [
            doc.metadata.get(
                "titulo_hijo",
                ""
            ),

            doc.metadata.get(
                "encabezado_original",
                ""
            ),

            doc.page_content
        ]
    ).upper()

    palabras = PALABRAS_CLAVE_CONSULTA.get(
        tipo_consulta,
        set()
    )

    return any(
        palabra in texto
        for palabra in palabras
    )


def coincide_con_documentos_objetivo(
    nombre,
    objetivos
):

    for objetivo in objetivos:

        if coincide_documento(
            nombre,
            objetivo["documento"],
            objetivo["anio"]
        ):
            return True

    return False


def filtrar_documentos(
    documentos,
    pregunta,
    documento=None,
    anio=None
):

    #
    # Detectar todos los documentos concretos
    # identificables en la consulta.
    #

    objetivos = detectar_documentos(
        pregunta
    )

    tipo_consulta = detectar_tipo_consulta(
        pregunta
    )

    #
    # Fallback al detector antiguo cuando
    # no se detectan documentos concretos.
    #

    if not objetivos:

        info = detectar_documento(
            pregunta
        )

        if info["documento"] is None:

            return documentos[:8]

        objetivos = [
            {
                "documento":
                    info["documento"],

                "anio":
                    info["anio"]
            }
        ]

    #
    # Filtrar por cualquiera de los documentos
    # objetivo detectados.
    #

    documentos_filtrados = []

    for doc in documentos:

        nombre = doc.metadata.get(
            "documento",
            ""
        )

        coincide = (
            coincide_con_documentos_objetivo(
                nombre,
                objetivos
            )
        )

        if coincide:

            documentos_filtrados.append(
                doc
            )

    #
    # Prioridad por tipo de consulta.
    #

    documentos_filtrados.sort(
        key=lambda doc:
            calcular_prioridad(
                doc,
                tipo_consulta
            ),
        reverse=True
    )

    #
    # Eliminar GENERAL cuando existe
    # una sección prioritaria.
    #

    if existe_seccion_prioritaria(
        documentos_filtrados,
        tipo_consulta
    ):

        documentos_filtrados = [

            doc

            for doc in documentos_filtrados

            if (
                doc.metadata.get(
                    "seccion",
                    ""
                ).upper()
                != "GENERAL"

                or

                conservar_general(
                    doc,
                    tipo_consulta
                )
            )

        ]

    #
    # Limitar cantidad.
    #

    if len(documentos_filtrados) > MAX_DOCUMENTOS:

        documentos_filtrados = (
            documentos_filtrados[
                :MAX_DOCUMENTOS
            ]
        )

    #
    # Si hay pocos, completar únicamente
    # con documentos de los objetivos detectados.
    #

    elif (
        len(documentos_filtrados)
        < MIN_DOCUMENTOS
    ):

        respaldo = []

        for doc in documentos:

            if doc in documentos_filtrados:
                continue

            nombre = doc.metadata.get(
                "documento",
                ""
            )

            if not coincide_con_documentos_objetivo(
                nombre,
                objetivos
            ):
                continue

            respaldo.append(doc)

        documentos_filtrados.extend(
            respaldo[
                :MAX_DOCUMENTOS
                - len(documentos_filtrados)
            ]
        )

    return documentos_filtrados
