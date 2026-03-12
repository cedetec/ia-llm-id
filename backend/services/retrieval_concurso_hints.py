# backend/services/retrieval/concurso_hints.py
from __future__ import annotations
import re
import unicodedata
from typing import Optional, Dict, List
from backend.services.retrieval_text_utils import normalizar


# -----------------------------------------------------------
# UTILIDAD: quitar tildes de forma robusta
# -----------------------------------------------------------

def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# -----------------------------------------------------------
# DETECTAR NOMBRE PEDIDO SIMPLE
# -----------------------------------------------------------

def nombre_pedido_simple(pregunta: str) -> Optional[str]:
    p = normalizar(pregunta)
    pl = _sin_tildes(p).lower()

    if re.search(r"\bines\b", pl) and re.search(r"\bgenero\b", pl):
        return "InES Género"

    if re.search(r"\bfondecyt\b", pl):
        for k in ("regular", "postdoctorado", "postdoc", "iniciacion"):
            if re.search(rf"\b{k}\b", pl):
                return f"FONDECYT {k.upper()}"
        return "FONDECYT"

    if re.search(r"\bfondap\b", pl):
        return "FONDAP"

    if re.search(r"\bfondequip\b", pl):
        return "FONDEQUIP"

    if re.search(r"\banillos\b", pl):
        return "ANILLOS"

    if re.search(r"\bbasal\b", pl):
        return "BASAL"

    if re.search(r"\bbecas?\b", pl):
        return "BECAS"

    return None


# -----------------------------------------------------------
# CLAVES MÍNIMAS PARA BÚSQUEDA
# -----------------------------------------------------------

def claves_concurso_min(nombre: str) -> List[str]:
    n = normalizar(nombre)
    n = _sin_tildes(n).lower()

    # eliminar año
    n = re.sub(r"\b20\d{2}\b", "", n)

    toks = [t for t in re.findall(r"[a-z0-9]+", n) if t]

    stop = {
        "concurso", "programa", "bases", "convocatoria",
        "objetivo", "general", "agencia", "nacional",
        "investigacion", "desarrollo"
    }

    toks = [t for t in toks if t not in stop]

    prioridad = []
    for k in (
        "fondecyt", "regular", "postdoctorado", "postdoc",
        "iniciacion", "fondap", "basal", "anillos",
        "fondequip", "ines", "genero",
        "doctorado", "becas", "beca",
        "magister"
    ):
        if k in toks and k not in prioridad:
            prioridad.append(k)

    resto = [t for t in toks if t not in prioridad]

    return (prioridad + resto)[:4]


# -----------------------------------------------------------
# DETECTAR FILTRO METADATA
# -----------------------------------------------------------

def detectar_filtro_metadata(pregunta: str) -> Dict:
    p = normalizar(pregunta)
    pl = _sin_tildes(p).lower()

    if re.search(r"\bines\b", pl) and re.search(r"\bgenero\b", pl):
        return {
            "metadata.documento": {
                "$regex": r"(InES[_\s-]*Genero|InES\s*G[eé]nero)",
                "$options": "i"
            }
        }

    if re.search(r"\bcalendario\b", pl):
        return {"metadata.origen": "CALENDARIO"}

    return {}


# -----------------------------------------------------------
# TOKENS FUERTES DESDE NOMBRE PEDIDO
# -----------------------------------------------------------

def doc_pref_tokens_desde_nombre(nombre_pedido: Optional[str]) -> List[str]:
    if not nombre_pedido:
        return []

    np = normalizar(nombre_pedido)
    np = _sin_tildes(np).lower()

    fuertes = {
        "fondecyt", "fondap", "basal", "anillos",
        "fondequip", "ines", "genero",
        "doctorado", "beca", "becas"
    }

    out = []
    for t in fuertes:
        if re.search(rf"\b{t}\b", np):
            out.append(t)

    return out