# LLM/rag/document_detector.py

import re
import unicodedata

from LLM.rag.document_registry import (
    DOCUMENTOS,
    DOCUMENTOS_CONCRETOS,
    DOCUMENTOS_POR_ANIO
)


def normalizar_texto(texto):
    """
    Normaliza el texto para facilitar
    la detección de documentos.
    """

    texto = texto.lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(

        c

        for c in texto

        if unicodedata.category(c) != "Mn"

    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def detectar_anio(texto):
    """
    Detecta un año con formato 20XX.
    """

    texto = normalizar_texto(texto)

    match = re.search(
        r"\b20\d{2}\b",
        texto
    )

    return match.group() if match else None


def seleccionar_mejor_coincidencia(coincidencias):
    """
    Selecciona la coincidencia más específica.

    Prioridad:

    1. Mayor cantidad de palabras.
    2. Mayor cantidad de caracteres.

    En el futuro esta función podrá
    considerar:

    - coincidencia exacta del año;
    - prioridad definida en
      document_registry.py;
    - sinónimos.
    """

    return max(

        coincidencias,

        key=lambda c: (

            c["longitud"],

            c["caracteres"]

        )

    )


def detectar_documento(pregunta):
    """
    Detecta el documento mencionado
    en la pregunta.
    """

    texto = normalizar_texto(
        pregunta
    )

    anio = detectar_anio(texto)

    coincidencias = []

    #
    # Buscar todas las coincidencias.
    #

    for termino, nombre in DOCUMENTOS.items():

        termino_normalizado = normalizar_texto(
            termino
        )

        if termino_normalizado in texto:

            coincidencias.append(

                {

                    "termino": termino_normalizado,

                    "documento": nombre,

                    #
                    # Cantidad de palabras.
                    #

                    "longitud": len(
                        termino_normalizado.split()
                    ),

                    #
                    # Cantidad de caracteres.
                    #

                    "caracteres": len(
                        termino_normalizado
                    )

                }

            )

    #
    # No se encontró ningún documento.
    #

    if not coincidencias:

        print(

            "[DOCUMENTO DETECTADO]",

            {

                "pregunta": pregunta,

                "coincidencias": [],

                "seleccionado": None

            }

        )

        return {

            "documento": None,

            "anio": anio

        }

    #
    # Elegir la coincidencia más específica.
    #

    coincidencia = seleccionar_mejor_coincidencia(

        coincidencias

    )

    print(

        "[DOCUMENTO DETECTADO]",

        {

            "pregunta": pregunta,

            "coincidencias": coincidencias,

            "seleccionado": coincidencia

        }

    )

    return {

        "documento": coincidencia["documento"],

        "anio": anio

    }


def detectar_documentos(pregunta):
    """
    Detecta todos los documentos concretos mencionados
    o identificables por año en la pregunta.

    Prioridad:

    1. Familia documental + año.
    2. Familia documental sin año, cuando solo existe
       un documento concreto asociado a esa familia.
    3. Año sin familia, cuando el año identifica
       un único documento.
    """

    texto = normalizar_texto(
        pregunta
    )

    #
    # Años mencionados explícitamente.
    #

    anios = re.findall(
        r"\b20\d{2}\b",
        texto
    )

    anios = list(
        dict.fromkeys(
            anios
        )
    )

    #
    # Familias documentales detectadas.
    #

    familias = []

    for termino, familia in DOCUMENTOS.items():

        termino_normalizado = (
            normalizar_texto(termino)
        )

        if termino_normalizado in texto:

            familias.append(
                {
                    "familia": familia,
                    "termino": termino_normalizado,
                    "posicion": texto.find(
                        termino_normalizado
                    )
                }
            )

    resultados = []

    documentos_agregados = set()

    #
    # 1. Resolver familia + año.
    #

    for familia_info in familias:

        familia = familia_info["familia"]

        documentos_familia = (
            DOCUMENTOS_CONCRETOS.get(
                familia,
                {}
            )
        )

        for anio in anios:

            nombre_documento = (
                documentos_familia.get(anio)
            )

            if not nombre_documento:
                continue

            if nombre_documento in documentos_agregados:
                continue

            resultados.append(
                {
                    "documento": nombre_documento,
                    "anio": anio,
                    "familia": familia,
                    "termino": (
                        familia_info["termino"]
                    ),
                    "posicion": (
                        familia_info["posicion"]
                    )
                }
            )

            documentos_agregados.add(
                nombre_documento
            )

    #
    # 2. Si una familia fue detectada pero no se
    #    indicó un año, usarla solamente cuando
    #    tenga un único documento concreto.
    #

    for familia_info in familias:

        familia = familia_info["familia"]

        documentos_familia = (
            DOCUMENTOS_CONCRETOS.get(
                familia,
                {}
            )
        )

        if len(documentos_familia) != 1:
            continue

        anio, nombre_documento = next(
            iter(
                documentos_familia.items()
            )
        )

        if nombre_documento in documentos_agregados:
            continue

        resultados.append(
            {
                "documento": nombre_documento,
                "anio": anio,
                "familia": familia,
                "termino": (
                    familia_info["termino"]
                ),
                "posicion": (
                    familia_info["posicion"]
                )
            }
        )

        documentos_agregados.add(
            nombre_documento
        )

    #
    # 3. Resolver años que identifican
    #    directamente un documento.
    #

    for anio in anios:

        nombre_documento = (
            DOCUMENTOS_POR_ANIO.get(
                anio
            )
        )

        if not nombre_documento:
            continue

        if nombre_documento in documentos_agregados:
            continue

        resultados.append(
            {
                "documento": nombre_documento,
                "anio": anio,
                "familia": None,
                "termino": None,
                "posicion": texto.find(anio)
            }
        )

        documentos_agregados.add(
            nombre_documento
        )

    #
    # Ordenar según la posición de aparición
    # en la pregunta.
    #

    resultados.sort(
        key=lambda item: (
            item["posicion"]
            if item["posicion"] >= 0
            else float("inf")
        )
    )

    print(
        "[DOCUMENTOS DETECTADOS]",
        {
            "pregunta": pregunta,
            "documentos": resultados
        }
    )

    return resultados
