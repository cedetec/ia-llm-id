# backend/services/retrieval_text_utils.py

from __future__ import annotations
import re
import unicodedata
from typing import Optional, List


# =========================================================
# STOPWORDS
# =========================================================

STOPWORDS = {
    "cual","cuál","que","qué","es","son","del","de","la","el",
    "los","las","un","una","y","o","segun","según","en","para",
    "por","con","a","al","se","su","sus","este","esta","estos",
    "estas","responde","dime","haz","sobre",
    "cuando","cuándo","donde","dónde","como","cómo"
}

ACRONIMOS_2 = {
    "ia", "ti", "id", "anid", "rex",
    "id", "fondef", "fondecyt",
    "corfo", "i+d"
}


# =========================================================
# NORMALIZACIÓN GLOBAL
# =========================================================

def normalizar(s: str) -> str:
    """
    Normalización consistente para todo el pipeline:
    - NFKC
    - quitar tildes
    - colapsar espacios
    - lowercase
    """

    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s)

    # quitar diacríticos
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

    s = s.lower()
    s = s.replace("\u00A0", " ")
    s = re.sub(r"\s+", " ", s)

    return s.strip()


# =========================================================
# AÑO
# =========================================================

def anio_en_texto(s: str) -> Optional[str]:
    m = re.search(r"\b(19\d{2}|20\d{2})\b", s or "")
    return m.group(1) if m else None


# =========================================================
# TOKENS
# =========================================================

def tokens(pregunta: str) -> List[str]:

    if not isinstance(pregunta, str):
        pregunta = str(pregunta or "")

    txt = normalizar(pregunta)

    txt = txt.replace("i+d+i+e", "i d i e")
    txt = txt.replace("i+d", "i d")

    txt = re.sub(r"(\d{1,5})/(\d{4})", r"\1 \2 \1/\2", txt)

    toks = re.findall(r"[a-z0-9\+\-/]+", txt)

    out = []

    for t in toks:

        if t in STOPWORDS:
            continue

        if len(t) == 1:
            continue

        if t.isdigit() and len(t) < 2:
            continue

        if len(t) >= 3 or t in ACRONIMOS_2:

            out.append(t)

            # singular simple
            if t.endswith("s") and len(t) > 5:
                out.append(t[:-1])

    seen = set()
    final = []

    for t in out:
        if t not in seen:
            seen.add(t)
            final.append(t)

    return final

def safe_split(x):

    if isinstance(x, dict):
        x = x.get("contenido") or x.get("texto") or ""

    elif isinstance(x, list):
        x = " ".join(
            i.get("contenido", "") if isinstance(i, dict) else str(i)
            for i in x
        )

    if not isinstance(x, str):
        x = str(x)

    return re.findall(r"[a-záéíóúñ0-9]+", x.lower())

# =========================================================
# NORMALIZACIÓN LINEAL (para bloques largos)
# =========================================================

def norm_txt_lineal(s: str) -> str:
    if not s:
        return ""

    # 🔥 FIX OCR comunes
    s = re.sub(r'(\d)l(\d)', r'\11\2', s)   # 1l0 → 110
    s = re.sub(r'(\d)I(\d)', r'\1\2', s)    # 1I0 → 10
    s = re.sub(r'(\d)o(\d)', r'\1\2', s)    # 1o0 → 100

    return normalizar(s)
