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

MAPA_ARTICULOS = {
    "primero": 1,
    "segundo": 2,
    "tercero": 3,
    "cuarto": 4,
    "quinto": 5,
    "sexto": 6,
    "septimo": 7,
    "séptimo": 7,
    "octavo": 8,
    "noveno": 9,
    "decimo": 10,
    "décimo": 10
}

def detectar_articulo(pregunta: str):

    p = pregunta.lower()

    m_num = re.search(r'art[ií]culo\s+(\d+)', p)
    if m_num:
        return int(m_num.group(1))

    m_txt = re.search(
        r'art[ií]culo\s+(primero|segundo|tercero|cuarto|quinto|sexto|septimo|séptimo|octavo|noveno|decimo|décimo)',
        p
    )

    if m_txt:
        return MAPA_ARTICULOS.get(m_txt.group(1))

    return None

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

    articulo_objetivo = detectar_articulo(pregunta)

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

    # --------------------------------------------------
    # NORMALIZAR CONTENIDO (🔥 IMPORTANTE)
    # --------------------------------------------------

    for d in docs:
        d["contenido_norm"] = normalizar(
            d.get("contenido") or d.get("texto_extraido") or ""
        )

    # --------------------------------------------------
    # Filtrar anexos irrelevantes (MEJORADO 🔥)
    # --------------------------------------------------

    docs_filtrados = []

    for d in docs:

        meta = d.get("metadata") or {}
        seccion = (meta.get("seccion") or "").lower()

        if any(x in seccion for x in ["anexo", "tabla", "referencias", "bibliografia"]):
            continue

        docs_filtrados.append(d)

    docs = docs_filtrados

    if nombre_doc:

        docs = sorted(
            docs,
            key=lambda d: nombre_doc in normalizar(
                (d.get("metadata") or {}).get("documento", "")
            ),
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

            if coincidencias >= max(2, len(toks) // 2):
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
    # Inicializar pre_score
    # --------------------------------------------------

    for d in docs:
        d["pre_score"] = 0

    # --------------------------------------------------
    # BOOST SI COINCIDE CON SECCION SOLICITADA
    # --------------------------------------------------

    if seccion:

        for d in docs:

            meta = d.get("metadata") or {}

            sec = meta.get("seccion")

            if not sec:
                continue

            if seccion.lower() in sec.lower():
                d["pre_score"] += 6
            elif sec.lower() in seccion.lower():
                d["pre_score"] += 4

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

        cont = d.get("contenido_norm", "")

        hits = [t for t in toks if len(t) > 3 and t in cont]

        if len(hits) >= 4:
            d["token_boost"] = 8
        elif len(hits) == 3:
            d["token_boost"] = 6
        elif len(hits) == 2:
            d["token_boost"] = 3
        else:
            d["token_boost"] = 0


    # --------------------------------------------------
    # BOOST POR PROXIMIDAD DE TOKENS
    # --------------------------------------------------

    for d in docs:

        cont = d.get("contenido_norm", "")

        posiciones = []

        for t in toks:
            if len(t) > 3:
                idx = cont.find(t)
                if idx != -1:
                    posiciones.append(idx)

        if len(posiciones) >= 2:

            span = max(posiciones) - min(posiciones)

            if span < 80:
                d["proximity_boost"] = 4
            elif span < 160:
                d["proximity_boost"] = 2
            else:
                d["proximity_boost"] = 0

        else:
            d["proximity_boost"] = 0

    # --------------------------------------------------
    # BOOST POR DENSIDAD DE TOKENS
    # --------------------------------------------------

    for d in docs:

        cont = d.get("contenido_norm", "")

        palabras = cont.split()

        if not palabras:
            continue

        hits = sum(1 for t in toks if len(t) > 3 and t in cont)

        densidad = hits / len(palabras)

        if densidad > 0.05:
            d["pre_score"] += 6

        elif densidad > 0.02:
            d["pre_score"] += 3

    # --------------------------------------------------
    # BOOST POR ARTICULO JURIDICO
    # --------------------------------------------------

    if articulo_objetivo:

        for d in docs:

            meta = d.get("metadata") or {}

            art = meta.get("articulo")

            if not art:
                continue

            m = re.search(r'(\d+)', str(art))

            if not m:
                continue

            art_num = int(m.group(1))

            if art_num == articulo_objetivo:
                d["pre_score"] += 20

            elif abs(art_num - articulo_objetivo) == 1:
                d["pre_score"] += 6

    # --------------------------------------------------
    # INTENCIÓN JURÍDICA DE LA PREGUNTA
    # --------------------------------------------------

    pregunta_norm = normalizar(pregunta)

    busca_resolucion = any(x in pregunta_norm for x in [
        "resuelve", "resolucion", "aprueba", "otorga"
    ])

    busca_considerando = any(x in pregunta_norm for x in [
        "considerando", "fundamento", "motivo"
    ])

    busca_objetivo = any(x in pregunta_norm for x in [
        "objetivo", "finalidad", "proposito"
    ])

    # --------------------------------------------------
    # BOOST POR TIPO DE CHUNK JURIDICO
    # --------------------------------------------------

    for d in docs:

        meta = d.get("metadata") or {}
        tipo = meta.get("tipo_chunk", "")

        # 🔥 prioridad máxima → lo que realmente responde
        if tipo == "articulo_resolucion":
            d["pre_score"] += 12

        elif tipo == "resolucion":
            d["pre_score"] += 8

        elif tipo == "considerando":
            d["pre_score"] += 3

        elif tipo == "bases_concurso":
            d["pre_score"] += 3

        elif tipo == "definicion":
            d["pre_score"] += 2

    # --------------------------------------------------
    # BOOST POR INTENCIÓN JURÍDICA
    # --------------------------------------------------

    for d in docs:

        tipo = (d.get("metadata") or {}).get("tipo_chunk", "")

        if busca_resolucion and tipo in ["resolucion", "articulo_resolucion"]:
            d["pre_score"] += 6

        if busca_considerando and tipo == "considerando":
            d["pre_score"] += 5

        if busca_objetivo and tipo in ["bases_concurso", "definicion"]:
            d["pre_score"] += 4

    # --------------------------------------------------
    # BOOST POR TITULO DE SECCION
    # --------------------------------------------------

    for d in docs:

        meta = d.get("metadata") or {}

        titulo = normalizar(meta.get("titulo", ""))

        if not titulo:
            continue

        for t in toks:
            if len(t) > 4 and t in titulo:
                d["pre_score"] += 4

    # --------------------------------------------------
    # PENALIZAR TEXTO RUIDOSO (OCR BASURA)
    # --------------------------------------------------

    for d in docs:

        cont = d.get("contenido_norm", "")

        # patrones típicos de OCR malo
        if re.search(r'(tabla\s+\d+|figura\s+\d+|anexo|bibliografia)', cont):
            d["pre_score"] -= 6

        # exceso de números → probablemente tabla
        if sum(c.isdigit() for c in cont) > 50:
            d["pre_score"] -= 4

    # --------------------------------------------------
    # PRE-SCORE PARA RANKING
    # --------------------------------------------------

    for d in docs:

        base = d.get("lex_boost", 0)

        base += d.get("token_boost", 0)

        base += d.get("proximity_boost", 0)

        d["pre_score"] += min(base, 15)

    # --------------------------------------------------
    # 🔥 BOOST POR POSICIÓN EN DOCUMENTO (NUEVO)
    # --------------------------------------------------

    for d in docs:

        idx = (d.get("metadata") or {}).get("chunk_index", 0)

        if idx < 5:
            d["pre_score"] += 3   # inicio documento

        elif idx > 50:
            d["pre_score"] -= 1   # muy profundo

    # --------------------------------------------------
    # 🔥 BOOST POR LONGITUD ÓPTIMA (NUEVO)
    # --------------------------------------------------

    for d in docs:

        length = len((d.get("contenido") or "").split())

        if 80 <= length <= 250:
            d["pre_score"] += 3

        elif length < 40:
            d["pre_score"] -= 2

    # --------------------------------------------------
    # BOOST SI EL TEXTO CONTIENE "RESUELVO"
    # --------------------------------------------------

    for d in docs:

        cont = d.get("contenido_norm", "")

        if re.search(r'\bresuelv[eo]\b', cont):
            d["pre_score"] += 3

    # --------------------------------------------------
    # BOOST SI LA PREGUNTA ES DE UN DOCUMENTO ESPECÍFICO
    # --------------------------------------------------

    if nombre_doc:

        for d in docs:

            meta_doc = normalizar(
                (d.get("metadata") or {}).get("documento", "")
            )

            if nombre_doc in meta_doc:
                d["pre_score"] += 6

    # --------------------------------------------------
    # BOOST SI LA PREGUNTA PIDE UNA PALABRA O FRASE EXACTA
    # --------------------------------------------------

    m = re.search(r'["“](.+?)["”]', pregunta)

    if m:

        palabra_objetivo = normalizar(m.group(1))

        for d in docs:

            cont = d.get("contenido_norm", "")

            if palabra_objetivo and palabra_objetivo in cont:
                d["pre_score"] += 8

    docs = sorted(
        docs,
        key=lambda d: d.get("pre_score", 0),
        reverse=True
    )[:800]

    for d in docs:

        tipo = (d.get("metadata") or {}).get("tipo_chunk")

        if tipo == "articulo_resolucion":
            d["pre_score"] *= 1.15

        elif tipo == "resolucion":
            d["pre_score"] *= 1.08

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
