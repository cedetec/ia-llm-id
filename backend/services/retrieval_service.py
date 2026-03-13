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
    top_k: int = 60,
    scan: int = 6000,
):

    # --------------------------------------------------
    # Detectar documento desde la pregunta
    # --------------------------------------------------

    nombre_doc = filtro_doc or extraer_nombre_documento(pregunta)

    if nombre_doc:
        top_k = max(top_k, 80)

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

    docs = sorted(
        docs,
        key=lambda d: len(d.get("contenido") or ""),
        reverse=True
    )

    # ----------------------------------
    # Prefiltro por tokens
    # ----------------------------------

    toks = tokens(pregunta) or []

    if toks:

        docs_token = []

        for d in docs:

            texto = (d.get("contenido") or d.get("texto_extraido") or "").lower()

            coincidencias = sum(1 for t in toks if t in texto)

            if coincidencias >= 1:
                docs_token.append(d)

            # permitir textos largos solo si no hay muchos candidatos
            elif len(docs_token) < 40 and len(texto) > 400:
                docs_token.append(d)

        # usar solo si no reduce demasiado
        if len(docs_token) > 30:
            docs = docs_token

    docs = [
        d for d in docs
        if (
            (d.get("contenido") or d.get("texto_extraido"))
            and len((d.get("contenido") or d.get("texto_extraido"))) < 6000
        )
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
    # BOOST POR COINCIDENCIA FUERTE DE TOKENS
    # --------------------------------------------------

    for d in docs:

        cont = (d.get("contenido") or "").lower()

        hits = [t for t in toks if len(t) > 3 and t in cont]

        if len(hits) >= 3:
            d["token_boost"] = 4
        elif len(hits) == 2:
            d["token_boost"] = 2
        else:
            d["token_boost"] = 0

    # --------------------------------------------------
    # BOOST POR PROXIMIDAD DE TOKENS
    # --------------------------------------------------

    for d in docs:

        cont = (d.get("contenido") or "").lower()

        posiciones = []

        for t in toks:
            if len(t) > 3:
                idx = cont.find(t)
                if idx != -1:
                    posiciones.append(idx)

        if len(posiciones) >= 2:

            span = max(posiciones) - min(posiciones)

            if span < 120:
                d["proximity_boost"] = 3
            elif span < 250:
                d["proximity_boost"] = 1
            else:
                d["proximity_boost"] = 0
        else:
            d["proximity_boost"] = 0

    # --------------------------------------------------
    # PRE-SCORE PARA RANKING
    # --------------------------------------------------

    for d in docs:

        base = d.get("lex_boost", 0)

        base += d.get("token_boost", 0)

        base += d.get("proximity_boost", 0)

        d["pre_score"] = base

    docs = sorted(
        docs,
        key=lambda d: d.get("pre_score", 0),
        reverse=True
    )

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
        resultados.append({
            "contenido": cont,
            "metadata": meta,
            "score": score
        })
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

            resultados.append({
                "contenido": cont,
                "metadata": d.get("metadata", {}),
                "score": 0
            })

            seen.add(cont)

            if len(resultados) >= top_k:
                break

    # --------------------------------------------------
    # Reordenar contexto (Lost in the Middle mitigation)
    # --------------------------------------------------

    if len(resultados) > 4:

        # ordenar por score
        ordenados = sorted(
            resultados,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        # mejores chunks
        top = ordenados[:2]

        # siguientes chunks
        medio = ordenados[2:-2]

        # últimos chunks relevantes
        tail = ordenados[-2:]

        # estrategia: mejores al inicio y final
        resultados = top + medio + tail[::-1]

    # --------------------------------------------------
    # Construir contexto final
    # --------------------------------------------------

    contexto = "\n\n".join(
        r["contenido"].strip()
        for r in resultados
        if r and len(r["contenido"].strip()) > 30
    )

    print("\nTOP CONTEXTO RAG:")
    for r in resultados[:5]:
        print(r["metadata"])
        print(r["contenido"][:200])
        print("score:", r["score"])
        print("----")

    MAX_CONTEXT = 4500

    return contexto[:MAX_CONTEXT]
