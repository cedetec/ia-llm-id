# LLM/rag/noise_filter.py

ADMINISTRATIVOS = {

    "INICIO TRANSCRIPCIÓN",
    "DEPTO. JURÍDICO",
    "RESUELVO",
    "VISTOS",
    "CONSIDERANDO",
    "APRUÉBASE",
    "CERTIFICO",
    "MEMORÁNDUM"

}


def filtrar_ruido(documentos):

    documentos_filtrados = []

    for doc in documentos:

        seccion = (
            doc.metadata.get(
                "seccion",
                ""
            ).upper()
        )

        encabezado = (
            doc.metadata.get(
                "encabezado_original",
                ""
            ).upper()
        )

        if any(

            palabra in encabezado

            for palabra in ADMINISTRATIVOS

        ):

            continue

        if (

            seccion == "GENERAL"

            and

            len(doc.page_content.split()) < 60

            and

            any(

                palabra in encabezado

                for palabra in ADMINISTRATIVOS

            )

        ):

            continue

        documentos_filtrados.append(doc)

    return documentos_filtrados