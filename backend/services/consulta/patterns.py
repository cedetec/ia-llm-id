# backend/services/consulta/patterns.py

import re

PATRON_RESOLUCION = re.compile(
    r"(resoluci[oó]n\s*(exenta|exento)?\s*(n[°ºo]|nº|n°|numero)?\s*\d{1,5}\s*[/\-.]?\s*\d{4})",
    re.IGNORECASE
)

PATRON_RES_ABREV = re.compile(
    r"(res\.?\s*exenta?\s*(n[°ºo])?\s*\d{1,5}/\d{4})",
    re.IGNORECASE
)