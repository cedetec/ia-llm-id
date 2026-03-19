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
        nombre_doc = nombre_doc.lower().strip()

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
            "$or": [
                {"metadata.documento_norm": nombre_doc},
                {
                    "metadata.documento_norm": {
                        "$regex": nombre_doc,
                        "$options": "i"
                    }
                }
            ]
        }

    # --------------------------------------------------
    # Buscar documentos
    # --------------------------------------------------

    docs = find_docs(filtro, scan=scan)

    print("TIPOS:", [
        (d.get("metadata") or {}).get("tipo_chunk")
        for d in docs[:10]
    ])
    print("TOP PRE_SCORE:", [
        (
            (d.get("metadata") or {}).get("tipo_chunk"),
            d.get("pre_score")
        )
        for d in docs[:10]
    ])
    print("PRIMEROS DOCS:", [
        (d.get("metadata") or {}).get("documento_norm")
        for d in docs[:10]
    ])

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
        "resuelve", "resolucion", "aprueba", "otorga",
        "cita", "frase", "extrae", "texto"
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
            d["pre_score"] += 25

        elif tipo == "resolucion":

            cont = d.get("contenido_norm") or normalizar(
                d.get("contenido") or ""
            )

            # 🔥 RESOLUTIVO REAL (TOP PRIORIDAD)
            if re.search(r'\bresuelv[eo]\b', cont):
                d["pre_score"] += 80

            elif re.search(r'aprueb[a-z]*.*bases', cont):
                d["pre_score"] += 70

            elif re.search(r'aprueb', cont):
                d["pre_score"] += 50

            # encabezado (menos importante)
            elif re.search(r'resolucion|res\.', cont):
                d["pre_score"] += 20

            else:
                d["pre_score"] -= 5  # 🔥 castigar basura tipo VISTOS

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

        if busca_resolucion and tipo not in ["resolucion", "articulo_resolucion"]:
            d["pre_score"] -= 8

        if busca_considerando and tipo == "considerando":
            d["pre_score"] += 5

        if busca_objetivo and tipo in ["bases_concurso", "definicion"]:
            d["pre_score"] += 12

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

    if nombre_doc:
        docs = [
            d for d in docs
            if (d.get("metadata") or {}).get("documento_norm", "") == nombre_doc
        ]

    # --------------------------------------------------
    # PRE-SCORE PARA RANKING
    # --------------------------------------------------

    for d in docs:

        base = d.get("lex_boost", 0)

        base += d.get("token_boost", 0)

        base += d.get("proximity_boost", 0)

        d["pre_score"] += min(base, 15)

    # 🔥 CASTIGO A TEXTO GENÉRICO LARGO (CLAVE)
    for d in docs:

        cont = d.get("contenido_norm") or normalizar(
            d.get("contenido") or ""
        )

        # textos largos sin señal resolutiva → basura típica
        if len(cont.split()) > 80 and not re.search(r'resuelv|aprueb', cont):
            d["pre_score"] -= 15

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

        cont = d.get("contenido_norm") or normalizar(
            d.get("contenido") or ""
        )

        if re.search(r'\bresuelv[eo]\b', cont):
            d["pre_score"] += 100

    # --------------------------------------------------
    # BOOST SI LA PREGUNTA ES DE UN DOCUMENTO ESPECÍFICO
    # --------------------------------------------------

    if nombre_doc:

        for d in docs:

            meta_doc = (d.get("metadata") or {}).get("documento_norm", "")

            if nombre_doc == meta_doc:
                d["pre_score"] += 8

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

    # 🔥 PENALIZAR TEXTO GENÉRICO LEGAL (VISTOS, MARCO, ETC)
    for d in docs:

        cont = d.get("contenido_norm", "")

        if re.search(r'\bvisto[s]?\b|\bconsiderando\b', cont):
            d["pre_score"] -= 10

        if "marco normativo" in cont:
            d["pre_score"] -= 8

    # --------------------------------------------------
    # 🔥 FILTRO DIRECTO PARA CITAS (ULTRA CLAVE)
    # --------------------------------------------------

    if modo_cita:

        docs_filtrados = []

        for d in docs:

            cont = d.get("contenido_norm") or ""

            # 🔥 SOLO FRASES QUE PUEDEN SER CITADAS
            if re.search(r'resuelv|aprueb|resolucion|res\.|\d{1,2}/\d{1,2}/\d{4}', cont):
                docs_filtrados.append(d)

        if len(docs_filtrados) >= 3:
            docs = docs_filtrados

    docs = sorted(
        docs,
        key=lambda d: d.get("pre_score", 0),
        reverse=True
    )[:120]

    for d in docs:

        tipo = (d.get("metadata") or {}).get("tipo_chunk")

        if tipo == "articulo_resolucion":
            d["pre_score"] *= 1.15

        elif tipo == "resolucion":
            d["pre_score"] *= 1.08

    for d in docs:
        d["score_total"] = d.get("pre_score", 0)

    # 🔥 FILTRO REAL POR INTENCIÓN (ARREGLADO)
    if busca_resolucion:

        docs_res = []

        for d in docs:

            meta = d.get("metadata") or {}
            cont = d.get("contenido_norm", "")

            if meta.get("es_resolutivo"):
                docs_res.append(d)
                continue

            if re.search(r'resolucion|res\.|resuelv|aprueb', cont):
                docs_res.append(d)

        if len(docs_res) >= 3:
            docs = docs_res

    # --------------------------------------------------
    # 🔥 DEBUG FINAL (CRÍTICO)
    # --------------------------------------------------

    print("\n🔥 DEBUG RESOLUTIVOS:")
    for d in docs[:20]:
        cont = (d.get("contenido") or "")[:120]
        print(
            "RESUELVO" in cont.upper(),
            "| score:", d.get("pre_score"),
            "|", cont
        )

    print("\nCANDIDATOS FINALES:")
    for d in docs[:10]:
        print(d.get("contenido")[:200])
        print("score:", d.get("pre_score"))
        print("----")

    # --------------------------------------------------
    # Ranking híbrido
    # --------------------------------------------------

    # 🔥 USAR DIRECTAMENTE docs (NO romper pre_score)
    ranked = docs

    # 🔥 asegurar que el mejor no se pierda
    if docs:
        best_doc = max(docs, key=lambda x: x.get("pre_score", 0))
        if best_doc not in ranked:
            ranked.insert(0, best_doc)

    # 🔥 ORDEN FINAL REAL (EL MÁS IMPORTANTE)
    ranked = sorted(
        ranked,
        key=lambda x: x.get("pre_score", 0),
        reverse=True
    )

    # 🔥 FILTRO FINAL SEMÁNTICO (ULTRA IMPORTANTE)
    if modo_cita:

        ranked_filtrado = []

        for r in ranked:

            cont = normalizar(r.get("contenido", ""))

            if re.search(r'resuelv|aprueb|resolucion|objetivo|postul', cont):
                ranked_filtrado.append(r)

        if len(ranked_filtrado) >= 2:
            ranked = ranked_filtrado

    # 🔥 HARD FILTER FINAL (AJUSTADO)
    ranked = [
        r for r in ranked
        if r.get("pre_score", 0) > 5
    ]

    # 🔥 fallback seguro
    if not ranked:
        ranked = docs[:10] if docs else []

    print("\nTOP RANKED FINAL:")
    for r in ranked[:5]:
        print(r.get("contenido")[:150])
        print("pre_score:", r.get("pre_score"))
        print("----")

    if not isinstance(ranked, list):
        ranked = []

    # 🔥 SI ES CITA → USAR DIRECTAMENTE EL MEJOR CHUNK
    if modo_cita and ranked:

        for r in ranked:

            cont = r.get("contenido") or ""
            cont_norm = normalizar(cont)

            if re.search(r'aprueb.*bases|resuelv', cont_norm):
                return cont[:400]

        # fallback
        best = ranked[0]
        cont = best.get("contenido")

        if cont:
            return cont[:400]

    # --------------------------------------------------
    # Selección principal
    # --------------------------------------------------

    resultados = []
    seen = set()

    for item in ranked:

        if not isinstance(item, dict):
            continue

        cont = item.get("contenido")

        if not isinstance(cont, str):
            cont = str(cont or "")

        meta = item.get("metadata")
        score = item.get("pre_score", 0)

        if not cont:
            continue

        if cont in seen:
            continue

        if modo_cita:

            cont_filtrado = aplicar_filtro_cita(
                pregunta,
                cont,
                modo_documento_fijado
            )

            if not isinstance(cont_filtrado, str):
                cont_filtrado = str(cont_filtrado or "")

            # 🔥 DESCARTAR SI NO SIRVE
            if not cont_filtrado or len(cont_filtrado.split()) < 5:
                continue

            cont = cont_filtrado

            # 🔥 FILTRO DURO FINAL
            cont_norm = normalizar(cont)

            if not re.search(r'resuelv|aprueb|resolucion|res\.|\d{1,2}/\d{1,2}/\d{4}', cont_norm):
                continue

        cont = cont.strip()

        resultados.append({
            "contenido": cont,
            "metadata": meta,
            "score": score,
        })

        seen.add(cont)

        if len(resultados) >= min(top_k, 40):
            break

    # --------------------------------------------------
    # Fallback robusto
    # --------------------------------------------------

    if not resultados:

        # ordenar primero (preliminar)
        docs = sorted(
            docs,
            key=lambda d: d.get("pre_score", 0),
            reverse=True
        )[:120]

        # aplicar ajustes finales
        for d in docs:
            tipo = (d.get("metadata") or {}).get("tipo_chunk")

            if tipo == "articulo_resolucion":
                d["pre_score"] *= 1.15
            elif tipo == "resolucion":
                d["pre_score"] *= 1.08

        # 🔥 REORDENAR OTRA VEZ (CLAVE)
        docs = sorted(
            docs,
            key=lambda d: d.get("pre_score", 0),
            reverse=True
        )

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
