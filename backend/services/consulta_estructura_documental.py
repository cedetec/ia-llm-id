# backend/services/consulta_estructura_documental.py
from __future__ import annotations
import unicodedata

def normalizar_basico(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.lower()

# =========================================================
# 📄 Clasificación avanzada de tipo documental
# =========================================================
def clasificar_documento_avanzado(texto: str) -> str:
    t = (texto or "").lower()

    reglas = {
        "resolucion_aprobacion": [
            "resolución exenta",
            "tómese razón",
            "contralor general",
            "aprueba bases"
        ],
        "bases_concurso": [
            "bases del concurso",
            "objetivo del concurso",
            "requisitos de postulación"
        ],
        "convenio": [
            "convenio de financiamiento",
            "las partes acuerdan"
        ],
        "anexo": [
            "anexo",
            "tabla de evaluación"
        ]
    }

    for tipo, patrones in reglas.items():
        if any(p in t for p in patrones):
            return tipo

    return "desconocido"


# =========================================================
# 📚 Diccionario de secciones semánticas
# =========================================================
SECCIONES = {
    "objetivo": ["objetivo", "finalidad del concurso"],
    "postulantes": ["podrán postular", "beneficiarios"],
    "requisitos": ["requisitos de postulación"],
    "financiamiento": ["monto máximo", "financiamiento"],
    "evaluacion": ["criterios de evaluación"],
}


# =========================================================
# 🔎 Segmentación del documento por secciones
# =========================================================
import re

def detectar_secciones(texto: str):
    bloques = {}

    patron = re.compile(
        r'(OBJETIVO|REQUISITOS|FINANCIAMIENTO|EVALUACIÓN|CRITERIOS|POSTULACIÓN)',
        re.IGNORECASE
    )

    matches = list(patron.finditer(texto))

    for i, m in enumerate(matches):
        inicio = m.start()
        fin = matches[i+1].start() if i+1 < len(matches) else len(texto)

        nombre = m.group(0).lower()
        bloques[nombre] = texto[inicio:fin].strip()

    return bloques
