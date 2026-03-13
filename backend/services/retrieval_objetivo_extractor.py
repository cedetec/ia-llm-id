#retrieval_objeto_extractor.py
from __future__ import annotations
import re
from typing import Optional, Dict
from backend.services.retrieval_text_utils import norm_txt_lineal


def extraer_cita_objetivo(contexto: str) -> Optional[Dict[str, str]]:

    if not contexto:
        return None

    contexto = norm_txt_lineal(contexto)

    # 🔒 limitar tamaño global
    MAX_CTX = 8000
    contexto = contexto[:MAX_CTX]

    # 🔧 corregir OCR tipo O B J E T I V O
    contexto = re.sub(
        r'\b(?:[A-ZÁÉÍÓÚÑ]\s){3,}[A-ZÁÉÍÓÚÑ]\b',
        lambda m: m.group(0).replace(" ", ""),
        contexto
    )

    contexto = contexto.replace("\u00A0", " ")

    if not contexto.strip():
        return None

    def _limpiar(s: str) -> str:
        s = re.sub(r"^\s*\[DOC=.*?\]\s*", "", s)
        return re.sub(r"\s+", " ", s).strip()

    def _score(s: str) -> int:

        sl = s.lower()
        score = 0

        if "objetivo general del concurso" in sl:
            score += 40

        elif "objetivo del concurso" in sl:
            score += 30

        elif "objetivo general" in sl:
            score += 20

        if "concurso" in sl:
            score += 5

        # penalizar frases administrativas
        if "bases del concurso" in sl:
            score -= 20

        # penalizar frases cortadas
        if sl.startswith(("5 ", "4 ", "3 ", "2 ")):
            score -= 30

        if len(s) > 500:
            score -= 5

        return score

    PATTERNS = [

        re.compile(r"\bobjetivo\s+general\s+del\s+concurso\b", re.I),
        re.compile(r"\bobjetivo\s+del\s+concurso\b", re.I),
        re.compile(r"\bel\s+objetivo\s+del\s+concurso\b", re.I),
        re.compile(r"\bel\s+objetivo\s+de\s+este\s+concurso\b", re.I),
        re.compile(r"\beste\s+concurso\s+tiene\s+por\s+objetivo\b", re.I),
        re.compile(r"\btiene\s+por\s+objetivo\b", re.I),

    ]

    mejor = None
    mejor_score = -10**9

    for pat in PATTERNS:
        for m in pat.finditer(contexto):
            idx = m.start()

            start = max(0, idx - 300)
            end = min(len(contexto), idx + 600)
            window = contexto[start:end]

            partes = re.split(r"(?<=[\.\!\?])\s+|\n{2,}", window)

            for p in partes:
                p = _limpiar(p)
                if len(p) < 60:
                    continue
                if "objetivo" not in p.lower():
                    continue

                score = _score(p)

                if score > mejor_score:
                    mejor_score = score
                    mejor = p[:380]

    if not mejor:
        return None

    return {
        "cita": mejor,
        "score": mejor_score
    }

