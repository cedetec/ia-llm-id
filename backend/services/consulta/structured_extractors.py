# backend/services/consulta/structured_extractors.py

import re
from services.consulta.patterns import (
    PATRON_RESOLUCION,
    PATRON_RES_ABREV
)
from utils.extractores import extraer_numero_resolucion
from utils.extractores_fecha import extraer_fecha_resolucion

def normalizar_contexto(contexto):

    if isinstance(contexto, list):
        return " ".join(
            d.get("contenido", "") if isinstance(d, dict) else str(d)
            for d in contexto
        )

    if isinstance(contexto, dict):
        return contexto.get("contenido") or contexto.get("texto") or ""

    if isinstance(contexto, str):
        return contexto

    return ""

def extraer_numero_resolucion_estructurado(pregunta_low, contexto):

    if not isinstance(pregunta_low, str):
        return None

    contexto = normalizar_contexto(contexto)

    if not contexto:
        return None

    contexto = str(contexto)

    # 🔥 FIX OCR
    contexto = re.sub(r'(?<=\d)[lI](?=\d)', '1', contexto)

    # 🔥 NORMALIZACIÓN PREGUNTA
    p = pregunta_low.lower()
    p = p.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")

    if (
        "numero" in p
        and "resol" in p
        and "frase" not in p
        and "cita" not in p
        and "textual" not in p
    ):

        m = PATRON_RESOLUCION.search(contexto)
        if m:
            return m.group(1) if m.lastindex else m.group(0)

        m = PATRON_RES_ABREV.search(contexto)
        if m:
            return m.group(1) if m.lastindex else m.group(0)

        fallback = extraer_numero_resolucion(contexto)
        if fallback:
            return fallback

    return None

def extraer_fecha_si_aplica(pregunta_low, contexto):
    
    # 🔥 FIX GLOBAL PREGUNTA
    if not isinstance(pregunta_low, str):
        return None

    contexto = normalizar_contexto(contexto)

    if any(x in pregunta_low for x in ["fecha", "dd/mm"]):
        fecha = extraer_fecha_resolucion(contexto)
        if fecha:
            return fecha

    return None
