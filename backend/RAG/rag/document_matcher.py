# LLM/rag/document_matcher.py

import re
import unicodedata

STOPWORDS = {

    "A",
    "AL",
    "DE",
    "DEL",
    "LA",
    "LAS",
    "EL",
    "LOS",
    "Y",
    "E",
    "O",
    "U",
    "PARA",
    "POR",
    "CON",
    "EN"

}

def normalizar_nombre(texto):

    if not texto:
        return ""

    #
    # Mayúsculas
    #

    texto = texto.upper()

    #
    # Eliminar acentos
    #

    texto = "".join(

        c

        for c in unicodedata.normalize(
            "NFD",
            texto
        )

        if unicodedata.category(c) != "Mn"

    )

    #
    # Eliminar extensión PDF
    #

    texto = re.sub(
        r"\.PDF$",
        "",
        texto
    )

    #
    # Guiones y guiones bajos → espacio
    #

    texto = re.sub(
        r"[-_]+",
        " ",
        texto
    )

    #
    # Espacios múltiples
    #

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    return texto

def coincide_documento(

    documento_chunk,

    documento_consulta,

    anio

):

    documento_chunk = normalizar_nombre(
        documento_chunk
    )

    documento_consulta = normalizar_nombre(
        documento_consulta
    )

    #
    # Eliminar palabras demasiado cortas
    # (A, DE, DEL, LA, EL, etc.).
    #

    tokens = [

        token

        for token in documento_consulta.split()

        if (
            len(token) >= 3
            and token not in STOPWORDS
        )

    ]

    coinciden = sum(

        token in documento_chunk

        for token in tokens

    )

    porcentaje = (

        coinciden / len(tokens)

        if tokens

        else 0

    )


    #
    # Aceptar cuando al menos el 60% de las
    # palabras importantes coincidan.
    #

    if porcentaje < 0.60:

        return False

    if (

        anio is not None

        and

        str(anio) not in documento_chunk

    ):

        return False

    return True

