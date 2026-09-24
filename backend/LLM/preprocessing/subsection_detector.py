# LLM/preprocessing/subsection_detector.py

import re

from LLM.preprocessing.section_regex import (
    SECTION_REGEX
)

from LLM.preprocessing.section_detector import (
    normalizar_encabezado
)

from LLM.preprocessing.section_vocabulary import (
    PALABRAS_TITULO,
    PALABRAS_PARRAFO
)

NUM = r"(?:\d+(?:\.\d+)*\.?|\d+\)|[IVXLCDM]+\.?)?"

NUMERO_SUBTITULO = re.compile(
    r"""
    ^
    \s*
    (
        \d+
        (?:\s*\.\s*\d+)*
    )
    (?=\s|$|[:.;-])
    """,
    re.VERBOSE
)


def compilar_patrones():

    patrones = []

    for nombre, regex in SECTION_REGEX.items():

        patrones.append(

            (

                nombre,

                re.compile(

                    rf"""
                    ^\s*
                    {NUM}
                    \s*
                    (?:{regex})
                    (?:\s+.*)?
                    $
                    """,

                    re.IGNORECASE | re.VERBOSE

                )

            )

        )

    patrones.append(

        (

            "ASPECTOS_GENERALES",

            re.compile(

                rf"""
                ^\s*
                {NUM}
                \s*
                ASPECTOS\s+GENERALES
                \s*
                [:.]?
                \s*$
                """,

                re.IGNORECASE | re.VERBOSE

            )

        )

    )

    return patrones


PATRONES = compilar_patrones()


def detectar_subseccion(lineas, indice):
    """
    Intenta detectar subtítulos usando
    3, 2 o 1 líneas.
    """

    for cantidad in (3, 2, 1):

        if indice + cantidad > len(lineas):
            continue

        bloque = lineas[indice:indice + cantidad]

        candidato = " ".join(
            linea.strip()
            for linea in bloque
        )

        candidato = normalizar_encabezado(candidato)

        print("=" * 80)
        print("[SUBSECTION CANDIDATO]")
        print("cantidad:", cantidad)
        print("indice:", indice)
        print("texto:", repr(candidato))
        print("=" * 80)

        if not re.match(
            r"^\s*\d+(?:\.\d+)*",
            candidato
        ):

            encontrado = False

            for nombre, patron in PATRONES:

                if patron.match(candidato):

                    return (
                        "",
                        candidato,
                        nombre,
                        cantidad
                    )

            print(
                "[SUBSECTION DESCARTADA]",
                {
                    "motivo": "SIN_NUMERACION",
                    "texto": candidato
                }
            )

            continue

        m = NUMERO_SUBTITULO.match(candidato)

        numero = ""

        if m:

            numero = m.group(1)

            numero = re.sub(
                r"\s*\.\s*",
                ".",
                numero
            )

            numero = re.sub(
                r"\s+",
                "",
                numero
            )

            numero = numero.strip(".")

            numero = numero.rstrip(".")

        #
        # Si no existe numeración, no considerarlo
        # una subsección.
        #

        if not numero:

            print("[DESCARTADO POR SIN_NUMERACION]", candidato)

            continue

        #
        # La primera palabra después de la numeración
        # debe parecer un encabezado conocido.
        #

        primera_palabra = re.sub(

            r"^\d+(?:\.\d+)*\.?\s*",

            "",

            candidato

        ).split()

        if not primera_palabra:

            continue

        if primera_palabra[0].lower() not in PALABRAS_TITULO:

            print(
                "[SUBSECTION DESCARTADA]",
                {
                    "motivo": "PRIMERA_PALABRA",
                    "palabra": primera_palabra[0],
                    "texto": candidato
                }
            )

            print("[DESCARTADO POR PRIMERA_PALABRA]", candidato)

            continue

        #
        # Nuevo filtro: evitar encabezados demasiado cortos.
        #

        MIN_PALABRAS_ENCABEZADO = 1

        if len(primera_palabra) < MIN_PALABRAS_ENCABEZADO:

            print(
                "[WARNING] Encabezado demasiado corto:",
                candidato
            )

            continue

        texto_lower = candidato.lower()

        if (
            len(candidato.split()) > 20
            and any(
                palabra in texto_lower
                for palabra in PALABRAS_PARRAFO
            )
        ):

            print(
                "[SUBSECTION DESCARTADA]",
                {
                    "motivo": "PALABRA_PARRAFO",
                    "texto": candidato,
                    "palabras": len(candidato.split())
                }
            )

            continue

        MAX_PALABRAS_ENCABEZADO = 15

        if len(candidato.split()) > MAX_PALABRAS_ENCABEZADO:

            print(
                "[SUBSECTION DESCARTADA]",
                {
                    "motivo": "DEMASIADAS_PALABRAS",
                    "palabras": len(candidato.split()),
                    "texto": candidato
                }
            )

            print("[DESCARTADO POR MAX_PALABRAS]", candidato)

            continue

        if candidato.endswith(","):

            print(
                "[WARNING] Candidato termina en coma:",
                candidato
            )

            continue

        for nombre, patron in PATRONES:

            if patron.match(candidato):

                print(

                    "[SUBSECTION MATCH]",

                    {

                        "numero": numero,

                        "texto": candidato,

                        "lineas": cantidad,

                        "seccion": nombre,

                        "patron": patron.pattern

                    }

                )

                return (

                    numero,

                    candidato,

                    nombre,

                    cantidad

                )

    return (

        None,

        None,

        None,

        1

    )
