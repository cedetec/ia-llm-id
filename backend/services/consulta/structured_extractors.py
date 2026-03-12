# backend/services/consulta/structured_extractors.py

import re
from backend.services.consulta.patterns import (
    PATRON_RESOLUCION,
    PATRON_RES_ABREV
)
from backend.utils.extractores import extraer_numero_resolucion
from backend.utils.extractores_fecha import extraer_fecha_resolucion


def extraer_numero_resolucion_estructurado(pregunta_low, contexto):

    if ("numero" in pregunta_low or "número" in pregunta_low) and "resol" in pregunta_low:

        match = PATRON_RESOLUCION.search(contexto) or PATRON_RES_ABREV.search(contexto)

        if match:
            return match.group(0)

        fallback = extraer_numero_resolucion(contexto)

        if fallback:
            return fallback

    return None


def extraer_fecha_si_aplica(pregunta_low, contexto):

    if any(x in pregunta_low for x in ["fecha", "dd/mm"]):
        fecha = extraer_fecha_resolucion(contexto)
        if fecha:
            return fecha

    return None