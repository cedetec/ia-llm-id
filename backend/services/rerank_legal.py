#rerank_legal.py
import re

def rerank_legal_chunks(pregunta, ranked):

    preg = pregunta.lower()

    for r in ranked:

        txt = r["contenido"].lower()
        score = r["score"]

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

        r["score"] = score

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return ranked
