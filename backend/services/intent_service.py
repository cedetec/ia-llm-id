# services/intent_service.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

class Intent(str, Enum):
    APERTURA = "apertura"
    CIERRE = "cierre"
    FALLO = "fallo"
    FECHAS = "fechas"
    ABIERTOS = "abiertos"
    FALLO_POR_MES = "fallo_por_mes"
    INICIO_POR_MES = "inicio_por_mes"
    CIERRE_MAS_TARDE = "cierre_mas_tarde"
    CIERRE_POR_MES = "cierre_por_mes"
    CONTAR_CONCURSOS = "contar_concursos"
    MONTO = "monto"
    CONCEPTUAL_DEF = "conceptual_def"
    CONCEPTUAL_POSTULANTES = "conceptual_postulantes"
    DESCONOCIDA = "desconocida"

MESES = {
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre", "dic"
}

REEMPLAZOS = {
    "post becas": "postdoctorado becas",
    "postdoc": "postdoctorado",
    "post-doc": "postdoctorado",
    "post doctorado": "postdoctorado",
    "fulbright anid": "fulbright",
    "anid fulbright": "fulbright",
}

def quitar_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def normalizar_pregunta(pregunta: str) -> str:
    p = quitar_tildes(pregunta.lower())
    for k, v in REEMPLAZOS.items():
        p = p.replace(k, v)
    p = re.sub(r"\s+", " ", p).strip()
    return p


def extraer_nombre_concurso(pregunta: str) -> str | None:
    if not pregunta:
        return None

    p = pregunta.lower()

    # 1) Prioridad: texto entre comillas
    match = re.search(r'“([^”]+)”|"([^"]+)"', pregunta)
    if match:
        return (match.group(1) or match.group(2)).strip()

    # 2) Patrones conocidos (extensible)
    patrones = [
        r"(ines\s+género(?:\s+\d{4})?)",
        r"(ines\s+genero(?:\s+\d{4})?)",
        r"(fondecyt(?:\s+\d{4})?)",
        r"(fondecyt\s+regular(?:\s+\d{4})?)",
        r"(fondecyt\s+iniciación(?:\s+\d{4})?)",
        r"(corfo(?:\s+\d{4})?)",
        r"(anid(?:\s+\d{4})?)",
    ]

    for pat in patrones:
        m = re.search(pat, p, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return None

def extraer_mes(pregunta_normalizada: str) -> str | None:
    # Devuelve mes en texto ("enero"... "diciembre") o None
    for m in MESES:
        if re.search(rf"\b{re.escape(m)}\b", pregunta_normalizada):
            return "diciembre" if m == "dic" else m
    return None

def detectar_intent(p: str) -> Intent:

    p = normalizar_pregunta(p)
    # Bloqueos conceptuales
    if any(x in p for x in ["postulantes", "dirigido", "dirigida", "beneficiarios", "perfil", "tipo de postulantes", "a quien esta dirigido", "para quien es"]):
        return Intent.CONCEPTUAL_POSTULANTES
    if any(x in p for x in ["que es", "definicion", "en que consiste", "segun anid", "de que se trata"]):
        return Intent.CONCEPTUAL_DEF

    # Monto
    if any(x in p for x in ["monto", "financiamiento", "financia", "financiar"]):
        return Intent.MONTO

    # Agregadas
    if any(x in p for x in ["abiertos", "abierto actualmente", "abiertos actualmente", "abiertos hoy"]):
        return Intent.ABIERTOS
    mes = extraer_mes(p)
    if mes and "cierre" in p:
        return Intent.CIERRE_POR_MES
    if any(x in p for x in ["mas tarde", "ultima fecha", "última fecha", "cierre mas tardio"]):
        return Intent.CIERRE_MAS_TARDE
    if any(x in p for x in ["cuantos concursos", "cuántos concursos", "cantidad de concursos"]):
        return Intent.CONTAR_CONCURSOS

    # Por mes
    if mes and "fallo" in p:
        return Intent.FALLO_POR_MES
    if mes and ("inicio" in p or "apertura" in p):
        return Intent.INICIO_POR_MES

    # Individuales típicas
    if any(x in p for x in ["cuando se abrio", "cuándo se abrió", "abrio", "abertura", "apertura", "inicio del concurso", "inicio:"]):
        return Intent.APERTURA
    if any(x in p for x in ["cierre", "cerro", "cerró", "postulacion", "postulación"]):
        return Intent.CIERRE
    if any(x in p for x in ["fallo", "resultado", "adjudicacion", "adjudicación"]):
        return Intent.FALLO
    if any(x in p for x in ["fechas", "cronograma", "calendario"]):
        return Intent.FECHAS

    return Intent.DESCONOCIDA

# =========================================================
# 🎯 Clasificación semántica específica de intención
# =========================================================
def clasificar_intencion(p: str) -> str:

    p = normalizar_pregunta(p)

    # =========================
    # OBJETIVO DEL CONCURSO
    # =========================
    if any(x in p for x in [
        "objetivo del concurso",
        "objetivo general del concurso",
        "el objetivo del concurso es",
        "el objetivo de este concurso es",
        "objetivo general",
        "proposito del concurso",
        "propósito del concurso",
        "finalidad del concurso",
        "para que es el concurso"
    ]):
        return "objetivo"

    # =========================
    # POSTULANTES
    # =========================
    if any(x in p for x in [
        "quienes pueden postular",
        "quien puede postular",
        "quién puede postular",
        "pueden postular",
        "podran postular",
        "podrán postular",
        "postulantes",
        "beneficiarios",
        "dirigido a",
        "a quien esta dirigido"
    ]):
        return "postulantes"

    # =========================
    # REQUISITOS
    # =========================
    if any(x in p for x in [
        "requisitos",
        "requisito",
        "condiciones",
        "criterios de admisibilidad",
        "que se necesita para postular"
    ]):
        return "requisitos"

    # =========================
    # FINANCIAMIENTO
    # =========================
    if any(x in p for x in [
        "financiamiento",
        "monto",
        "cuanto financia",
        "cuanto dinero",
        "subsidio",
        "fondos"
    ]):
        return "financiamiento"

    # =========================
    # RESOLUCIONES
    # =========================
    if any(x in p for x in [
        "numero de resolucion",
        "número de resolución",
        "resolucion exenta",
        "res ex",
        "resolucion"
    ]):
        return "numero_resolucion"

    # =========================
    # APROBACIÓN DE BASES
    # =========================
    if any(x in p for x in [
        "aprueba bases",
        "aprobacion de bases",
        "aprobación de bases",
        "se aprueban las bases",
        "aprueban las bases",
        "apruebanse las bases",
        "aprueban las bases concursales",
    ]):
        return "aprobacion_bases"
    return "general"
