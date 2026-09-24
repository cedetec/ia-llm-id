# LLM/preprocessing/header_detector.py

from LLM.preprocessing.section_detector import (
    detectar_seccion,
    normalizar_encabezado
)

from LLM.preprocessing.heading_classifier import (
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

        print("\n================ HEADER RAW ================\n")

        for j in range(indice, min(indice + 4, len(lineas))):

            print(
                j,
                repr(lineas[j])
            )

        print("\n===========================================\n")

        candidato = " ".join(

            linea.strip()

            for linea in lineas[indice:indice + cantidad]

        )

        candidato = normalizar_encabezado(
            candidato
        )

        print(

            "[HEADER CANDIDATO]",

            {

                "lineas": cantidad,

                "texto": candidato

            }

        )

        print(
            "[HEADER -> SECTION]",
            {
                "texto": candidato,
                "longitud": len(candidato),
                "palabras": len(candidato.split())
            }
        )

        if not parece_encabezado(candidato):

            print(
                "[HEADER DESCARTADO]",
                {
                    "texto": candidato,
                    "motivo": "NO_PARECE_ENCABEZADO"
                }
            )

            continue

        seccion = detectar_seccion(
            candidato
        )

        print(
            "[SECTION RESULT]",
            {
                "texto": candidato,
                "seccion": seccion
            }
        )

        if seccion:

            print(

                "[HEADER MATCH]",

                {

                    "texto": candidato,

                    "seccion": seccion,

                    "lineas": cantidad

                }

            )

            print(
                "[HEADER RETURN]",
                {
                    "texto": candidato,
                    "seccion": seccion,
                    "usadas": cantidad
                }
            )

            return (

                seccion,

                candidato,

                cantidad

            )

    print(

        "[HEADER NO MATCH]",

        {

            "indice": indice,

            "texto": lineas[indice].strip()

        }

    )

    return (

        None,

        None,

        1

    )

