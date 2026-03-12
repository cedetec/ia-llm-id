# backend/services/consulta_gates.py
from __future__ import annotations

import re

def pide_objetivo(p_low: str) -> bool:
    return bool(re.search(
        r"\b(objetivo|finalidad|prop[oó]sito|persigue|para\s+qu[eé])\b",
        p_low
    ))

def pide_inventar(p_low: str) -> bool:
    return any(x in p_low for x in ("inventa", "aunque no exista", "aunque no esté", "aunque no este", "aunque no esté en los documentos"))
