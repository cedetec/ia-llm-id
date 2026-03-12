# backend/services/retrieval/query_builders.py
from __future__ import annotations
import re
from typing import List, Dict, Any

def agregar_and(filtro, nuevo):
    if not filtro:
        return nuevo
    if "$and" in filtro:
        return {"$and": filtro["$and"] + [nuevo]}
    return {"$and": [filtro, nuevo]}

def inferir_tipo_documento_desde_pregunta(pregunta: str) -> str | None:
    p = pregunta.lower()

    # primero actos administrativos (más específicos)
    if any(k in p for k in [
        "resolución",
        "res.",
        "aprueba",
        "exenta"
    ]):
        return "resolucion_aprobatoria"

    # luego bases
    if any(k in p for k in [
        "objetivo",
        "quiénes pueden postular",
        "requisitos",
        "financiamiento",
        "beneficiarios",
        "postulación"
    ]):
        return "bases"

    return None

def inferir_seccion_objetivo(pregunta: str) -> str | None:
    p = pregunta.lower()

    if "objetivo" in p and "proyecto" not in p:
        return "objetivo"

    if "quiénes pueden postular" in p or "beneficiarios" in p:
        return "beneficiarios"

    if "requisito" in p:
        return "requisitos"

    if "financiamiento" in p or "monto" in p:
        return "financiamiento"

    return None

def construir_filtro_seccion(seccion: str) -> Dict[str, Any]:
    return {
        "metadata.seccion": seccion
    }

def extraer_nombre_documento(pregunta: str) -> str | None:
    """
    Extrae nombres tipo:
    59-21REXBases.pdf
    Bases.pdf
    Aprueba-Bases-Concurso-ID-2021.pdf
    """
    m = re.search(r'([A-Za-z0-9\-_]+\.pdf)', pregunta, re.IGNORECASE)
    if not m:
        return None
    return m.group(1)

def normalizar_nombre(nombre: str) -> str:
    nombre = nombre.lower().strip()
    nombre = nombre.replace(".pdf", "")
    nombre = re.sub(r"\s+", "", nombre)
    return nombre

def construir_filtro_documento_exacto(nombre_doc: str) -> Dict[str, Any]:
    nombre_norm = normalizar_nombre(nombre_doc)

    return {
        "metadata.documento_norm": nombre_norm
    }

def construir_filtro_tipo_documento(tipo: str) -> Dict[str, Any]:
    return {
        "metadata.tipo_documento": tipo
    }

def regex_or(tokens: List[str]) -> str:
    toks = [t for t in tokens if t]
    toks = sorted(set(toks), key=len, reverse=True)[:25]
    if not toks:
        return ""

    parts = [fr"\b{re.escape(t)}\b" for t in toks]

    MAX_REGEX_LEN = 500
    regex = "(?:" + "|".join(parts) + ")"

    return regex[:MAX_REGEX_LEN]

def construir_filtro_base(regex: str) -> Dict[str, Any]:
    return {"contenido": {"$regex": regex, "$options": "i"}}

def _tiene_restriccion_documento(filtro: Dict[str, Any]) -> bool:
    """
    Retorna True si el filtro (incluyendo anidado en $and/$or)
    ya contiene alguna restricción por metadata.documento.
    """
    if not isinstance(filtro, dict):
        return False

    # Caso directo: {"metadata.documento": {...}}
    if "metadata.documento" in filtro:
        return True

    # Caso anidado: {"$and": [ ... ]} o {"$or": [ ... ]}
    for k in ("$and", "$or"):
        if k in filtro and isinstance(filtro[k], list):
            for part in filtro[k]:
                if _tiene_restriccion_documento(part):
                    return True

    return False

def aplicar_prefiltro_doc(filtro, doc_pref_tokens, pregunta=""):

    nombre_doc = extraer_nombre_documento(pregunta)
    tipo_doc = inferir_tipo_documento_desde_pregunta(pregunta)
    seccion = inferir_seccion_objetivo(pregunta)

    if seccion:
        filtro = agregar_and(filtro, construir_filtro_seccion(seccion))

    if nombre_doc:
        return agregar_and(filtro, construir_filtro_documento_exacto(nombre_doc))

    if tipo_doc:
        filtro = agregar_and(filtro, construir_filtro_tipo_documento(tipo_doc))

    if not doc_pref_tokens:
        return filtro

    filtro_doc = {
        "$or": [
            {"metadata.documento": {"$regex": t, "$options": "i"}}
            for t in doc_pref_tokens
        ]
    }

    return agregar_and(filtro, filtro_doc)

def aplicar_estricto_por_anio(filtro: Dict[str, Any], regex: str, anio: str) -> Dict[str, Any]:

    filtro_contenido_estricto = {
        "$and": [
            {"contenido": {"$regex": regex, "$options": "i"}},
            {"contenido": {"$regex": anio, "$options": "i"}}
        ]
    }

    return agregar_and(filtro, filtro_contenido_estricto)

    if "$and" in filtro:
        and_parts = []
        for part in filtro["$and"]:
            if isinstance(part, dict) and "contenido" in part:
                continue
            and_parts.append(part)
        and_parts.insert(0, filtro_contenido_estricto)
        return {"$and": and_parts}

    out = dict(filtro)
    out.update(filtro_contenido_estricto)
    return out
