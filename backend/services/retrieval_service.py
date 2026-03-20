# backend/services/retrieval_service.py

from backend.services.retrieval.doc_utils import extraer_nombre_documento
from backend.services.retrieval.intent_utils import (
    detectar_seccion_simple,
    detectar_modo_cita,
)
from backend.services.retrieval.filter_builder import construir_filtro_inicial
from backend.services.retrieval.chunk_filters import filtrar_posicional
from backend.services.retrieval.ranking_pipeline import rankear_chunks
from backend.services.retrieval.citation_utils import aplicar_filtro_cita
from backend.services.retrieval_mongo_repo import find_docs
from backend.services.retrieval_text_utils import tokens, normalizar
from backend.services.consulta_utils_text import extraer_palabra_entre_comillas

import re


# ==========================================
# 🔥 DETECTOR DE ARTÍCULO
# ==========================================

MAPA_ARTICULOS = {
    "primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4,
    "quinto": 5, "sexto": 6, "septimo": 7, "séptimo": 7,
    "octavo": 8, "noveno": 9, "decimo": 10, "décimo": 10
}

def detectar_articulo(pregunta: str):
    p = pregunta.lower()

    m = re.search(r'art[ií]culo\s+(\d+)', p)
    if m:
        return int(m.group(1))

    m = re.search(
        r'art[ií]culo\s+(primero|segundo|tercero|cuarto|quinto|sexto|septimo|séptimo|octavo|noveno|decimo|décimo)',
        p
    )
    if m:
        return MAPA_ARTICULOS.get(m.group(1))

    return None


# ==========================================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================================

def obtener_contexto(
    pregunta: str,
    *,
    tipo_busqueda: str | None = None,
    modo_cita: bool = False,
    filtro_doc: str | None = None,
    top_k: int = 8,
    scan: int = 4000,
):

    docs = []  # 🔥 FIX CRÍTICO

    # --------------------------------------------------
    # 🔎 Detectar documento
    # --------------------------------------------------

    nombre_doc = filtro_doc or extraer_nombre_documento(pregunta)

    if nombre_doc:
        nombre_doc = normalizar(nombre_doc)
        scan = max(scan, 5000)

    # --------------------------------------------------
    # 🔎 Detectar modo cita
    # --------------------------------------------------

    if detectar_modo_cita(pregunta):
        modo_cita = True
        top_k = max(top_k, 6)

    # --------------------------------------------------
    # 🔎 Detectar intención
    # --------------------------------------------------

    seccion = detectar_seccion_simple(pregunta)
    articulo = detectar_articulo(pregunta)

    pregunta_norm = normalizar(pregunta)

    busca_objetivo = "objetivo" in pregunta_norm
    busca_postulacion = any(x in pregunta_norm for x in ["postular", "beneficiario"])
    busca_requisito = "requisito" in pregunta_norm
    busca_resolucion = any(x in pregunta_norm for x in ["resuelve", "resolucion", "aprueba"])

    # --------------------------------------------------
    # 🔎 Construir filtro
    # --------------------------------------------------

    pregunta_low = normalizar(pregunta)

    palabra = extraer_palabra_entre_comillas(pregunta)

    # 🔥 1. palabra entre comillas (PRIORIDAD MÁXIMA)
    if palabra:
        filtro_base = {
            "contenido_norm": {"$regex": palabra, "$options": "i"}
        }

    # 🔥 2. resolución (CLAVE TESIS)
    elif any(x in pregunta_low for x in ["resolucion", "res.", "rex", "resuelve"]):
        filtro_base = {
            "$or": [
                {"contenido_norm": {"$regex": "resolucion", "$options": "i"}},
                {"contenido_norm": {"$regex": "resolución", "$options": "i"}},
                {"contenido_norm": {"$regex": "resuelv", "$options": "i"}},
                {"contenido_norm": {"$regex": "rex", "$options": "i"}},
                {"contenido_norm": {"$regex": "res\\.", "$options": "i"}},
            ]
        }

    # 🔥 3. lo que ya tenías
    elif "aprueb" in pregunta_low:
        filtro_base = {
            "$or": [
                {"contenido_norm": {"$regex": "aprueb", "$options": "i"}},
                {"contenido_norm": {"$regex": "aprueban", "$options": "i"}},
                {"contenido_norm": {"$regex": "apruebase", "$options": "i"}},
            ]
        }

    elif "objetivo" in pregunta_low:
        filtro_base = {
            "$or": [
                {"contenido_norm": {"$regex": "objetivo", "$options": "i"}},
                {"contenido_norm": {"$regex": "finalidad", "$options": "i"}},
            ]
        }

    elif "requisito" in pregunta_low:
        filtro_base = {
            "$or": [
                {"contenido_norm": {"$regex": "requisito", "$options": "i"}},
                {"contenido_norm": {"$regex": "postulacion", "$options": "i"}},
                {"contenido_norm": {"$regex": "deben", "$options": "i"}},
            ]
        }

    else:
        filtro_base = construir_filtro_inicial(pregunta, None)

    if nombre_doc:

        filtro_doc_q = {
            "$or": [
                {"metadata.documento_norm": {"$regex": nombre_doc, "$options": "i"}},
                {"metadata.documento": {"$regex": nombre_doc, "$options": "i"}}
            ]
        }

        if filtro_base:
            filtro = {"$and": [filtro_doc_q, filtro_base]}
        else:
            filtro = filtro_doc_q

    else:
        filtro = filtro_base

    print("\n🧪 FILTRO FINAL:", filtro)

    # --------------------------------------------------
    # 🔎 Obtener documentos
    # --------------------------------------------------

    docs = find_docs(filtro, scan=scan) or []

    print("📦 DOCS ENCONTRADOS:", len(docs))

    # 🔥 fallback si filtro fue demasiado estricto
    if len(docs) == 0 and nombre_doc:

        print("⚠️ fallback por documento")

        docs = find_docs(
            {
                "metadata.documento_norm": {
                    "$regex": nombre_doc,
                    "$options": "i"
                }
            },
            scan=min(scan, 1000)
        ) or []

        print("📦 DOCS fallback:", len(docs))

    if len(docs) == 0:
        return ""

    # --------------------------------------------------
    # 🔥 Limpieza
    # --------------------------------------------------

    docs_limpios = []

    for d in docs:

        cont = d.get("contenido_norm") or d.get("texto_extraido")

        if isinstance(cont, dict):
            cont = cont.get("contenido") or cont.get("texto") or ""

        elif isinstance(cont, list):
            cont = " ".join(
                x.get("contenido", "") if isinstance(x, dict) else str(x)
                for x in cont
            )

        if not isinstance(cont, str):
            cont = str(cont)

        if not cont or len(cont) < 40:
            continue

        cont_norm = normalizar(cont)

        if any(x in cont_norm for x in ["anexo", "tabla", "bibliografia"]):
            continue

        d["contenido_raw"] = cont
        d["contenido_norm"] = cont_norm
        
        docs_limpios.append(d)

    docs = docs_limpios

    if not docs:
        return ""

    # --------------------------------------------------
    # 🔎 Tokens
    # --------------------------------------------------

    toks = tokens(pregunta) or []
    STOPWORDS = {"del", "las", "los", "una", "uno", "para", "como"}

    toks = [
        t for t in toks
        if len(t) > 2 and t not in STOPWORDS
    ]

    # --------------------------------------------------
    # 🔥 SCORING
    # --------------------------------------------------

    for d in docs:

        meta = d.get("metadata") or {}
        cont = d["contenido_norm"]

        score = 0

        # léxico
        hits = sum(1 for t in toks if t in cont)

        if hits >= 4: score += 8
        elif hits == 3: score += 6
        elif hits == 2: score += 3

        tipo = meta.get("tipo_chunk")

        if tipo == "resolucion": score += 10
        elif tipo == "objetivo": score += 8
        elif tipo == "postulacion": score += 8
        elif tipo == "requisito": score += 6
        elif tipo == "considerando": score += 3

        if busca_objetivo and tipo == "objetivo": score += 10
        if busca_postulacion and tipo == "postulacion": score += 10
        if busca_requisito and tipo == "requisito": score += 8
        if busca_resolucion and tipo == "resolucion": score += 12

        if articulo:
            art_meta = meta.get("articulo")
            if art_meta:
                m = re.search(r'\d+', str(art_meta))
                if m and int(m.group()) == articulo:
                    score += 20

        if meta.get("chunk_index", 999) < 5:
            score += 3

        if meta.get("es_resolutivo"):
            score += 12

        # 🔥 boost especial para citas
        if modo_cita:
            if any(x in cont for x in ["resolucion", "aprueba", "objetivo"]):
                score += 8

        d["pre_score"] = score

    docs = sorted(docs, key=lambda x: x["pre_score"], reverse=True)[:200]

    # --------------------------------------------------
    # 🔎 Filtro por sección
    # --------------------------------------------------

    if seccion:
        filtrados = filtrar_posicional(docs, seccion)
        if len(filtrados) > 3:
            docs = filtrados

    # --------------------------------------------------
    # 🔥 Ranking final
    # --------------------------------------------------

    ranked = rankear_chunks(
        pregunta,
        docs,
        toks,
        modo_cita=modo_cita
    )

    # --------------------------------------------------
    # 🔥 Selección
    # --------------------------------------------------

    resultados = []
    seen = set()

    for r in ranked:

        cont = r.get("contenido_norm")

        if not cont or cont in seen:
            continue

        if modo_cita:
            cont_filtrado = aplicar_filtro_cita(pregunta, cont, nombre_doc is not None)
            if cont_filtrado:
                cont = cont_filtrado

        resultados.append(cont.strip())
        seen.add(cont)

        if len(resultados) >= top_k:
            break

    # fallback final
    if not resultados:
        for d in docs[:top_k]:
            cont = d.get("contenido_norm")
            if cont:
                resultados.append(cont.strip())

    contexto = "\n\n".join(resultados)

    return contexto[:3500]
