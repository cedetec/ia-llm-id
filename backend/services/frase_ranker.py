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
        r'(?<=[\.\!\?])\s+|\n{2,}|;|:\s+|,\s+(?=[A-Z])',
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

    # 🔥 FIX CRÍTICO GLOBAL
    if isinstance(texto, dict):
        texto = texto.get("contenido") or texto.get("texto") or ""

    elif isinstance(texto, list):
        texto = " ".join(
            t.get("contenido", "") if isinstance(t, dict) else str(t)
            for t in texto
        )

    # 🔥 VALIDACIÓN FINAL
    if not isinstance(texto, str) or not texto.strip():
        return []

    frases = dividir_frases(texto)

    # -------------------------------------------------
    # 🔥 DETECTAR INTENCIÓN DESDE LA PREGUNTA
    # -------------------------------------------------
    preg_norm = (pregunta or "").lower()

    es_objetivo = "objetivo" in preg_norm
    es_requisito = any(x in preg_norm for x in ["requisito", "postular"])
    es_beneficiarios = any(x in preg_norm for x in [
        "beneficiario",
        "beneficiarios",
        "quienes pueden",
        "postulantes"
    ])
    es_resolucion = any(x in preg_norm for x in [
        "resolucion",
        "aprueba",
        "rex",
        "numero de resolucion"
    ])
    es_evaluacion = "evaluacion" in preg_norm
    es_financiamiento = any(x in preg_norm for x in ["monto", "financiamiento"])
    es_duracion = any(x in preg_norm for x in ["duracion", "meses", "años"])

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
            # SEMÁNTICO
            # -----------------------------
            s_sem = 0
            if pregunta:
                s_sem = score_semantico(f, pregunta)

            # -----------------------------
            # BONUS LEGAL
            # -----------------------------
            f_low = f.lower()

            s_legal = 0

            # ----------------------------------
            # BONUS SEGÚN CONTENIDO LEGAL
            # ----------------------------------

            if "resuelvo" in f_low:
                s_legal += 0.6

            if "apruebase" in f_low or "apruebanse" in f_low:
                s_legal += 0.8

            if "objetivo" in f_low:
                s_legal += 0.6

            if "requisito" in f_low:
                s_legal += 0.5

            if "beneficiario" in f_low or "postular" in f_low:
                s_legal += 0.5

            if "evaluacion" in f_low:
                s_legal += 0.5

            if "monto" in f_low or "financiamiento" in f_low:
                s_legal += 0.5

            if "meses" in f_low or "duracion" in f_low:
                s_legal += 0.4


            # ----------------------------------
            # BONUS SEGÚN INTENCIÓN PREGUNTA
            # ----------------------------------

            if es_objetivo and "objetivo" in f_low:
                s_legal += 1.5

            if es_requisito and "requisito" in f_low:
                s_legal += 1.5

            if es_beneficiarios and ("postular" in f_low or "beneficiario" in f_low):
                s_legal += 1.5

            if es_resolucion and ("resolucion" in f_low or "aprueb" in f_low):
                s_legal += 1.5

            if es_evaluacion and "evaluacion" in f_low:
                s_legal += 1.5

            if es_financiamiento and ("monto" in f_low or "financiamiento" in f_low):
                s_legal += 1.5

            if es_duracion and ("meses" in f_low or "duracion" in f_low):
                s_legal += 1.5

            # -----------------------------
            # LONGITUD
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

            scored.append((score, f))

        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)

    top = [f for _, f in scored[:top_k]]

    if not top:
        return frases[:top_k]

    return top
