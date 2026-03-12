import re

SECCIONES_BASE = [
    "OBJETIVO",
    "OBJETIVOS",
    "REQUISITOS",
    "POSTULACIÓN",
    "BENEFICIARIOS",
    "EVALUACIÓN",
    "FINANCIAMIENTO",
    "ADJUDICACIÓN",
    "VIGENCIA",
    "CONSULTAS",
    "PLAZOS",
]

def normalizar(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto.strip())
    return texto

def detectar_secciones(texto: str):
    texto = normalizar(texto)

    patron = r"""
    (?:
        (?:\b[IVXLCDM]{1,6}\b|\b\d{1,2}\b)[\.\-]?\s+
    )?
    (""" + "|".join(SECCIONES_BASE) + r""")
    \b
    """

    matches = list(re.finditer(patron, texto, re.IGNORECASE | re.VERBOSE))

    if not matches:
        return []

    secciones = []

    for i, m in enumerate(matches):
        inicio = m.start()
        fin = matches[i+1].start() if i+1 < len(matches) else len(texto)

        nombre = m.group(1).lower()
        contenido = texto[inicio:fin]

        secciones.append((nombre, contenido))

    return secciones