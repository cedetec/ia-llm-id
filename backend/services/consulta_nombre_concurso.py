# backend/services/consulta_nombre_concurso.py
from __future__ import annotations
import re
from typing import Optional
from backend.services.intent_service import extraer_nombre_concurso
from backend.services.consulta_utils_text import normalizar_txt

def extraer_nombre_concurso_fallback(p: str) -> Optional[str]:
    p = (p or "").strip()
    pl = p.lower()

    m = re.search(r"\bconcurso\s+([^\?\.\n]+)", p, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    for key in ["ANID", "FONDECYT", "FONDAP", "BASAL", "ANILLOS", "FONDEQUIP", "INES", "BECAS", "DOCTORADO"]:
        if key.lower() in pl:
            if key == "ANID":
                m2 = re.search(r"\banid\b\s+(.+?)(?:\?|\.|,|;|:|$)", p, flags=re.IGNORECASE)
                if m2:
                    return f"ANID {m2.group(1).strip()}"
                return "ANID"

            if key in ("BECAS", "DOCTORADO"):
                m3 = re.search(rf"\b{key}\b\s+(.+?)(?:\?|\.|,|;|:|$)", p, flags=re.IGNORECASE)
                if m3:
                    tail = m3.group(1).strip()
                    tail = re.sub(r"^(de|del|la|el|los|las)\s+", "", tail, flags=re.IGNORECASE)
                    return f"{key} {tail}"

            return key

    return None

def extraer_nombre_concurso_flexible(pregunta: str) -> Optional[str]:
    p = normalizar_txt(pregunta).strip()

    m = re.search(r'“([^”]{3,120})”|"([^"]{3,120})"', p)
    if m:
        return (m.group(1) or m.group(2)).strip()

    m = re.search(r"\bconcurso\b\s+(.+?)(?:\?|\.|,|;|:|$)", p, flags=re.IGNORECASE)
    if m:
        nombre = m.group(1).strip()
        nombre = re.sub(r"\b(cita|textual|frase|literal|exacta)\b.*$", "", nombre, flags=re.IGNORECASE).strip()
        return nombre if len(nombre) >= 4 else None

    pl = p.lower()
    if "ines" in pl and "genero" in pl:
        return "InES Género"
    if "fondecyt" in pl:
        return "FONDECYT"
    if "anid" in pl:
        m = re.search(r"\banid\b\s+(.+?)(?:\?|\.|,|;|:|$)", p, flags=re.IGNORECASE)
        if m:
            return f"ANID {m.group(1).strip()}"
        return "ANID"

    return None

def obtener_nombre_pedido(pregunta: str, pregunta_norm: str) -> Optional[str]:
    candidatos = [
        extraer_nombre_concurso(pregunta_norm),
        extraer_nombre_concurso(pregunta),
        extraer_nombre_concurso_flexible(pregunta_norm),
        extraer_nombre_concurso_flexible(pregunta),
        extraer_nombre_concurso_fallback(pregunta_norm),
        extraer_nombre_concurso_fallback(pregunta),
    ]

    candidatos_validos = [c for c in candidatos if c and c.strip()]
    if not candidatos_validos:
        return None

    # elegir el más largo (más específico)
    candidatos_validos.sort(key=lambda x: len(x), reverse=True)
    nombre = candidatos_validos[0]

    # 🔥 AHORA sí limpiar correctamente
    nombre = normalizar_txt(nombre)

    nombre = re.sub(
        r"\b(cita|textual|frase|literal|exacta|exactamente|tal cual)\b.*$",
        "",
        nombre,
        flags=re.IGNORECASE,
    ).strip()

    nombre = re.sub(
        r"\b(aunque(?:\s+no\s+(?:exista|est(?:e|é))(?:\s+en\s+los\s+documentos)?)?)\b.*$",
        "",
        nombre,
        flags=re.IGNORECASE,
    ).strip()

    nombre = re.sub(
        r"\b(objetivo|objetivo general|persigue|finalidad|propósito|proposito)\b.*$",
        "",
        nombre,
        flags=re.IGNORECASE,
    ).strip()

    nombre = re.sub(r"[\"”\“]+", "", nombre).strip()

    return nombre if len(nombre) >= 3 else None
