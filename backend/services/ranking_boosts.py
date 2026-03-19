# ranking_boosts.py
import re
from backend.services.ranking_utils import normalizar_txt
from backend.services.retrieval_text_utils import safe_split


def boost_frase(pregunta, texto):

    preg = normalizar_txt(pregunta)

    if len(preg) < 15:
        return 0

    if preg in texto:
        return 80

    tokens = safe_split(preg)

    if len(tokens) >= 3:
        for i in range(len(tokens) - 2):
            frase = " ".join(tokens[i:i+3])
            if frase in texto:
                return 40

    return 0


def boost_posicion(meta):

    idx = meta.get("chunk_index", 0)
    total = meta.get("total_chunks", 1)

    if total <= 0:
        return 0

    ratio = idx / total

    if ratio < 0.05:
        return 40

    if ratio < 0.10:
        return 25

    if ratio < 0.20:
        return 10

    return 0


def penalizar_repeticion(texto):

    words = safe_split(texto)

    if len(words) < 10:
        return 0

    unique_ratio = len(set(words)) / len(words)

    if unique_ratio < 0.35:
        return -80

    if unique_ratio < 0.50:
        return -40

    return 0
