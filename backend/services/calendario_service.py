# backend/services/calendario_service.py
from database.mongo import documents_collection
from datetime import datetime
import re
from rapidfuzz import fuzz
from typing import Optional, Tuple, List
import unicodedata

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

# -----------------------------
# Cargar calendario desde JSON
# -----------------------------
def cargar_calendario():
    docs = documents_collection.find({
        "tipo": {"$in": ["JSON", "CALENDARIO"]}
    })

    calendario_total = []

    for doc in docs:
        contenido = doc.get("contenido")

        if isinstance(contenido, list):
            calendario_total.extend(contenido)

        elif isinstance(contenido, dict) and isinstance(contenido.get("contenido"), list):
            calendario_total.extend(contenido["contenido"])

    return calendario_total

def _candidatos_texto(concurso_doc: dict) -> List[Tuple[str, str]]:
    cands: List[Tuple[str, str]] = []

    t = concurso_doc.get("concurso")
    if isinstance(t, str) and t.strip():
        cands.append((t, "concurso"))

    concursos = concurso_doc.get("concursos")
    if isinstance(concursos, list):
        for i, item in enumerate(concursos):
            if isinstance(item, dict):
                n = item.get("nombre")
                if isinstance(n, str) and n.strip():
                    cands.append((n, f"concursos[{i}].nombre"))

    aliases = concurso_doc.get("aliases")
    if isinstance(aliases, list):
        for i, a in enumerate(aliases):
            if isinstance(a, str) and a.strip():
                cands.append((a, f"aliases[{i}]"))

    return cands

# -----------------------------
# Buscar concurso por nombre
# -----------------------------
def buscar_concurso(
    nombre: str,
    estricto: bool = False,
    threshold: int = 80
) -> Optional[dict]:
    nombre_n = normalizar(nombre)
    calendario = cargar_calendario()
    if not calendario:
        return None

    # FASE 1: exacto (siempre)
    for c in calendario:
        for texto, _src in _candidatos_texto(c):
            if normalizar(texto) == nombre_n:
                return c

    if estricto:
        return None

    # FASE 2: fuzzy matching (genérico)
    mejor_doc = None
    mejor_score = -1
    mejor_len = 10**9

    for c in calendario:
        for texto, _src in _candidatos_texto(c):
            t_n = normalizar(texto)
            if not t_n:
                continue

            s1 = fuzz.token_set_ratio(nombre_n, t_n)
            s2 = fuzz.partial_ratio(nombre_n, t_n)
            score = max(s1, s2)
            
            if len(nombre_n) < 5:
                threshold = 90

            if score < threshold:
                continue

            if (score > mejor_score) or (score == mejor_score and len(t_n) < mejor_len):
                mejor_doc = c
                mejor_score = score
                mejor_len = len(t_n)

    return mejor_doc

# -----------------------------
# Obtener fechas del concurso
# -----------------------------
def obtener_fechas_concurso(nombre):
    """
    Retorna un diccionario con inicio, cierre, fallo y categoría
    del concurso solicitado.
    """
    concurso = buscar_concurso(nombre)
    if not concurso:
        return None

    return {
        "concurso": concurso.get("concurso"),
        "inicio": concurso.get("inicio"),
        "cierre": concurso.get("cierre"),
        "fallo": concurso.get("fallo"),
        "categoria": concurso.get("categoria"),
    }

# -----------------------------
# Concursos que cierran en marzo 2025
# -----------------------------
def concursos_que_cierran_en_marzo():
    calendario = cargar_calendario()
    return [
        c for c in calendario
        if isinstance(c.get("cierre"), str) and c["cierre"].startswith("2025-03")
    ]


# -----------------------------
# Concurso con cierre más tardío
# -----------------------------
def concurso_cierra_mas_tarde():
    calendario = cargar_calendario()

    fechas_validas = [
        c for c in calendario
        if _es_fecha_iso(c.get("cierre"))
    ]

    if not fechas_validas:
        return None

    return max(
        fechas_validas,
        key=lambda c: datetime.fromisoformat(c["cierre"])
    )

def _es_fecha_iso(valor: str) -> bool:
    return isinstance(valor, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor.strip()))

def concursos_abiertos_hoy():
    calendario = cargar_calendario()
    hoy = datetime.now().date()
    abiertos = []

    for c in calendario:
        ini = c.get("inicio")
        cie = c.get("cierre")

        # Ignorar concursos sin fechas reales
        if not _es_fecha_iso(ini) or not _es_fecha_iso(cie):
            continue

        inicio = datetime.fromisoformat(ini).date()
        cierre = datetime.fromisoformat(cie).date()

        if inicio <= hoy <= cierre:
            abiertos.append(c)

    return abiertos

def concursos_por_mes(mes: str, campo: str):
    calendario = cargar_calendario()
    mes = mes.lower()

    MESES = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    if mes not in MESES:
        return []

    codigo_mes = MESES[mes]
    resultados = []

    for c in calendario:
        valor = c.get(campo)
        if not isinstance(valor, str):
            continue
        v = valor.strip()

        # aceptar YYYY-MM-DD o YYYY-MM
        if not (re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) or re.fullmatch(r"\d{4}-\d{2}", v)):
            continue

        # match por mes en cualquier año
        if v[5:7] == codigo_mes:
            resultados.append(c)

    return resultados
