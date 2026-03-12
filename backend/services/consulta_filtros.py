# backend/services/consulta_filtros.py
from __future__ import annotations
import re
from backend.services.consulta_utils_text import normalizar_txt

def contiene_palabras_clave(texto: str, claves: list[str], *, min_hits: int | None = None) -> bool:
    if not texto:
        return False

    t = normalizar_txt(texto).lower()

    ks = []
    for c in (claves or []):
        if not c:
            continue
        c_norm = normalizar_txt(c).lower()
        if c_norm:
            ks.append(c_norm)

    if not ks:
        return False

    if min_hits is None:
        min_hits = 1  # 🔥 más permisivo

    hits = 0
    for k in ks:
        if re.search(rf"\b{re.escape(k)}\b", t):
            hits += 1
            if hits >= min_hits:
                return True

    return False

def claves_concurso(nombre: str) -> list[str]:
    n = normalizar_txt(nombre).lower()

    toks = [t for t in re.split(r"[^a-záéíóúñ0-9]+", n) if t]

    stop = {
        "concurso", "programa", "bases", "convocatoria",
        "objetivo", "general", "agencia", "nacional",
        "investigacion", "investigación", "desarrollo"
    }

    toks = [t for t in toks if t not in stop]

    prioridad_keywords = [
        "fondecyt", "regular", "postdoctorado", "postdoc",
        "iniciacion", "iniciación", "fondap", "basal",
        "anillos", "fondequip", "ines", "genero", "género",
        "doctorado", "becas", "magister", "magíster",
        "ia", "inteligencia", "artificial"
    ]

    prioridad = [k for k in prioridad_keywords if k in toks]
    resto = [t for t in toks if t not in prioridad]

    # 🔥 No limitar tan agresivamente
    return prioridad + resto[:6]
