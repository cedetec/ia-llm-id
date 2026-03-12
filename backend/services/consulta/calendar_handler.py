# backend/services/consulta/calendar_handler.py

from backend.services.calendario_service import (
    concursos_abiertos_hoy,
    concursos_por_mes,
    buscar_concurso,
)
from backend.services.consulta_calendario_helpers import formatear_fechas, intent_mes
from backend.services.intent_service import Intent


def manejar_calendario(intent, pregunta_norm):

    if intent == Intent.ABIERTOS:
        abiertos = concursos_abiertos_hoy()
        if not abiertos:
            return {"respuesta": "No hay concursos abiertos actualmente.", "fuente": "Calendario"}

        lista = "\n".join(
            f"• {c['concurso']} (cierra {c.get('cierre','N/D')})"
            for c in abiertos
        )
        return {"respuesta": lista, "fuente": "Calendario"}

    campo, mes = intent_mes(intent, pregunta_norm)

    if campo:
        if not mes:
            return {"respuesta": "Debes indicar un mes válido.", "fuente": "Calendario"}

        concursos = concursos_por_mes(mes, campo)

        if not concursos:
            return {"respuesta": f"No hay concursos con {campo} en {mes}.", "fuente": "Calendario"}

        lista = "\n".join(
            f"• {c['concurso']} ({campo}: {c[campo]})"
            for c in concursos
        )

        return {"respuesta": lista, "fuente": "Calendario"}

    return None