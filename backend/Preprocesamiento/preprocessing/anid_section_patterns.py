# LLM/preprocessing/anid_section_patterns.py

import re

from Preprocesamiento.preprocessing.section_constants import *

from Preprocesamiento.preprocessing.section_regex import (
    CENTRO as RX_PRESENTACION_CENTRO,
    PROPUESTA as RX_PROPUESTA,
    CONTINUIDAD as RX_CONTINUIDAD
)


def patron(regex):

    return re.compile(

        rf"""
        ^\s*
        {NUMERACION}
        \s*
        ({regex})
        \s*:?\s*$
        """,

        re.IGNORECASE | re.VERBOSE

    )


PATRONES_ANID = [

    #
    # PRESENTACIÓN DEL CENTRO
    #

    (
        patron(
            r"""
            PRESENTACI[ÓO]N\s+DEL\s+CENTRO
            |
            ANTECEDENTES\s+DEL\s+CENTRO
            |
            DESCRIPCI[ÓO]N\s+DEL\s+CENTRO
            |
            CAPACIDADES\s+DEL\s+CENTRO
            |
            INFRAESTRUCTURA
            |
            GOBERNANZA
            |
            ORGANIZACI[ÓO]N
            |
            EQUIPO
            |
            EQUIPO\s+DE\s+TRABAJO
            |
            INSTITUCI[ÓO]N\s+RESPONSABLE
            |
            ORGANISMO\s+RESPONSABLE
            |
            ENTIDAD\s+EJECUTORA
            |
            AGENCIA\s+NACIONAL\s+DE\s+INVESTIGACI[ÓO]N\s+Y\s+DESARROLLO
            |
            AGENCIA\s+NACIONAL
            |
            ANID
            """
        ),
        PRESENTACION_CENTRO
    ),

    #
    # OBJETIVO DE LA PROPUESTA
    #

    (
        patron(
            r"""
            OBJETIVO\s+DE\s+LA\s+PROPUESTA
            |
            OBJETIVO\s+DEL\s+PROYECTO
            |
            OBJETIVO\s+GENERAL\s+DE\s+LA\s+PROPUESTA
            |
            OBJETIVO\s+GENERAL\s+DEL\s+PROYECTO
            |
            OBJETIVOS?\s+DE\s+LA\s+PROPUESTA
            |
            OBJETIVOS?\s+DEL\s+PROYECTO
            """
        ),
        OBJETIVO_PROPUESTA
    ),

    #
    # PROPUESTA TÉCNICA
    #

    (
        patron(
            r"""
            PROPUESTA\s+T[ÉE]CNICA
            |
            DESCRIPCI[ÓO]N\s+DE\s+LA\s+PROPUESTA
            |
            DESCRIPCI[ÓO]N\s+DE\s+LA\s+PROPUESTA\s+T[ÉE]CNICA
            |
            DESCRIPCI[ÓO]N\s+DEL\s+PROYECTO
            |
            DESCRIPCI[ÓO]N\s+DEL\s+PROGRAMA
            |
            ANTECEDENTES\s+DEL\s+PROGRAMA
            |
            PLAN\s+DE\s+TRABAJO
            |
            PLAN\s+DE\s+ACCI[ÓO]N
            |
            PLAN\s+DE\s+IMPLEMENTACI[ÓO]N
            |
            PROPUESTA\s+DE\s+TRABAJO
            |
            CRONOGRAMA
            |
            ACTIVIDADES
            |
            METODOLOG[IÍ]A
            |
            ESTRATEGIA
            |
            MODELO\s+DE\s+GESTI[ÓO]N
            """
        ),
        PROPUESTA_TECNICA
    ),

    #
    # PLAN DE CONTINUIDAD
    #

    (
        patron(
            r"""
            PLAN\s+DE\s+CONTINUIDAD
            |
            CONTINUIDAD\s+DEL\s+CENTRO
            |
            SOSTENIBILIDAD
            |
            PROYECCI[ÓO]N
            """
        ),
        PLAN_CONTINUIDAD
    ),

    #
    # ANTECEDENTES DE POSTULACIÓN
    #

    (
        patron(
            r"""
            ANTECEDENTES\s+DE\s+POSTULACI[ÓO]N
            |
            PROCESO\s+DE\s+POSTULACI[ÓO]N
            |
            PROCESO\s+DE\s+LA\s+POSTULACI[ÓO]N
            |
            ANTECEDENTES\s+DE\s+LA\s+POSTULACI[ÓO]N
            |
            ANTECEDENTES\s+PARA\s+LA\s+POSTULACI[ÓO]N
            |
            ANTECEDENTES\s+POSTULACI[ÓO]N
            |
            ANTECEDENTES\s+PARA\s+POSTULAR
            |
            DOCUMENTACI[ÓO]N
            |
            DOCUMENTOS?\s+A\s+PRESENTAR
            |
            DOCUMENTOS?\s+DE\s+POSTULACI[ÓO]N
            |
            ANEXOS?\s+DE\s+POSTULACI[ÓO]N
            """
        ),
        ANTECEDENTES_POSTULACION
    ),
    
]
