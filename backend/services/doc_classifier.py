import re
import unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()

def clasificar_documento(texto: str) -> str:
    t = _norm(texto)

    # -------------------------
    # Resolución administrativa
    # -------------------------
    if (
        re.search(r"\bresuelvo\b", t)
        or re.search(r"\bresolucion\s+(exent[ao]|n[°o]?)?\s*\d+", t)
        or re.search(r"\brex\s*\d{1,5}/\d{4}", t)
    ):
        return "resolucion"

    # -------------------------
    # Bases de concurso
    # -------------------------
    if (
        "bases del concurso" in t
        or re.search(r"\bobjetivo(s)?\b", t)
        or re.search(r"\brequisitos?\s+de\s+postulacion", t)
        or re.search(r"\bquienes?\s+pueden\s+postular", t)
    ):
        return "bases"

    # -------------------------
    # Anexo
    # -------------------------
    if re.search(r"\banexo\s+[ivx0-9]?", t):
        return "anexo"

    return "otro"