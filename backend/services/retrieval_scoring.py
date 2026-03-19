# backend/services/retrieval_scoring.py
from __future__ import annotations
import re
import unicodedata
from typing import List, Tuple
from backend.services.retrieval_text_utils import safe_split

# =========================================================
# NORMALIZACIÓN
# =========================================================

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""

    # lower
    texto = texto.lower()

    # quitar tildes
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    # colapsar espacios
    texto = re.sub(r'\s+', ' ', texto)

    # unir solo letras sueltas (OCR típico tipo "o b j e t i v o")
    texto = re.sub(r'\b([a-z])\s+([a-z])\b', r'\1\2', texto)

    return texto.strip()

# =========================================================
# REPARACIÓN OCR
# =========================================================

def compactar_ocr(texto: str) -> str:
    """
    Corrige OCR tipo:
    o b j e t i v o
    c o n c u r s o
    """

    return re.sub(
        r'\b(?:[a-z]\s+){2,}[a-z]\b',
        lambda m: m.group(0).replace(" ", ""),
        texto
    )

# =========================================================
# BOOSTS Y PENALIZACIONES
# =========================================================

BOOSTS_FUERTES = (
    "objetivo general del concurso",
    "1.2 objetivo general",
    "objetivo del concurso",
)

BOOSTS_MEDIOS = (
    "objetivo general",
    "tiene por objeto",
    "tendra por objeto",
    "finalidad del concurso",
    "proposito del concurso",
    "busca",
    "consiste en",
    "objetivo del presente concurso",

    # NUEVOS
    "el objetivo del presente concurso",
    "tiene como objetivo",
    "tiene como finalidad",
    "tiene como proposito",
)

BOOSTS_RESOLUCION = (
    "apruebase las bases",
    "apruebanse las bases",
    "aprueba las bases",
)

BOOSTS_RESOLUCION_GENERICOS = (
    "resuelvo",
    "resolucion exenta",
    "resolucion exento",
)

PENALTIES = (
    "presupuesto",
    "item",
    "gastos",
    "rendicion",
    "financiamiento",
    "transferencia",
    "boleta",
    "factura",
    "contrapartida",
    "plan de compras",
)

# =========================================================
# TOKENS IMPORTANTES (peso extra)
# =========================================================

TOKENS_IMPORTANTES = {
    "objetivo",
    "objetivo general",
    "concurso",
    "postular",
    "postulacion",
    "fondos",
    "beneficiarios",
}


# =========================================================
# TOKEN SCORING
# =========================================================

def score_tokens(c_normalizado: str, tokens) -> Tuple[int, int]:
    """
    Devuelve:
    - present: cantidad de tokens distintos presentes
    - occ: ocurrencias totales
    """

    # 🔴 FIX CRÍTICO
    if not isinstance(tokens, (list, tuple, set)):
        tokens = []

    present = 0
    occ = 0

    for t in tokens:

        if not t:
            continue

        t_norm = normalizar_texto(str(t))

        # 🔥 permitir coincidencias parciales (tipo stemming ligero)
        t_root = t_norm[:5]

        if not t_norm:
            continue

        # frase completa
        if " " in t_norm:

            if t_norm in c_normalizado:
                present += 1
                occ += c_normalizado.count(t_norm)

        # palabra individual
        else:

            matches = re.findall(
                rf"\b{re.escape(t_root)}\w*\b",
                c_normalizado
            )

            if matches:
                present += 1
                peso = 2 if t_norm in TOKENS_IMPORTANTES else 1
                occ += len(matches) * peso

    return present, occ


# =========================================================
# SCORE PRINCIPAL DE CHUNK
# =========================================================

def score_chunk(
    contenido: str,
    tokens: List[str],
    *,
    modo_cita: bool
) -> float:

    if not contenido:
        return 0.0

    if isinstance(contenido, dict):
        contenido = contenido.get("contenido") or contenido.get("texto") or ""

    elif isinstance(contenido, list):
        contenido = " ".join(
            c.get("contenido", "") if isinstance(c, dict) else str(c)
            for c in contenido
        )

    if not isinstance(contenido, str):
        return 0.0

    try:

        c_low = normalizar_texto(contenido)
        c_low = compactar_ocr(c_low)

        # arreglar palabras OCR comunes
        c_low = re.sub(r'f\s*o\s*n\s*d\s*e\s*c\s*y\s*t', 'fondecyt', c_low)
        c_low = re.sub(r'a\s*n\s*i\s*d', 'anid', c_low)

        c_low = c_low.replace("res.", "resolucion")
        c_low = c_low.replace("rex", "resolucion")

        if not isinstance(tokens, (list, tuple, set)):
            tokens = []

        bonus = 0
        penalty = 0

        # evitar chunks demasiado pequeños
        if not isinstance(c_low, str) or len(safe_split(c_low)) < 5:
            return 0.0

        pres, occ = score_tokens(c_low, tokens)

        if pres == 0:
            penalty -= 5

        # tablas suelen ser ruido
        if contenido.count("|") > 4 or re.search(r'\btabla\b', c_low):
            penalty -= 6

        # =====================================================
        # BOOSTS ESTRUCTURALES
        # =====================================================

        if any(x in c_low for x in BOOSTS_FUERTES):
            bonus += 12

        elif any(x in c_low for x in BOOSTS_MEDIOS):
            bonus += 8

        if any(x in c_low for x in BOOSTS_RESOLUCION):
            bonus += 15

        if any(x in c_low for x in BOOSTS_RESOLUCION_GENERICOS):
            bonus += 4

        # =====================================================
        # BOOSTS CONTEXTUALES
        # =====================================================

        # estructura típica de bases
        if re.search(r'\b1\.\d?\s+objetivo', c_low):
            bonus += 10

        # encabezado directo
        if c_low.startswith("objetivo"):
            bonus += 10

        if "objetivo del concurso" in c_low:
            bonus += 10

        if "requisitos de postulacion" in c_low:
            bonus += 8

        if "requisitos para postular" in c_low:
            bonus += 8

        if "podran postular" in c_low:
            bonus += 8

        if "pueden postular" in c_low:
            bonus += 8

        if "quienes pueden postular" in c_low:
            bonus += 10

        if "fondecyt" in c_low:
            bonus += 6

        # NUEVO
        if re.search(r'i\s*\+\s*d', c_low):
            bonus += 6

        if "idea" in c_low:
            bonus += 4

        if re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b', c_low):
            bonus += 6

        # =====================================================
        # PENALIZACIONES
        # =====================================================

        if modo_cita:
            pen_count = sum(1 for p in PENALTIES if p in c_low)
            penalty -= min(pen_count * 3, 9)

            if "objetivo general" in c_low and "del proyecto" in c_low:
                penalty -= 6

            # preferir frases cortas en citas
            words = len(safe_split(c_low))

            if words < 8:
                penalty -= 4

            if words > 80:
                penalty -= 6

            if words > 200:
                penalty -= 10


        # =====================================================
        # SCORE FINAL
        # =====================================================

        if modo_cita and len(safe_split(c_low)) > 200:
            penalty -= 10


        length_norm = max(len(safe_split(c_low)), 1)
        density = occ / length_norm

        total = (
            bonus
            + (pres * 3.5)
            + min(occ * 0.4, 5)
            + min(density * 30, 6)
            + penalty
        )

        # 🔥 normalización suave (mantiene diferencias)
        return float(max(min(total, 60), 0))

    except Exception:
        
        return 0.0
