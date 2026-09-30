# LLM/preprocessing/section_detector.py

import re

from Preprocesamiento.preprocessing.section_patterns import (
    PATRONES_SECCION
)

from Preprocesamiento.preprocessing.section_constants import (

    OBJETIVOS,
    OBJETIVO_GENERAL,
    OBJETIVOS_ESPECIFICOS,
    PROPOSITO_CONVOCATORIA,
    POSTULANTES,
    REQUISITOS,
    FINANCIAMIENTO,
    BENEFICIOS,
    EVALUACION,
    INTRODUCCION,
    OTRAS_SECCIONES

)

from Preprocesamiento.preprocessing.ocr_corrections import (
    CORRECCIONES_OCR
)

from Preprocesamiento.preprocessing.section_vocabulary import (
    PALABRAS_TITULO,
    PALABRAS_PARRAFO
)

PADRES = {

    OBJETIVO_GENERAL: OBJETIVOS,

    OBJETIVOS_ESPECIFICOS: OBJETIVOS,

    PROPOSITO_CONVOCATORIA: OBJETIVOS,

    POSTULANTES: POSTULANTES,

    REQUISITOS: REQUISITOS,

    FINANCIAMIENTO: FINANCIAMIENTO,

    BENEFICIOS: BENEFICIOS,

    EVALUACION: EVALUACION

}

PATRONES_GENERALES = (

        "FIRMA",

        "CONVENIO",

        "MODIFICACIONES",

        "TÉRMINO",

        "TERMINO",

        "ADJUDICACIÓN",

        "ADJUDICACION",

        "LISTA DE ESPERA",

        "APELACIÓN",

        "APELACION",

        "SEGUIMIENTO",

        "EJECUCIÓN",

        "EJECUCION"

    )


def normalizar_encabezado(texto):
    """
    Normaliza un posible encabezado antes de compararlo
    con los patrones.
    """

    texto = " ".join(
        texto.split()
    )

    #
    # Eliminar signos frecuentes al final
    # (OCR, PDF, etc.)
    #

    texto = re.sub(
        r"[.:;\-]+$",
        "",
        texto
    )

    texto_original = texto

    texto_normalizado = texto

    for origen, destino in CORRECCIONES_OCR.items():

        texto_normalizado = re.sub(
            rf"\b{re.escape(origen)}\b",
            destino,
            texto_normalizado,
            flags=re.IGNORECASE
        )

    #
    # Normalizar numeración.
    #

    texto_normalizado = re.sub(
        r"(?<=\d)\s*\.\s*(?=\d)",
        ".",
        texto_normalizado
    )

    texto_normalizado = re.sub(
        r"^(\d+(?:\.\d+)*)\s*(?=[A-Za-zÁÉÍÓÚÑ])",
        r"\1 ",
        texto_normalizado
    )

    #
    # Eliminar espacios repetidos.
    #

    texto_normalizado = re.sub(
        r"\s+",
        " ",
        texto_normalizado
    )

    #
    # Eliminar espacios antes de ":" y ";"
    #

    texto_normalizado = re.sub(
        r"\s+([:;])",
        r"\1",
        texto_normalizado
    )

    #
    # Eliminar signos frecuentes al final.
    #

    texto_normalizado = re.sub(
        r"[.:;\-]+$",
        "",
        texto_normalizado
    )

    #
    # Eliminar puntos repetidos.
    #

    texto_normalizado = re.sub(
        r"\.{2,}$",
        "",
        texto_normalizado
    )

    texto_normalizado = texto_normalizado.strip()

    return texto_normalizado


def buscar_seccion(texto):

    for patron, nombre in PATRONES_SECCION:

        if patron.match(texto):

            return nombre

    return None


def parece_encabezado_valido(texto):
    """
    Filtra textos que claramente no corresponden
    a encabezados.
    """

    if not texto:
        return False

    texto = texto.strip()

    #
    # Solo un número.
    #

    if re.fullmatch(
        r"\d+",
        texto
    ):
        return False

    #
    # Solo numeración.
    #

    if re.fullmatch(
        r"\d+(?:\.\d+)*\.?",
        texto
    ):
        return False

    #
    # Muy largo.
    #

    if len(texto.split()) > 14:
        return False

    #
    # Debe contener letras.
    #

    if not re.search(
        r"[A-Za-zÁÉÍÓÚÑáéíóúñ]",
        texto
    ):
        return False

    #
    # Página X de Y
    #

    if re.fullmatch(
        r"\d+\s+de\s+\d+",
        texto,
        re.IGNORECASE
    ):
        return False

    #
    # Años sueltos.
    #

    if re.fullmatch(
        r"\d{4}",
        texto
    ):
        return False

    #
    # Evitar frases que comienzan con un número
    # seguido de texto normal.
    #

    if re.match(
        r"^\d+\s+de\s+",
        texto,
        re.IGNORECASE
    ):
        return False

    #
    # Encabezados institucionales
    #

    texto_lower = texto.lower()

    descartar = (

        "gobierno de chile",

        "ministerio",

        "anid",

        "ingeniería 2030",

        "tercera etapa",

        "www.",

        "http"

    )

    if any(
        x in texto_lower
        for x in descartar
    ):
        return False

    return True


def detectar_seccion(texto):
    """
    Detecta la sección correspondiente a un bloque
    de texto.
    Puede recibir una o varias líneas.
    """

    if not texto:
        return None

    primeras_lineas = texto.splitlines()[:4]

    #
    # Construir un bloque unificado eliminando
    # líneas vacías y espacios extra.
    #

    bloque = " ".join(

        linea.strip()

        for linea in primeras_lineas

        if linea.strip()

    )

    bloque = normalizar_encabezado(
        bloque
    )

    if not parece_encabezado_valido(
        bloque
    ):
        return None

    #
    # Evitar detectar únicamente numeración.
    #

    if re.fullmatch(
        r"[IVXLCDM]+\.?",
        bloque,
        re.IGNORECASE
    ):

        return None

    if re.fullmatch(
        r"\d+(?:\.\d+)*\.?",
        bloque
    ):

        return None

    encabezado = bloque
    #
    # La primera palabra debe corresponder a un
    # encabezado conocido.
    #

    primera_palabra = re.sub(
        r"^\d+(?:\.\d+)*\.?\s*",
        "",
        encabezado
    ).split()

    primera_palabra_valida = False

    if primera_palabra:

        if primera_palabra[0].lower() in PALABRAS_TITULO:

            primera_palabra_valida = True

    texto_lower = encabezado.lower()

    encabezado = encabezado.replace(":", "")
    encabezado = encabezado.replace("-", " ")

    seccion_bloque = buscar_seccion(encabezado)

    #
    # Si el encabezado proviene de varias líneas,
    # intentar primero cada línea por separado.
    #

    if len(primeras_lineas) > 1:

        mejor = None

        for linea in primeras_lineas:

            linea = normalizar_encabezado(linea)

            s = buscar_seccion(linea)

            if s:

                mejor = s

                break

        if mejor:
            return mejor

    if seccion_bloque:
        return seccion_bloque

    encabezado = bloque.upper()

    #
    # Último intento: revisar línea por línea.
    #

    for linea in primeras_lineas:

        linea = normalizar_encabezado(linea)

        seccion = buscar_seccion(linea)

        if seccion:

            return seccion

    #
    # Fallback para encabezados institucionales
    # frecuentes en concursos ANID.
    #

    if any(

        patron in encabezado

        for patron in (

            "AGENCIA NACIONAL",

            "AGENCIA NACIONAL DE INVESTIGACIÓN",

            "AGENCIA NACIONAL DE INVESTIGACION",

            "AGENCIA NACIONAL DE INVESTIGACIÓN Y DESARROLLO",

            "AGENCIA NACIONAL DE INVESTIGACION Y DESARROLLO",

            "ANID",

            "MINISTERIO",

            "INSTITUCIÓN RESPONSABLE",

            "INSTITUCION RESPONSABLE",

            "ORGANISMO RESPONSABLE",

            "ENTIDAD EJECUTORA"

        )

    ):

        return INTRODUCCION

    if any(

        re.match(
            rf"^(?:\d+(?:\.\d+)*\s+)?{re.escape(palabra)}\b",
            encabezado,
            re.IGNORECASE
        )

        for palabra in PATRONES_GENERALES

    ):

        return OTRAS_SECCIONES


    #
    # Último recurso:
    # Solo considerar OTRAS_SECCIONES si realmente
    # parece un encabezado.
    #

    if (

        len(bloque.split()) <= 12

        and primera_palabra_valida

        and bloque == bloque.upper()

    ):

        return OTRAS_SECCIONES

    return None


def obtener_titulo_padre(seccion):

    return PADRES.get(
        seccion,
        seccion
    )
