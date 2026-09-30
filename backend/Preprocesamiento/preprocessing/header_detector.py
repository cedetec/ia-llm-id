# LLM/preprocessing/header_detector.py

from Preprocesamiento.preprocessing.section_detector import (
    detectar_seccion,
    normalizar_encabezado
)

from Preprocesamiento.preprocessing.heading_classifier import (
    parece_encabezado
)


def detectar_encabezado(

    lineas,

    indice

):
    """
    Intenta detectar encabezados usando
    3, 2 o 1 líneas.
    """

    for cantidad in (4, 3, 2, 1):

        if indice + cantidad > len(lineas):
            continue

        candidato = " ".join(

            linea.strip()

            for linea in lineas[indice:indice + cantidad]

        )

        candidato = normalizar_encabezado(
            candidato
        )

        if not parece_encabezado(candidato):

            continue

        seccion = detectar_seccion(
            candidato
        )

        if seccion:

            return (

                seccion,

                candidato,

                cantidad

            )

    return (

        None,

        None,

        1

    )
