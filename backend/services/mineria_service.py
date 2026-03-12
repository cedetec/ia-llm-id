# backend/services/mineria_service.py
from __future__ import annotations
import re
from collections import Counter
import unicodedata

def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()

STOP = {
  "de","la","el","los","las","y","o","a","en","del","al","por","para","con","sin",
  "un","una","unos","unas","que","qué","como","cómo","cual","cuál","cuando","cuándo",
  "donde","dónde","se","su","sus","es","son","ser","haber","ha","han","fue","fueron",
  "este","esta","estos","estas","ese","esa","esos","esas","muy","más","menos",
}

def extraer_keywords(texto: str, topk: int = 12) -> list[str]:
    t = _normalizar(texto)

    toks = re.findall(r"[a-z0-9]{3,}", t)
    toks = [
        x for x in toks
        if x not in STOP
        and not re.fullmatch(r"\d{4,}", x)
    ]

    if not toks:
        return []

    freq = Counter(toks)
    return [w for w, _ in freq.most_common(topk)]

def extraer_entidades_basicas(texto: str) -> dict:
    t = texto or ""

    fechas_iso = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", t)
    fechas_slash = re.findall(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", t)

    # montos: $ 1.000.000 / 10 millones / UF 2000 / UTM 50
    montos = []
    montos += re.findall(r"\$\s?\d[\d\.\,]*", t)
    montos += re.findall(r"\bUF\s?\d[\d\.\,]*\b", t, flags=re.IGNORECASE)
    montos += re.findall(r"\bUTM\s?\d[\d\.\,]*\b", t, flags=re.IGNORECASE)
    montos += re.findall(r"\b\d+\s?(?:millones|millon|millón)\b", t, flags=re.IGNORECASE)

    # instituciones (diccionario simple)
    instituciones = []
    for inst in ("anid", "minciencia", "corfo", "fondef", "fondecyt", "fondap", "onu"):
        if re.search(rf"\b{inst}\b", t.lower()):
            instituciones.append(inst.upper())

    # “concurso …”
    concursos = re.findall(
        r"(concurso\s+[a-z0-9áéíóúñü\-\s]{5,60}?)(?:\.|,|\n)",
        t.lower()
    )

    return {
        "fechas_iso": list(dict.fromkeys(fechas_iso)),
        "fechas_slash": list(dict.fromkeys(fechas_slash)),
        "montos": list(dict.fromkeys(montos)),
        "instituciones": list(dict.fromkeys(instituciones)),
        "concursos": list(dict.fromkeys(concursos[:3])),
    }
