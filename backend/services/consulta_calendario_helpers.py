# backend/services/consulta_calendario_helpers.py
from __future__ import annotations
import re
from typing import Optional, Tuple
from backend.services.intent_service import extraer_mes, Intent

def es_fecha_valida(valor: str | None) -> bool:
    if not isinstance(valor, str):
        return False

    v = valor.strip()

    # aceptar YYYY-MM-DD o YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return True

    if re.fullmatch(r"\d{4}-\d{2}", v):
        return True

    # aceptar ISO con tiempo
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T.*", v):
        return True

    return False

def valor_es_no_fecha(valor: str | None) -> bool:
    if not isinstance(valor, str):
        return True

    if es_fecha_valida(valor):
        return False

    v = valor.strip().lower()

    estados = (
        "suspend",
        "sin fecha",
        "pendiente",
        "no aplica",
        "por definir",
        "se comunicar",
        "directamente"
    )

    return any(x in v for x in estados)

def frase_estado_fecha(campo: str, valor: str, concurso: str) -> str:
    return f"El concurso “{concurso}” no registra fecha exacta de {campo}; {valor}."

def formatear_fechas(concurso: dict) -> str:
    partes = []
    nombre = concurso.get("concurso", "N/D")

    for campo, etiqueta in [
        ("inicio", "Apertura"),
        ("cierre", "Cierre"),
        ("fallo", "Fallo")
    ]:
        valor = concurso.get(campo)

        if not valor:
            continue

        if valor_es_no_fecha(valor):
            partes.append(
                f"El concurso “{nombre}” no registra fecha exacta de {campo}; {valor}."
            )
        else:
            partes.append(f"• {etiqueta}: {valor}")

    return "\n".join(partes)

def intent_mes(intent: Intent, pregunta_norm: str) -> Tuple[Optional[str], Optional[str]]:
    mes = extraer_mes(pregunta_norm)

    if not mes:
        return None, None

    if intent == Intent.INICIO_POR_MES:
        return "inicio", mes

    if intent == Intent.CIERRE_POR_MES:
        return "cierre", mes

    if intent == Intent.FALLO_POR_MES:
        return "fallo", mes

    return None, None
