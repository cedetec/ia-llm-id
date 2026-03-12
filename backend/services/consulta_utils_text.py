# backend/services/consulta_utils_text.py
from __future__ import annotations
import re
import unicodedata
from typing import Optional

_RE_META = re.compile(r"\[DOC=.*?\]", flags=re.IGNORECASE)

_RE_DOCFILE = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9_\-\.]{2,200}\.pdf)\b",
    re.IGNORECASE
)

def _extraer_docfile(pregunta: str) -> str | None:

    m = _RE_DOCFILE.search(pregunta or "")

    if not m:
        return None

    doc = m.group(1)

    # normalización consistente con Mongo
    doc = doc.lower()

    return doc

# Alias público para usarlo desde otros módulos
extraer_docfile = _extraer_docfile

CITA_TRIGGERS = (
    "cita", "textual", "frase textual", "cita textual",
    "frase exacta", "literal", "exactamente", "tal cual"
)

_OCR_RUIDO = re.compile(
    r"\b(documento\s+electr[oó]nico|firma(?:do)?\s+electr[oó]nicamente)\b",
    flags=re.IGNORECASE
)

# =========================================================
# 🔢 Patrón estructural número de resolución administrativa
# =========================================================
_RE_NUM_RESOL = re.compile(
    r"(?:Resoluci[oó]n(?:\s+Exent[ao])?|REX)?\s*"
    r"(?:N[°ºo]\s*)?"
    r"\d{1,5}\s*[/\-.]\s*\d{2,4}",
    re.IGNORECASE
)

PATRONES_SECCION = {
    "objetivo": re.compile(
        r"^(?:\d+(\.\d+)*\.?|[IVXLC]+\.)?\s*(OBJETIVO(S)?(\s+GENERAL(ES)?)?)\b",
        re.IGNORECASE
    ),
    "requisitos": re.compile(
        r"^(?:\d+(\.\d+)*\.?|[IVXLC]+\.)?\s*(REQUISITOS?|CONDICIONES\s+DE\s+POSTULACI[ÓO]N)\b",
        re.IGNORECASE
    ),
    "evaluacion": re.compile(
        r"^(?:\d+(\.\d+)*\.?|[IVXLC]+\.)?\s*(EVALUACI[ÓO]N|CRITERIOS\s+DE\s+EVALUACI[ÓO]N)\b",
        re.IGNORECASE
    ),
    "beneficiarios": re.compile(
        r"^(?:\d+(\.\d+)*\.?|[IVXLC]+\.)?\s*(QUI[ÉE]NES\s+PUEDEN\s+POSTULAR|POSTULANTES?|BENEFICIARIOS?)\b",
        re.IGNORECASE
    ),
}

def modo_cita(pregunta: str) -> bool:

    p = (pregunta or "").lower()

    return bool(re.search(
        r"\b(cita|textual|literal|tal\s+cual|frase\s+exacta|extrae|donde\s+aparezca)\b",
        p
    ))

def anio_en_pregunta(p: str) -> Optional[str]:
    m = re.search(r"\b(20\d{2})\b", p or "")
    return m.group(1) if m else None

def quitar_anio(p: str) -> str:
    return re.sub(r"\b20\d{2}\b", "", p or "").strip()

def normalizar_txt(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u00A0", " ")
    return re.sub(r"\s+", " ", s).strip()

def limpiar_meta_preservando_newlines(fragmento: str) -> str:
    frag = _RE_META.sub("", fragmento or "")

    lineas = []
    for ln in frag.splitlines():
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if ln:
            lineas.append(ln)

    frag = "\n".join(lineas)

    frag = frag.replace(" ny:", " n°:").replace(" ny", " n°")
    frag = frag.replace(" n*", " n°").replace(" n°*", " n°")
    return frag

def post_corte_frase(s: str, *, max_chars: int = 260) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()

    # =========================================
    # 🔧 Reparación OCR estructural
    # =========================================

    # eliminar cortes de palabra por salto de línea OCR
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)

    # normalizar variantes de número
    s = s.replace("N Y:", "N°:")
    s = s.replace("N Y", "N°")
    s = s.replace("Nº", "N°")
    s = _OCR_RUIDO.sub("", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,;:-")

    m = re.search(r"\b\d{1,5}/\d{4}\b", s)
    if m:
        tail = s[m.end():]
        cut = re.search(r"[.;]", tail)
        if cut:
            s = (s[:m.end()] + tail[:cut.start() + 1]).strip(" ,;:-")

    if len(s) > max_chars:
        s = s[:max_chars].rstrip(" ,;:-") + "…"

    s = re.sub(r"\b(dla|dlo|dl|d1a|dIa)\b\.?$", "", s, flags=re.IGNORECASE).strip(" ,;:-")
    s = re.sub(r"\b(nela|va|dla|dlo)\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,;:-")

    s = re.sub(r"\b[nN]\s*(?:[°º]|o)\s*:", "N°:", s)
    s = re.sub(r"\b[nN]\s*(?:[°º]|o)\b", "N°", s)
    s = re.sub(r"\bsantiago\b", "Santiago", s, flags=re.IGNORECASE)
    s = re.sub(r"\bexento\b", "Exento", s, flags=re.IGNORECASE)
    s = re.sub(r"\bexenta\b", "Exenta", s, flags=re.IGNORECASE)

    s = re.sub(
        r"Ministerio de ciencia tecnología, conocimiento e innovación",
        "Ministerio de Ciencia, Tecnología, Conocimiento e Innovación",
        s,
        flags=re.IGNORECASE
    )

    s = re.sub(r"\binvestigacion\b", "investigación", s, flags=re.IGNORECASE)
    s = re.sub(r"\bconcurso de nacional\b", "concurso nacional", s, flags=re.IGNORECASE)
    s = re.sub(r"\bResolución\s+Exento\b", "Resolución Exenta", s)
    # arreglos de OCR típicos al inicio
    s = re.sub(r"^trav[eé]s\b", "A través", s, flags=re.IGNORECASE)
    s = re.sub(r"^\|\s*", "", s)  # elimina barra inicial


    if s and s[0].isalpha():
        s = s[0].upper() + s[1:]
    s = re.sub(r"(\.\s+)([a-záéíóúñ])", lambda m: m.group(1) + m.group(2).upper(), s)

    return s

# ==========================================================
# VALIDACIONES DE EXCELENCIA RAG (TESIS)
# ==========================================================

def frase_completa(f: str) -> bool:
    f = (f or "").strip()
    if not f:
        return False

    return (
        len(f) > 40 and
        f.endswith((".", ";", ":"))
    )


def score_semantico(frase: str, pregunta: str) -> float:
    STOP = {"el", "la", "los", "las", "de", "del", "para", "en", "por", "y", "o"}

    tokens_f = {
        t for t in re.findall(r"[a-záéíóúñ0-9]+", normalizar_txt(frase).lower())
        if t not in STOP
    }

    tokens_p = {
        t for t in re.findall(r"[a-záéíóúñ0-9]+", normalizar_txt(pregunta).lower())
        if t not in STOP
    }
    if not tokens_p:
        return 0.0
    return len(tokens_f & tokens_p) / len(tokens_p)


def nivel_confianza(score: float) -> str:
    if score > 0.75:
        return "ALTO"
    if score > 0.45:
        return "MEDIO"
    return "BAJO"

# =========================================================
# 🎯 Extraer número de resolución desde frase limpia
# =========================================================
def extraer_numero_resolucion_frase(frase: str) -> Optional[str]:
    if not frase:
        return None

    m = _RE_NUM_RESOL.search(frase)
    if m:
        return m.group(0).strip()

    return None

def extraer_palabra_entre_comillas(pregunta: str) -> Optional[str]:

    if not pregunta:
        return None

    m = re.search(r'"([^"]+)"', pregunta)

    if m:
        return m.group(1).strip().lower()

    return None
