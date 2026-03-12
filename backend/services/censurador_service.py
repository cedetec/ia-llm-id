# backend/services/censurador_service.py
from __future__ import annotations
import re

# Regex simples (puedes ampliar según tu necesidad)
RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
RE_TEL = re.compile(r"\b(?:\+?56\s?)?(?:9\s?)?\d{4}\s?\d{4}\b")  # Chile móvil típico
RE_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")

# Opcional: IDs largos (cuentas / tokens)
RE_LONG_ID = re.compile(r"\b\d{9,}\b")

def censurar_texto(texto: str, modo_indexado: bool = False) -> str:
    if not texto:
        return ""

    t = texto

    # 🔥 SOLO censurar cuando sea respuesta final
    if not modo_indexado:
        t = RE_EMAIL.sub("[EMAIL]", t)
        t = RE_TEL.sub("[TEL]", t)
        t = RE_RUT.sub("[RUT]", t)

    return t
