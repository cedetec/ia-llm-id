# context_patterns.py

#
# ============================================================
# PATRONES DE ENCABEZADOS
# ============================================================
#

#
# Encabezados que identifican claramente
# el objetivo principal del concurso.
#

PATRONES_ENCABEZADO_OBJETIVO_GENERAL = (
    "OBJETIVO GENERAL",
    "EL OBJETIVO DE ESTE CONCURSO",
    "OBJETIVO DEL CONCURSO",
    "OBJETIVO DEL INSTRUMENTO",
    "OBJETIVO PRINCIPAL",
    "OBJETIVO CENTRAL",
    "FINALIDAD DEL CONCURSO",
)

PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS = (
    "OBJETIVOS ESPECÍFICOS",
    "OBJETIVOS ESPECIFICOS",
    "OBJETIVOS ESPECIALES",
)

#
# ============================================================
# PATRONES DE CONTENIDO
# ============================================================
#

#
# Frases que suelen aparecer dentro del contenido
# cuando el chunk describe el objetivo principal.
#

PATRONES_CONTENIDO_OBJETIVO_GENERAL = (
    "EL OBJETIVO DE ESTE CONCURSO",
    "EL OBJETIVO DEL CONCURSO",
    "TIENE POR OBJETIVO",
    "TIENE COMO OBJETIVO",
    "TIENE COMO PROPÓSITO",
    "TIENE COMO PROPOSITO",
    "TIENE COMO FINALIDAD",
    "CUYO OBJETIVO ES",
    "OBJETIVO GENERAL",
    "OBJETIVO DEL CONCURSO",
    "OBJETIVO DEL INSTRUMENTO",
    "FINALIDAD DEL CONCURSO",
)


#
# ============================================================
# COMPATIBILIDAD CON EL CÓDIGO EXISTENTE
# ============================================================
#

#
# Se mantiene para no romper módulos que aún
# utilizan PATRONES_OBJETIVO.
#

PATRONES_OBJETIVO = (

    *PATRONES_ENCABEZADO_OBJETIVO_GENERAL,

)

#
# ============================================================
# PATRONES ADMINISTRATIVOS
# ============================================================
#

PATRONES_ADMINISTRATIVOS = (

    "MEMORÁNDUM",

    "CERTIFICADO",

    "RESOLUCIÓN",

    "ANEXO",

    "CONVENIO",

    "FIRMA",

)

# ============================================================
# ALIASES PARA COMPATIBILIDAD CON document_priority.py
# ============================================================

PATRONES_OBJETIVO_GENERAL = PATRONES_ENCABEZADO_OBJETIVO_GENERAL

PATRONES_OBJETIVOS_ESPECIFICOS = (
    PATRONES_ENCABEZADO_OBJETIVOS_ESPECIFICOS
)
