
# backend/services/retrieval/citation_utils.py

import re
import unicodedata
from backend.services.retrieval_text_utils import safe_split


def _normalizar(txt: str) -> str:

    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ascii", "ignore").decode("ascii")
    txt = txt.lower()

    # colapsar espacios
    txt = re.sub(r'\s+', ' ', txt)

    # corregir OCR tipo "o b j e t i v o"
    txt = re.sub(r'([a-z])\s+(?=[a-z])', r'\1', txt)

    return txt.strip()


def _extraer_palabras_clave(pregunta: str):

    palabras = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    return [
        _normalizar(p)
        for p in palabras
    ]


def aplicar_filtro_cita(pregunta, texto, modo_documento_fijado, seccion_objetivo=None):

    if not isinstance(texto, str):
        texto = str(texto or "")

    texto_norm = _normalizar(texto)

    palabras = _extraer_palabras_clave(pregunta)

    match = None

    # ----------------------------------------------------
    # 1️⃣ búsqueda por palabras entre comillas
    # ----------------------------------------------------

    if palabras:

        for palabra in palabras:
            pat = re.escape(palabra)
            match = re.search(pat, texto_norm, re.IGNORECASE)

            if match:
                break

    # ----------------------------------------------------
    # 2️⃣ patrones jurídicos si no hay palabra explícita
    # ----------------------------------------------------

    if not match:

        if seccion_objetivo == "objetivo":
            patrones = [
                r"objetivo.{0,20}concurso",
                r"objetivo\s+general",
                r"tiene\s+por\s+objetivo",
            ]

        elif seccion_objetivo == "requisito":
            patrones = [
                r"requisitos?.{0,20}postulacion",
                r"deben\s+postular",
            ]

        elif seccion_objetivo == "beneficiarios":
            patrones = [
                r"podran.{0,20}postular",
                r"quienes.{0,20}pueden.{0,20}postular",
            ]

        elif seccion_objetivo == "resolucion":
            patrones = [
                r"aprue?b[a-z]*\s+las?\s+bases",
                r"resolucion\s+exenta",
                r"res\.?\s*n[°o]\s*\d+",
            ]

        else:
            patrones = [
                r"\bidea\b",
                r"i\s*\+\s*d",
                r"fondecyt",
                r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            ]

        for p in patrones:

            match = re.search(p, texto_norm)

            if match:
                break

    # ----------------------------------------------------
    # 🔥 FILTRO POR INTENCIÓN (CLAVE)
    # ----------------------------------------------------

    if match and seccion_objetivo:

        if seccion_objetivo == "objetivo":
            if not re.search(r'objetivo|finalidad|proposito', texto_norm):
                return None

        elif seccion_objetivo == "requisito":
            if not re.search(r'requisito', texto_norm):
                return None

        elif seccion_objetivo == "beneficiarios":
            if not re.search(r'podran|quienes pueden|beneficiarios', texto_norm):
                return None

        elif seccion_objetivo == "resolucion":
            if not re.search(r'resolucion|resuelv|aprueb', texto_norm):
                return None

    # ----------------------------------------------------
    # 🔥 FILTRO DE BASURA ADMINISTRATIVA (MEJORADO)
    # ----------------------------------------------------

    if match and re.search(
        r'ejemplar de las bases|acto administrativo|facultades que detenta|adjunto al acto',
        texto_norm
    ):
        return None

    # ----------------------------------------------------

    if not match:

        if modo_documento_fijado:
            texto = texto.strip()

            # 🔥 SOLO si contiene algo relevante
            if any(x in texto_norm for x in [
                "objetivo",
                "requisito",
                "postular",
                "beneficiario",
                "resolucion"
            ]):
                return texto[:200]

        return None

    # ----------------------------------------------------
    # 3️⃣ extraer frase alrededor
    # ----------------------------------------------------

    delimitadores = ['.', ';', ':', '\n']

    inicio = -1

    for d in delimitadores:

        pos = texto.rfind(d, 0, match.start())

        if pos > inicio:
            inicio = pos

    fin_candidates = [
        texto.find('.', match.end()),
        texto.find(';', match.end()),
        texto.find(':', match.end()),
        texto.find('\n', match.end())
    ]

    fin_candidates = [f for f in fin_candidates if f != -1]

    fin = min(fin_candidates) if fin_candidates else len(texto)

    inicio = 0 if inicio == -1 else inicio + 1
    fin = len(texto) if fin == -1 else fin + 1

    frase = texto[inicio:fin].strip()

    # ----------------------------------------------------
    # 🔥 VALIDACIÓN FINAL POR SECCIÓN (CLAVE REAL)
    # ----------------------------------------------------

    frase_norm = _normalizar(frase)

    if seccion_objetivo == "objetivo":
        if not re.search(r'objetivo|finalidad|proposito', frase_norm):
            return None

    elif seccion_objetivo == "requisito":
        if not re.search(r'requisito', frase_norm):
            return None

    elif seccion_objetivo == "beneficiarios":
        if not re.search(r'podran|quienes pueden|beneficiarios', frase_norm):
            return None

    elif seccion_objetivo == "resolucion":
        if not re.search(r'resolucion|resuelv|aprueb', frase_norm):
            return None

    # 🔥 FIX CRÍTICO: descartar frases basura muy cortas
    if len(safe_split(frase)) < 6:
        return None

    if len(frase) < 40:

        # intentar ampliar alrededor del match
        start = max(0, match.start() - 120)
        end = min(len(texto), match.end() + 120)

        frase = texto[start:end].strip()

        # 🔥 volver a validar después de ampliar
        if len(safe_split(frase)) < 6:
            return None

        return frase

    return frase
