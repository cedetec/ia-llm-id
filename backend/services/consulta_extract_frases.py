# backend/services/consulta_extract_frases.py
from __future__ import annotations
import re
from typing import Optional, Tuple
from backend.services.consulta_utils_text import limpiar_meta_preservando_newlines, post_corte_frase

def _score_frase_juridica(frase: str, tipo_consulta: str | None = None) -> int:

    s = frase.lower()

    score = 0

    # -----------------------------------------
    # OBJETIVO
    # -----------------------------------------

    if tipo_consulta == "objetivo":

        if "objetivo del concurso" in s:
            score += 120

        elif "el objetivo del concurso" in s:
            score += 110

        elif "objetivo general del concurso" in s:
            score += 100

        elif "objetivo general" in s:
            score += 60

        if "objetivo del proyecto" in s:
            score -= 100


    # -----------------------------------------
    # POSTULACIÓN
    # -----------------------------------------

    if tipo_consulta == "postulacion":

        if "podrán postular" in s:
            score += 120

        if "pueden postular" in s:
            score += 120

        if "quienes pueden postular" in s:
            score += 120


    # -----------------------------------------
    # REQUISITOS
    # -----------------------------------------

    if tipo_consulta == "requisitos":

        if "requisitos" in s:
            score += 80


    # -----------------------------------------
    # APROBACIÓN DE BASES
    # -----------------------------------------

    if tipo_consulta == "aprueba_bases":

        if "apruebanse las bases concursales" in s:
            score += 200

        elif "apruebanse las bases" in s:
            score += 180

        elif "aprueba las bases" in s:
            score += 160


    # -----------------------------------------
    # BONUS GENERAL
    # -----------------------------------------

    if "resolucion" in s:
        score += 20

    if "fondecyt" in s:
        score += 10

    return score

# =========================
# 🔎 PATRONES SEMÁNTICOS
# =========================

PATRONES_APRUEBA_BASES = [
    "aprueba bases",
    "aprueban las bases",
    "aprueban las bases concursales",
    "apruebase",
    "apruebanse",
    "aprueba",
    "aprueban",
    "aprueba las bases",
    "apruebase las bases",
    "apruebanse las bases",
    "apruebase el texto de las bases",
    "apruebanse las bases concursales",
    "apruebanse las bases del concurso",
    "apruebanse las presentes bases",
    "aprueba las presentes bases",
    "aprueba bases del concurso",
    "aprueban las presentes bases",
    "apruebase el texto",
    "aprueba el texto",
    "aprueba las presentes bases del concurso",
    "aprueban las presentes bases del concurso",
    "aprueba el texto de las bases", 
    "aprueba las bases concursales del concurso",
    "aprueban las bases que regiran",
]

PATRONES_OBJETIVO = [
    "objetivo del concurso",
    "objetivo general del concurso",
    "el objetivo del concurso es",
    "el objetivo de este concurso es",
    "tiene por objetivo promover",
    "tiene como objetivo promover",
    "finalidad del concurso",
    "este concurso tiene por objetivo",
]

PATRONES_POSTULANTES = [
    r"podrán postular",
    r"pueden postular",
    r"quiénes pueden postular",
    r"quienes pueden postular",
    r"requisitos de postulación",
    r"requisitos para postular",
    r"serán elegibles",
    r"beneficiarios",
    r"investigador responsable",
    r"coinvestigador",
    r"institución patrocinante",
    r"entidad patrocinante",
    r"participantes del proyecto",
    r"podran postular",
    r"podran participar",
    r"investigadores podran postular",
    r"instituciones podran postular",
    ]

# Si quieres dejarlo global (recomendado), ponlo arriba del archivo:
_RE_RELLENO = re.compile(r"(\.{8,}|_{6,}|-{6,}|…{3,})", flags=re.IGNORECASE)
_RE_BASURA_INICIO = re.compile(r"^[\.\-_\|oO]{6,}")
_RE_PREFIJO_BASURA = re.compile(r'^[\s\.\-\_\|\*oO"“”‘’´`]{6,}')

def _recortar_prefijo_basura(s: str) -> str:
    s = (s or "").strip()
    # quita prefijos tipo "............ooooo. ”." dejando el texto real
    s = _RE_PREFIJO_BASURA.sub("", s).strip()
    # si quedaron puntos sueltos pegados al inicio, límpialos
    s = s.lstrip(" .-_|*“”\"'’‘´`").strip()
    return s

def _es_basura(frase: str) -> bool:
    f = (frase or "").strip()

    if not f:
        return True

    if _RE_RELLENO.search(f):
        return True
        
    if _RE_BASURA_INICIO.search(f):
        return True

    ADMIN_BASURA = [
        "oficial de partes",
        "repositorio de archivo institucional",
        "comite de asignacion",
        "distribuyase",
        "distribúyase",
        "anotese y comuniquese",
        "anótese y comuníquese",
        "direccion nacional",
        "contralor general",
    ]

    if any(x in f.lower() for x in ADMIN_BASURA):
        return True

    return False

def limpiar_ocr_extra(s: str) -> str:
    if not s:
        return s

    # arreglar palabras separadas por espacios del OCR
    s = re.sub(r'\b(?:[a-zA-Z]\s+){2,}[a-zA-Z]\b',
               lambda m: m.group(0).replace(" ", ""),
               s)

    s = re.sub(r"\|+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"[^\wÁÉÍÓÚáéíóúÑñ°º.,;:/()%-N°]", " ", s)
    # reparar palabras cortadas por OCR
    s = re.sub(r"\bisponible\b", "disponible", s, flags=re.I)
    s = re.sub(r"\besolucion\b", "resolucion", s, flags=re.I)
    s = re.sub(r"\bobjetiv\b", "objetivo", s, flags=re.I)
    s = re.sub(r'R\s*E\s*S\s*U\s*E\s*L\s*V\s*O', 'RESUELVO', s, flags=re.I)

    return s.strip()

def extraer_frase_con_patron(contexto: str, patron: str, *, window: int = 260) -> Optional[str]:
    if not contexto or not patron:
        return None

    raw = limpiar_ocr_extra(
        limpiar_meta_preservando_newlines(contexto)
    )

    raw = re.sub(r'\besolucion\b', 'resolucion', raw, flags=re.I)
    raw = re.sub(r'\bresoluci[oó]n\b', 'resolucion', raw, flags=re.I)
    raw = re.sub(r'\btos\s+fondecyt\b', 'los proyectos fondecyt', raw, flags=re.I)

    # -------------------------------------------------
    # DETECTAR TIPO DE CONSULTA
    # -------------------------------------------------

    tipo_consulta = None
    preg = f"{patron} {contexto[:200]}".lower()

    if "objetivo" in preg:
        tipo_consulta = "objetivo"

    elif "postular" in preg or "postulación" in preg:
        tipo_consulta = "postulacion"

    elif "requisito" in preg:
        tipo_consulta = "requisitos"

    elif "aprueba" in preg or "bases" in preg:
        tipo_consulta = "aprueba_bases"

    # Evita zonas administrativas iniciales
    if patron.lower() in [
        "objetivo del concurso",
        "objetivo general",
        "objetivo general del concurso"
    ]:

        corte_resuelvo = re.search(r"\bresuelvo\b", raw, re.I)

        # si aparece, empezar cerca pero no eliminarlo
        if corte_resuelvo and corte_resuelvo.start() > 100:
            raw = raw[corte_resuelvo.start():]


    # expansión de patrones jurídicos frecuentes
    patron_low = patron.lower()

    if patron_low in ["bases", "concurso", "aprueba", "aprueban"]:
        patron = r"(apruebanse|apruebase|aprueba|aprueban|bases\s+concursales)"

    low = raw.lower()

    # normalización OCR para palabras frecuentes
    low = re.sub(r'f\s*o\s*n\s*d\s*e\s*c\s*y\s*t', 'fondecyt', low)
    low = re.sub(r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n', 'resolucion', low)

    p_low = patron.lower()

    if not p_low:
        return None

    if p_low.startswith("("):
        pattern = p_low
        pattern_ocr = None
    else:
        pattern = re.escape(p_low)

        if len(p_low) > 2:
            pattern_ocr = r"\s*".join(list(p_low))
        else:
            pattern_ocr = None

    matches = [m.start() for m in re.finditer(pattern, low)]

    if not matches and pattern_ocr:
        matches = [m.start() for m in re.finditer(pattern_ocr, low)]

    # Helpers internos para construir candidatos
    def _limpiar_prefijos(bloque: str) -> str:
        b = (bloque or "").strip()

        pos_vistos = re.search(
            r"\b(vistos\s*:|considerando\s*:|"
            r"documento\s+electr[oó]nico|"
            r"firma(?:do)?\s+electr[oó]nicamente|"
            r"lo\s+dispu(?:esto|esta))\b",
            b,
            flags=re.IGNORECASE
        )

        if pos_vistos and pos_vistos.start() < len(b) * 0.5:
            b = b[:pos_vistos.start()]

        # limpia encabezados OCR típicos tipo "27/1/22 10:21 ssgdoc a ..."
        b = re.sub(
            r"^\d{1,2}/\d{1,2}/\d{2}\s+\d{1,2}:\d{2}\s+\w+\s+a\s+",
            "",
            b,
            flags=re.IGNORECASE
        ).strip()

        b = re.sub(r"\bR\s*E\s*S\s*O\s*L\s*U\s*C\s*I\s*O\s*N\b", "RESOLUCION", b, flags=re.I)

        return b

    def _candidato_linea(idx: int) -> Optional[str]:
        # intenta devolver "línea actual + 0-3 líneas previas relevantes"
        if "\n" not in raw:
            return None

        line_start = raw.rfind("\n", 0, idx)
        line_start = 0 if line_start == -1 else line_start + 1
        line_end = raw.find("\n", idx)
        line_end = len(raw) if line_end == -1 else line_end

        linea_match = raw[line_start:line_end].strip()
        if not linea_match:
            return None

        prev = raw[:line_start].splitlines()
        prev_lines = []

        # toma hasta 3 líneas previas "útiles"
        for k in range(1, 4):
            if len(prev) - k < 0:
                break
            cand = prev[-k].strip()
            if not cand:
                continue
            CLAVES_ADMIN = [
                "aprueb",
                "apruebase",
                "apruebanse",
                "resoluc",
                "rex",
                "tomado",
                "fecha",
            ]

            CLAVES_BASES = ["objetivo", "finalidad", "concurso", "programa", "postul", "benefici"]

            if any(w in cand.lower() for w in (CLAVES_ADMIN + CLAVES_BASES)):
                prev_lines.insert(0, cand)

        bloque = " ".join(prev_lines + [linea_match]).strip()
        bloque = _limpiar_prefijos(bloque)

        # ✅ NUEVO: recorta prefijos basura ANTES de post_corte_frase / _es_basura
        bloque = _recortar_prefijo_basura(bloque)

        if re.search(pattern, bloque, re.I):
            frase = post_corte_frase(bloque, max_chars=window)
            if frase and not _es_basura(frase) and len(frase) > 40:
                return frase
        return None

    def _candidato_ventana(idx: int) -> Optional[str]:
        back = int(window * 0.85)
        fwd = int(window * 0.30)  # un poco más de forward ayuda mucho en OCR

        start = max(0, idx - back)
        end = min(len(raw), idx + len(p_low) + fwd)
        frag = raw[start:end].strip(" \t,;:-")
        frag = _limpiar_prefijos(frag)

        # ✅ NUEVO: recorta prefijos basura ANTES de post_corte_frase / _es_basura
        frag = _recortar_prefijo_basura(frag)

        if re.search(pattern, frag, re.I):
            frase = post_corte_frase(frag, max_chars=window)
            if frase and not _es_basura(frase) and len(frase) > 40:
                return frase
        return None

    # Estrategia: recorre matches en orden, pero si un candidato es basura, sigue buscando.
    candidatos = []

    for idx in matches:

        cand = _candidato_linea(idx)
        if cand and "objetivo del proyecto" not in cand.lower():
            candidatos.append(cand)

        cand = _candidato_ventana(idx)
        if cand and "objetivo del proyecto" not in cand.lower():
            candidatos.append(cand)

    if not candidatos:
        return None

    # ⭐ elegir mejor frase jurídica
    candidatos.sort(
        key=lambda x: (
            _score_frase_juridica(x, tipo_consulta),
            1 if x.strip().endswith(".") else 0,
            -abs(len(x) - 150),
            len(x)
        ),
        reverse=True
    )

    return candidatos[0]

def recortar_frase_limpia(texto, max_len=500):
    if len(texto) <= max_len:
        return texto

    corte = texto[:max_len]
    ultimo_punto = max(
        corte.rfind("."),
        corte.rfind(";"),
        corte.rfind(":")
    )

    if ultimo_punto > 200:
        return corte[:ultimo_punto+1]

    return corte + "…"


def extraer_resolucion_en_frase(contexto: str) -> Tuple[Optional[str], Optional[str]]:
    if not contexto:
        return None, None

    m = re.search(r"\b(\d{1,5}\s*[/\-\.]\s*\d{4})\b", contexto)
    if not m:
        return None, None

    num = m.group(1)
    frase = extraer_frase_con_patron(contexto, num)
    return num, frase

