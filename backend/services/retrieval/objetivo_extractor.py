# backend/services/retrieval/objetivo_extractor.py

from __future__ import annotations
import re
from typing import Optional, Dict


# ==============================
# UTILIDADES
# ==============================

def limpiar_texto(s: str) -> str:
    s = re.sub(r"^\s*\[DOC=.*?\]\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()


def tiene_relleno(s: str) -> bool:
    return bool(re.search(r"\.{8,}|_{6,}|-{6,}|…{3,}", s))


def es_objetivo_proyecto(s: str) -> bool:
    sl = s.lower()
    señales = (
        "proyecto adjudicado",
        "objetivo general del proyecto",
        "objetivo del proyecto",
        "la propuesta",
        "iniciativa",
    )
    return any(x in sl for x in señales)


def score_objetivo(s: str) -> int:
    sl = s.lower()
    score = 0

    if "objetivo general del concurso" in sl:
        score += 20
    if "objetivo general" in sl:
        score += 5
    if "concurso" in sl:
        score += 3

    if tiene_relleno(s):
        score -= 40
    if es_objetivo_proyecto(s):
        score -= 60

    blacklist = (
        "presupuesto",
        "gastos",
        "rendición",
        "factura",
        "boleta",
    )
    if any(w in sl for w in blacklist):
        score -= 20

    L = len(s)
    if 80 <= L <= 350:
        score += 2
    if L > 500:
        score -= 5

    return score


# ==============================
# EXTRACTOR PRINCIPAL
# ==============================

def extraer_cita_objetivo(contexto: str) -> Optional[Dict[str, str]]:

    if not contexto:
        return None

    low = contexto.lower()

    patrones = [
        r"\bobjetivo\s+general\s+del\s+concurso\b",
        r"\bobjetivo\s+general\b",
        r"\btiene\s+por\s+objeto\b",
        r"\bprop[oó]sito\b",
        r"\bfinalidad\b",
    ]

    mejor = None
    mejor_score = -10**9

    for pat in patrones:
        for match in re.finditer(pat, low):
            idx = match.start()

            ventana = contexto[max(0, idx - 150): idx + 600]
            partes = re.split(r"(?<=[\.\!\?])\s+|\n{2,}", ventana)

            for p in partes:
                p = limpiar_texto(p)
                if len(p) < 50:
                    continue
                if tiene_relleno(p):
                    continue
                if es_objetivo_proyecto(p):
                    continue

                sc = score_objetivo(p)
                if sc > mejor_score:
                    mejor_score = sc
                    mejor = p

    if not mejor:
        return None

    mejor = re.sub(r"\bi\+d\+i\+e\b", "I+D+i+e", mejor, flags=re.IGNORECASE)

    return {
        "cita": mejor,
        "score": mejor_score,
    }