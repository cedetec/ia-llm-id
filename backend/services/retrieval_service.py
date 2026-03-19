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
            scan=scan
        ) or []

        print("📦 DOCS fallback:", len(docs))

    if len(docs) == 0:
        return ""

    # --------------------------------------------------
    # 🔥 Limpieza
    # --------------------------------------------------

    docs_limpios = []

    for d in docs:

        cont = d.get("contenido") or d.get("texto_extraido")

        if not cont or len(cont) < 40:
            continue

        cont_norm = normalizar(cont)

        if any(x in cont_norm for x in ["anexo", "tabla", "bibliografia"]):
            continue

        d["contenido_norm"] = cont_norm
        docs_limpios.append(d)

    docs = docs_limpios

    if not docs:
        return ""

    # --------------------------------------------------
    # 🔎 Tokens
    # --------------------------------------------------

    toks = tokens(pregunta) or []
    toks = [t for t in toks if len(t) > 3]

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

        cont = r.get("contenido")

        if not cont or cont in seen:
            continue

        if modo_cita:
            cont = aplicar_filtro_cita(pregunta, cont, nombre_doc is not None)
            if not cont:
                continue

        resultados.append(cont.strip())
        seen.add(cont)

        if len(resultados) >= top_k:
            break

    # fallback final
    if not resultados:
        for d in docs[:top_k]:
            cont = d.get("contenido")
            if cont:
                resultados.append(cont.strip())

    contexto = "\n\n".join(resultados)

    return contexto[:3500]
