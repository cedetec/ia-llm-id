# backend/services/consulta/structured_extractors.py

import re
from backend.services.consulta.patterns import (
    PATRON_RESOLUCION,
    PATRON_RES_ABREV
)
from backend.utils.extractores import extraer_numero_resolucion
from backend.utils.extractores_fecha import extraer_fecha_resolucion


def extraer_numero_resolucion_estructurado(pregunta_low, contexto):

    # 🔥 NORMALIZACIÓN GLOBAL (FIX REAL)

    if isinstance(contexto, list):
        partes = []
        for d in contexto:
            if isinstance(d, dict):
                val = d.get("contenido") or d.get("texto")
                if isinstance(val, str):
                    partes.append(val)
            elif isinstance(d, str):
                partes.append(d)
        contexto = " ".join(partes)

    elif isinstance(contexto, dict):
        contexto = (
            contexto.get("contenido")
            or contexto.get("texto")
            or ""
        )

    if not isinstance(contexto, str) or not contexto.strip():
        return None

    # -----------------------------------------
    # 🎯 SOLO SI LA PREGUNTA LO PIDE
    # -----------------------------------------

    if (
        ("numero" in pregunta_low or "número" in pregunta_low)
        and "resol" in pregunta_low
        and "frase" not in pregunta_low
        and "cita" not in pregunta_low
        and "textual" not in pregunta_low
    ):

        # -----------------------------------------
        # 🔎 1. BUSCAR CON REGEX PRINCIPAL
        # -----------------------------------------

        m = PATRON_RESOLUCION.search(contexto)
        if m:
            return m.group(1) if m.groups() else m.group(0)

        # -----------------------------------------
        # 🔎 2. BUSCAR ABREVIADO (RES.)
        # -----------------------------------------

        m = PATRON_RES_ABREV.search(contexto)
        if m:
            return m.group(1) if m.groups() else m.group(0)

        # -----------------------------------------
        # 🔥 3. FALLBACK ROBUSTO
        # -----------------------------------------

        fallback = extraer_numero_resolucion(contexto)
        if fallback:
            return fallback

    return None


def extraer_fecha_si_aplica(pregunta_low, contexto):

    # 🔥 MISMO FIX AQUÍ

    if isinstance(contexto, list):
        partes = []
        for d in contexto:
            if isinstance(d, dict):
                val = d.get("contenido") or d.get("texto")
                if isinstance(val, str):
                    partes.append(val)
            elif isinstance(d, str):
                partes.append(d)
        contexto = " ".join(partes)

    elif isinstance(contexto, dict):
        contexto = (
            contexto.get("contenido")
            or contexto.get("texto")
            or ""
        )

    if any(x in pregunta_low for x in ["fecha", "dd/mm"]):
        fecha = extraer_fecha_resolucion(contexto)
        if fecha:
            return fecha

    return None
