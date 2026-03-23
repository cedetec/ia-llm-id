# backend/services/rerank_legal.py
import re
from backend.services.retrieval_text_utils import safe_split, safe_text

def rerank_legal_chunks(pregunta, ranked):

    preg = pregunta.lower()

    for r in ranked:

        # 🔥 obtener texto seguro
        txt = safe_text(
            r.get("contenido")
            or r.get("contenido_norm")
            or ""
        )

        txt = txt.lower()
        score = r.get("score", 0)

        # -----------------------------
        # Frases típicas de normativa
        # -----------------------------

        if re.search(r'\bel\s+presente\s+concurso\s+tiene\s+por\s+objetivo\b', txt):
            score += 0.12

        if re.search(r'\bpodran\s+postular\b', txt):
            score += 0.10

        if re.search(r'\bquienes\s+pueden\s+postular\b', txt):
            score += 0.10

        if re.search(r'\baprueba[n]??\s+las\s+bases\b', txt):
            score += 0.12

        if re.search(r'\bresuelvo\b', txt):
            score += 0.08

        # -----------------------------
        # Penalizar tablas o listados
        # -----------------------------

        if txt.count(";") > 6:
            score -= 0.05

        if txt.count("|") > 4:
            score -= 0.05

        # 🔥 longitud segura
        words = len(safe_split(txt))

        if words > 250:
            score -= 0.05

        r["score"] = score

    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)

    return ranked
