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


def obtener_contexto(
    pregunta: str,
    *,
    tipo_busqueda: str | None = None,
    modo_cita: bool = False,
    filtro_doc: str | None = None,
    top_k: int = 18,
    scan: int = 6000,
):

    # --------------------------------------------------
    # Detectar documento desde la pregunta
    # --------------------------------------------------

    nombre_doc = filtro_doc or extraer_nombre_documento(pregunta)

    if nombre_doc:
        nombre_doc = normalizar(nombre_doc)

    modo_documento_fijado = nombre_doc is not None

    if modo_documento_fijado:
        scan = max(scan, 6000)

    # --------------------------------------------------
    # Detectar modo cita automáticamente
    # --------------------------------------------------

    if detectar_modo_cita(pregunta):
        modo_cita = True

    if modo_cita:
        scan = max(scan, 2500)
        top_k = max(top_k, 10)

    # --------------------------------------------------
    # Detectar sección jurídica
    # --------------------------------------------------

    seccion = detectar_seccion_simple(pregunta)

    # --------------------------------------------------
    # Construir filtro Mongo
    # --------------------------------------------------

    filtro = construir_filtro_inicial(pregunta, nombre_doc)

    # reforzar filtro por documento si se detectó uno
    if nombre_doc:
        filtro = {
            "$and": [
                filtro,
                {
                    "$or": [
                        {
                            "metadata.documento": {
                                "$regex": nombre_doc,
                                "$options": "i"
                            }
                        },
                        {
                            "metadata.documento_norm": {
                                "$regex": nombre_doc,
                                "$options": "i"
                            }
                        }
                    ]
                }
            ]
        }

    # --------------------------------------------------
    # Buscar documentos
    # --------------------------------------------------

    docs = find_docs(filtro, scan=scan)

    # ----------------------------------
    # Prefiltro por tokens
    # ----------------------------------

    toks = tokens(pregunta) or []

    if toks:

        docs_token = []

        for d in docs:

            texto = (d.get("contenido") or d.get("texto_extraido") or "").lower()

            coincidencias = sum(1 for t in toks if t in texto)

            if coincidencias >= 1 or len(texto) > 400:
                docs_token.append(d)

        # usar solo si no reduce demasiado
        if len(docs_token) > 30:
            docs = docs_token

    docs = [
        d for d in docs
        if d.get("contenido") or d.get("texto_extraido")
    ]

    # --------------------------------------------------
    # fallback: buscar solo por documento
    # --------------------------------------------------

    if not docs and nombre_doc:

        docs = find_docs(
            {
                "metadata.documento": {
                    "$regex": nombre_doc,
                    "$options": "i"
                }
            },
            scan=scan
        )

        docs = [d for d in docs if d.get("contenido")]

    if not docs:
        return ""

    # --------------------------------------------------
    # Filtrar por sección SOLO si mantiene suficientes candidatos
    # --------------------------------------------------

    if seccion:

        docs_filtrados = filtrar_posicional(docs, seccion)

        # usar filtro solo si no elimina demasiado
        if docs_filtrados and len(docs_filtrados) > 3:
            docs = docs_filtrados

    # --------------------------------------------------
    # Tokenizar pregunta
    # --------------------------------------------------

    toks = tokens(pregunta) or []

    if len(toks) < 2:
        toks = [
            t for t in pregunta.lower().split()
            if len(t) > 3
        ]

    # ----------------------------------
    # Boost léxico simple
    # ----------------------------------

    for d in docs:

        cont = (d.get("contenido") or d.get("texto_extraido", "")).lower()

        lex_score = sum(
            1 for t in toks
            if len(t) > 3 and t in cont
        )

        d["lex_boost"] = lex_score

    # --------------------------------------------------
    # Ranking híbrido
    # --------------------------------------------------

    ranked = rankear_chunks(
        pregunta,
        docs,
        toks,
        modo_cita=modo_cita
    )

    resultados = []
    seen = set()

    # --------------------------------------------------
    # Selección principal
    # --------------------------------------------------

    for item in ranked:

        if not isinstance(item, dict):
            continue

        cont = item.get("contenido")
        meta = item.get("metadata")
        score = item.get("score", 0)

        if not cont:
            continue

        if cont in seen:
            continue

        if modo_cita:

            cont = aplicar_filtro_cita(
                pregunta,
                cont,
                modo_documento_fijado
            )

            if not cont:
                continue

        cont = cont.strip()
        resultados.append(cont)
        seen.add(cont)

        if len(resultados) >= top_k:
            break

    # --------------------------------------------------
    # Fallback robusto
    # --------------------------------------------------

    if not resultados:

        docs_sorted = sorted(
            docs,
            key=lambda d: len(d.get("contenido") or d.get("texto_extraido", "")),
            reverse=True
        )

        for d in docs_sorted:

            cont = d.get("contenido") or d.get("texto_extraido")

            if not cont:
                continue

            if len(cont) < 80:
                continue

            if cont in seen:
                continue

            resultados.append(cont)
            seen.add(cont)

            if len(resultados) >= top_k:
                break

    # --------------------------------------------------
    # Construir contexto final
    # --------------------------------------------------

    contexto = "\n\n".join(
        r.strip()
        for r in resultados
        if r and len(r.strip()) > 30
    )

    MAX_CONTEXT = 4500

    return contexto[:MAX_CONTEXT]
