# frase_ranker.py

import re
from backend.services.retrieval_scoring import score_tokens, normalizar_texto
from backend.services.consulta_utils_text import score_semantico


# ---------------------------------------------------------
# 1️⃣ DIVISIÓN DE FRASES (MEJORADA PARA TEXTO JURÍDICO)
# ---------------------------------------------------------

def dividir_frases(texto: str):

    if not isinstance(texto, str) or not texto.strip():
        return []

    # limpieza básica
    texto = texto.replace("SECCION:", "").replace("SECCIÓN:", "")

    # split robusto (legal + OCR)
    frases = re.split(
        r'(?<=[\.\!\?])\s+|\n+|;|:|,\s+(?=[A-Z])',
        texto
    )

    frases_limpias = []

    for f in frases:

        f = f.strip()

        # eliminar ruido típico OCR
        f = re.sub(r'\s{2,}', ' ', f)

        # filtros más flexibles
        if 40 < len(f) < 500:
            frases_limpias.append(f)

    return frases_limpias


# ---------------------------------------------------------
# 2️⃣ RANKING HÍBRIDO (TOKEN + SEMÁNTICO + LEGAL)
# ---------------------------------------------------------

def rankear_frases(texto, tokens, pregunta=None, top_k=3):

    frases = dividir_frases(texto)

    if not frases:
        return []

    scored = []

    for f in frases:

        try:

            f_norm = normalizar_texto(f)

            # -----------------------------
            # TOKEN SCORE
            # -----------------------------

            pres, occ = score_tokens(f_norm, tokens)

            s_token = pres * 5 + occ * 2

            # -----------------------------
            # SEMÁNTICO (CLAVE)
            # -----------------------------

            s_sem = 0

            if pregunta:
                s_sem = score_semantico(f, pregunta)

            # -----------------------------
            # BONUS LEGAL
            # -----------------------------

            f_low = f.lower()

            s_legal = 0

            if "resuelvo" in f_low:
                s_legal += 0.5

            if "apruebase" in f_low or "apruebanse" in f_low:
                s_legal += 0.6

            if "objetivo" in f_low:
                s_legal += 0.4

            if "requisitos" in f_low:
                s_legal += 0.3

            # -----------------------------
            # LONGITUD (evita frases malas)
            # -----------------------------

            s_len = min(len(f) / 400, 1)

            # -----------------------------
            # SCORE FINAL
            # -----------------------------

            score = (
                (s_sem * 0.5) +
                (s_token * 0.3) +
                (s_len * 0.1) +
                s_legal
            )

            # guardar incluso si token = 0 (mejora recall)
            scored.append((score, f))

        except Exception:
            continue

    # ordenar
    scored.sort(key=lambda x: x[0], reverse=True)

    top = [f for _, f in scored[:top_k]]

    # -------------------------------------------------
    # FALLBACK INTELIGENTE
    # -------------------------------------------------

    if not top:
        return frases[:top_k]

    return top
