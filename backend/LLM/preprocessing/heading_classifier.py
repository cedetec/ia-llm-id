# LLM/preprocessing/heading_classifier.py

import re


MAX_PALABRAS_ENCABEZADO = 8

PATRON_NUMERACION = re.compile(
    r"^([IVXLCDM]+\.?|\d+(?:\.\d+)*)",
    re.IGNORECASE
)


def parece_encabezado(texto: str) -> bool:

    primeras = texto.splitlines()[:3]

    if not primeras:
        return False

    candidato = " ".join(

        linea.strip()

        for linea in primeras

    )

    candidato = re.sub(
        r"\s+",
        " ",
        candidato
    ).strip()

    #
    # Un encabezado suele ser corto.
    #

    if len(candidato.split()) > MAX_PALABRAS_ENCABEZADO:
        return False

    #
    # Muchas mayúsculas.
    #

    letras = [

        c

        for c in candidato

        if c.isalpha()

    ]

    if letras:

        porcentaje = sum(

            c.isupper()

            for c in letras

        ) / len(letras)

        if porcentaje >= 0.70:

            return True

    #
    # Numeración romana o arábiga.
    #

    if PATRON_NUMERACION.match(candidato):

        texto_sin_numero = PATRON_NUMERACION.sub(
            "",
            candidato,
            count=1
        ).strip()

        primeras_palabras = texto_sin_numero.split()[:2]

        PALABRAS_TITULO = {

            "objetivo",
            "objetivos",
            "resultado",
            "resultados",
            "requisitos",
            "beneficios",
            "financiamiento",
            "evaluación",
            "evaluacion",
            "criterios",
            "presentación",
            "presentacion",
            "antecedentes",
            "definiciones",
            "plan",
            "propuesta",
            "documentos",
            "postulación",
            "postulacion"

        }

        if primeras_palabras:

            if primeras_palabras[0].lower() in PALABRAS_TITULO:

                return True

    return False
