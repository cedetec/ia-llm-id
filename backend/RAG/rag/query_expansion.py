# LLM/rag/query_expansion.py

from RAG.rag.document_detector import (
    detectar_documentos
)

from RAG.rag.query_type_detector import (
    detectar_tipo_consulta
)

from RAG.rag.expansions import (
    EXPANSIONES_COMUNES,
    EXPANSIONES_DOCUMENTO
)

from RAG.rag.query_expansions import (
    EXPANSIONES_TIPO,
    EXPANSIONES_TIPO_DOCUMENTO,
    MAX_EXPANSIONES_TIPO
)


def agregar_expansiones(
    consulta,
    grupos,
    max_expansiones=None
):

    terminos = consulta.splitlines()

    existentes = {

        termino.strip().lower()

        for termino in terminos

        if termino.strip()

    }

    consulta_lower = consulta.lower()

    for grupo in grupos:

        if any(

            trigger in consulta_lower

            for trigger in grupo["triggers"]

        ):

            agregadas = 0

            for expansion in grupo["expansiones"]:

                if (

                    max_expansiones is not None

                    and agregadas >= max_expansiones

                ):

                    break

                expansion = expansion.strip()

                if expansion.lower() not in existentes:

                    terminos.append(expansion)

                    existentes.add(
                        expansion.lower()
                    )

                    agregadas += 1

    return "\n".join(terminos)


def expandir_consulta(
    pregunta
):

    consulta = pregunta.lower()

    documentos_detectados = detectar_documentos(
        pregunta
    )

    tipo = detectar_tipo_consulta(
        pregunta
    )


    #
    # Agregar siempre las expansiones generales.
    #

    consulta_expandida = agregar_expansiones(
        consulta,
        EXPANSIONES_COMUNES
    )

    #
    # Seleccionar expansiones según el tipo de consulta.
    #
    # Como una consulta puede contener varios documentos,
    # no utilizamos una variable "documento" singular.
    #

    expansiones = EXPANSIONES_TIPO.get(
        tipo,
        []
    )

    existentes = {

        termino.strip().lower()

        for termino in consulta_expandida.splitlines()

        if termino.strip()

    }

    agregadas = []

    for expansion in expansiones[:MAX_EXPANSIONES_TIPO]:

        if expansion.lower() not in existentes:

            consulta_expandida += f"\n{expansion}"

            existentes.add(
                expansion.lower()
            )

            agregadas.append(
                expansion
            )

    #
    # Incorporar todos los documentos detectados.
    #

    if documentos_detectados:

        consulta_expandida += (
            "\n\nDOCUMENTOS DETECTADOS:\n"
        )

        for item in documentos_detectados:

            consulta_expandida += (
                f"- {item['documento']} "
                f"(AÑO: {item['anio']})\n"
            )

    #
    # Expansiones específicas de documentos.
    #
    # Se mantienen solamente para documentos que estén
    # definidos explícitamente en EXPANSIONES_DOCUMENTO.
    #

    for item in documentos_detectados:

        documento = item["documento"]

        if (
            documento in EXPANSIONES_DOCUMENTO
            and tipo is not None
        ):

            grupos = [

                grupo

                for grupo in EXPANSIONES_DOCUMENTO[documento]

                if grupo.get("tipo") == tipo

            ]

            consulta_expandida = agregar_expansiones(

                consulta_expandida,

                grupos

            )



    return consulta_expandida
