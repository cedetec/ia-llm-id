# backend/services/retrieval_service.py

from backend.services.retrieval.doc_utils import extraer_nombre_documento, normalizar_nombre_doc
from backend.services.retrieval.intent_utils import detectar_seccion_simple, detectar_modo_cita
from backend.services.retrieval.filter_builder import construir_filtro_inicial
from backend.services.retrieval.chunk_filters import filtrar_posicional
from backend.services.retrieval.ranking_pipeline import rankear_chunks
from backend.services.retrieval.citation_utils import aplicar_filtro_cita
from backend.services.retrieval_mongo_repo import find_docs
from backend.services.retrieval_text_utils import tokens, normalizar

import re


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


# ==================================================
# 🔥 FUNCIÓN PRINCIPAL OPTIMIZADA
# ==================================================

def obtener_contexto(
    pregunta: str,
    *,
    tipo_busqueda: str | None = None,
    modo_cita: bool = False,
    filtro_doc: str | None = None,
    top_k: int = 8,
    scan: int = 300,
):

    # --------------------------------------------------
    # 🔎 DOCUMENTO
    # --------------------------------------------------

    nombre_doc = filtro_doc or extraer_nombre_documento(pregunta)

    nombre_doc_norm = None
    if nombre_doc:
        nombre_doc_norm = normalizar_nombre_doc(nombre_doc)
        scan = min(max(scan, 200), 600)

    # --------------------------------------------------
    # 🔎 INTENCIÓN
    # --------------------------------------------------

    if detectar_modo_cita(pregunta):
        modo_cita = True
        top_k = max(top_k, 6)

    seccion = detectar_seccion_simple(pregunta)
    articulo = detectar_articulo(pregunta)
    pregunta_norm = normalizar(pregunta)

    # --------------------------------------------------
    # 🔎 TOKENS LIMPIOS
    # --------------------------------------------------

    STOPWORDS = {
        "documento", "extrae", "frase", "textual",
        "menciona", "indique", "responde", "cita",
        "aparece", "donde", "parte", "solo"
    }

    toks = tokens(pregunta)
    toks = [t for t in toks if len(t) > 4 and t not in STOPWORDS][:4]

    # --------------------------------------------------
    # 🔥 FILTRO
    # --------------------------------------------------

    filtro = construir_filtro_inicial(pregunta, nombre_doc)

    print("\n🧪 FILTRO FINAL:", filtro)

    docs = find_docs(filtro, scan=scan) or []

    if len(docs) > 300:
        docs = docs[:300]

    print("📦 DOCS ENCONTRADOS:", len(docs))

    # --------------------------------------------------
    # 🔥 FALLBACK CORRECTO
    # --------------------------------------------------

    if len(docs) < 5 and nombre_doc_norm:

        print("⚠️ fallback inteligente")

        docs = find_docs(
            {
                "metadata.documento_norm": {
                    "$regex": nombre_doc_norm[:6],  # 🔥 parcial robusto
                    "$options": "i"
                }
            },
            scan=200
        ) or []

        docs = docs[:150]

    if not docs:
        return "NO_CONTEXT"

    # --------------------------------------------------
    # 🔥 LIMPIEZA
    # --------------------------------------------------

    docs_limpios = []

    for d in docs:

        cont = d.get("contenido_norm") or ""

        if not isinstance(cont, str):
            cont = str(cont)

        if len(cont) < 50:
            continue

        cont_norm = normalizar(cont)

        if any(x in cont_norm for x in ["anexo", "tabla", "bibliografia"]):
            continue

        d["contenido_norm"] = cont_norm
        docs_limpios.append(d)

    docs = docs_limpios

    if not docs:
        return "NO_CONTEXT"

    # --------------------------------------------------
    # 🔥 PRE-SCORING AVANZADO
    # --------------------------------------------------

    frases = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta_norm)

    for d in docs:

        meta = d.get("metadata") or {}
        cont = d["contenido_norm"]

        score = 0

        # 🔥 match tokens (mejorado)
        hits = sum(1 for t in toks if t in cont)
        score += hits * 3

        # 🔥 MATCH FRASE EXACTA (CRÍTICO)
        for f in frases:
            if f in cont:
                score += 25

        # 🔥 tipo chunk
        tipo = meta.get("tipo_chunk")

        if tipo == "resolucion": score += 15
        elif tipo == "objetivo": score += 12
        elif tipo == "postulacion": score += 10
        elif tipo == "requisito": score += 9

        # 🔥 sección
        if seccion and meta.get("seccion") == seccion:
            score += 12

        # 🔥 artículo
        if articulo and meta.get("articulo") == articulo:
            score += 25

        # 🔥 resolutivo
        if meta.get("es_resolutivo"):
            score += 12

        # 🔥 inicio documento
        if meta.get("chunk_index", 999) < 5:
            score += 5

        # 🔥 boost documento correcto
        if nombre_doc_norm and nombre_doc_norm in (meta.get("documento_norm") or ""):
            score += 20

        d["pre_score"] = score

    docs = sorted(docs, key=lambda x: x["pre_score"], reverse=True)[:120]

    # --------------------------------------------------
    # 🔎 FILTRO SECCIÓN SUAVE
    # --------------------------------------------------

    if seccion:
        filtrados = filtrar_posicional(docs, seccion)
        if filtrados:
            docs = filtrados + docs[:40]

    # --------------------------------------------------
    # 🔥 RANKING FINAL
    # --------------------------------------------------

    ranked = rankear_chunks(
        pregunta,
        docs,
        toks,
        modo_cita=modo_cita
    )

    # --------------------------------------------------
    # 🔥 SELECCIÓN FINAL
    # --------------------------------------------------

    resultados = []
    seen = set()

    for r in ranked:

        cont = r.get("contenido_norm")

        if not cont or cont in seen:
            continue

        # 🔥 FILTRO DE CITA MEJORADO
        if modo_cita:
            cont_filtrado = aplicar_filtro_cita(
                pregunta,
                cont,
                nombre_doc is not None
            )
            if cont_filtrado:
                cont = cont_filtrado

        resultados.append(cont.strip())
        seen.add(cont)

        if len(resultados) >= top_k:
            break

    if not resultados:
        resultados = [
            d["contenido_norm"]
            for d in docs[:top_k]
            if d.get("contenido_norm")
        ]

    contexto = "\n\n".join(resultados)

    return contexto[:1800]
