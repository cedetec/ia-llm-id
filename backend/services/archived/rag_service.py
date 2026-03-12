# rag_service.py
import re
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from backend.services.retrieval_scoring import score_chunk
from backend.services.retrieval_text_utils import tokens, normalizar

# -----------------------------
# CONFIGURACIÓN
# -----------------------------

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "asistente"
COLLECTION = "indexados"

_DOC_CACHE = None
_client = None
_model = None


# -----------------------------
# CONEXIONES
# -----------------------------

def _get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[DB_NAME][COLLECTION]


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model

def coverage_score(tokens_query, texto):

    t = texto.lower()

    hits = 0

    for tok in tokens_query:
        if tok in t:
            hits += 1

    if not tokens_query:
        return 0

    return (hits / len(tokens_query)) * 100

def density_score(tokens_query, texto):

    t = texto.lower()

    posiciones = []

    for tok in tokens_query:

        idx = t.find(tok)

        if idx != -1:
            posiciones.append(idx)

    if len(posiciones) < 2:
        return 0

    span = max(posiciones) - min(posiciones)

    if span <= 0:
        return 0

    return max(0, 50 - span / 20)

def ruido_penalty(texto):

    ruido = [
        "www.",
        "http",
        "ministerio",
        "página",
        "pagina",
        "anid.cl"
    ]

    t = texto.lower()

    penalty = 0

    for r in ruido:
        if r in t:
            penalty += 5

    return penalty

def detectar_seccion_en_texto(texto):

    texto = texto.lower()

    if "objetivo del concurso" in texto:
        return "objetivo"

    if "requisitos de postulacion" in texto:
        return "requisitos"

    if "pueden postular" in texto:
        return "postulacion"

    return None

# -----------------------------
# UTILIDADES
# -----------------------------

def enriquecer_query_legal(pregunta: str) -> str:

    p = pregunta.lower()

    if any(k in p for k in ["resolución", "resuelve", "aprueba"]):
        prefijo = "resolucion administrativa chile acto administrativo resuelvo "
    elif any(k in p for k in ["objetivo", "requisitos", "postular"]):
        prefijo = "bases concurso investigacion objetivo general requisitos postulacion beneficiarios "
    else:
        prefijo = "documento administrativo chile "

    return prefijo + pregunta


def normalizar_nombre(nombre: str):
    nombre = nombre.lower()
    nombre = nombre.replace(".pdf", "")
    nombre = nombre.replace("_", "")
    nombre = nombre.replace(" ", "")
    return nombre


def detectar_documento(pregunta: str):

    collection = _get_collection()

    candidatos = re.findall(
        r'[a-z0-9_\-]{3,}\.pdf',
        pregunta.lower()
    )

    if not candidatos:
        return None

    global _DOC_CACHE

    if _DOC_CACHE is None:
        docs = collection.distinct("metadata.documento_norm")
        _DOC_CACHE = {normalizar_nombre(d): d for d in docs}

    for candidato in candidatos:

        norm = normalizar_nombre(candidato)

        if norm in _DOC_CACHE:
            return _DOC_CACHE[norm]

    return None


def es_pregunta_resolutiva(pregunta: str):

    palabras = [
        "aprueba",
        "apruebase",
        "apruébase",
        "resuelve",
        "resolución",
        "decreto",
        "autoriza",
        "adjudica"
    ]

    p = pregunta.lower()

    return any(k in p for k in palabras)


def es_consulta_cita(pregunta: str):

    claves = [
        "cita",
        "frase textual",
        "textualmente",
        "extrae",
        "donde aparezca",
        "menciona literalmente",
        "frase",
        "literal",
        "exacta",
    ]

    p = pregunta.lower()

    return any(k in p for k in claves)


def extraer_palabra_clave(pregunta: str):

    m = re.search(r'"([^"]+)"', pregunta)

    if m:
        return m.group(1)

    return None

def detectar_seccion(pregunta: str):

    p = pregunta.lower()

    if any(k in p for k in ["objetivo", "propósito", "finalidad"]):
        return "objetivo"

    if any(k in p for k in ["requisito", "requisitos"]):
        return "requisitos"

    if any(k in p for k in ["postular", "postulación", "postulacion"]):
        return "postulacion"

    if any(k in p for k in ["beneficiario", "beneficiarios"]):
        return "beneficiarios"

    if any(k in p for k in ["financiamiento", "financiar", "monto", "recursos"]):
        return "financiamiento"

    if any(k in p for k in ["evaluacion", "evaluación", "criterio"]):
        return "evaluacion"

    if any(k in p for k in ["objetivo del concurso", "objetivo general"]):
        return "objetivo"

    return None

# -----------------------------
# BÚSQUEDA LÉXICA
# -----------------------------

def busqueda_lexica(pregunta: str, documento: str | None):

    collection = _get_collection()

    palabra = extraer_palabra_clave(pregunta)

    filtro = {}

    if documento:
        doc_norm = normalizar_nombre(documento)
        filtro["metadata.documento_norm"] = doc_norm

    patrones = [

        r"resoluci[oó]n",
        r"\bres\s*\.?",
        r"apru[eé]b",
        r"apruebase",
        r"apruebanse",
        r"resuelv",

        r"objetivo",
        r"objetivo\s+general",
        r"objetivo\s+del\s+concurso",
        r"objetivo\s+del\s+presente\s+concurso",

        r"requisitos?",
        r"requisitos?\s+de\s+postulaci[oó]n",

        r"postulaci[oó]n",
        r"podr[aá]n\s+postular",
        r"pueden\s+postular",

        r"beneficiarios?",
        r"financiamiento",
        r"investigaci[oó]n",
        r"fondecyt",
        r"concurso"
        ]

    if palabra:
        regex_total = rf"{re.escape(palabra)}|{re.escape(palabra).replace('e','[eé]')}"
    else:
        regex_total = "|".join(patrones)

    query = {
        **filtro,
        "contenido": {
            "$regex": regex_total,
            "$options": "i"
        }
    }

    hits = collection.find(
        query,
        {"contenido": 1, "metadata": 1}
    ).limit(300)

    return list(hits)


# -----------------------------
# BÚSQUEDA VECTORIAL
# -----------------------------

def busqueda_vectorial(pregunta: str, documento: str | None):

    collection = _get_collection()
    model = _get_model()

    query = enriquecer_query_legal(pregunta)

    embedding = model.encode(
        f"query: {query}",
        normalize_embeddings=True
    ).tolist()

    seccion = detectar_seccion(pregunta)

    vector_filter = {}

    if documento:
        doc_norm = normalizar_nombre(documento)
        vector_filter["metadata.documento_norm"] = doc_norm

    if seccion:
        vector_filter["metadata.seccion"] = seccion

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 800,
                "limit": 200,
                "filter": vector_filter
            }
        }
    ]

    if seccion:
        vector_filter["metadata.seccion"] = {
            "$regex": seccion,
            "$options": "i"
        }

    pipeline.append({
        "$project": {
            "contenido": 1,
            "metadata": 1,
            "score": {"$meta": "vectorSearchScore"}
        }
    })

    vector_results = list(collection.aggregate(pipeline))

    doc_filter = normalizar_nombre(documento) if documento else None

    scored = []

    tokens_query = tokens(normalizar(pregunta))
    tokens_query = [t for t in tokens_query if len(t) > 2]

    if not tokens_query:
        tokens_query = tokens(normalizar(pregunta))

    tokens_query = tokens_query[:20]

    tokens_query = [
        t for t in tokens_query
        if not t.isdigit()
        and t not in ["pdf","rex"]
    ]

    pregunta_l = pregunta.lower()

    quoted = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta.lower())

    for c in vector_results:

        final_score = 0

        meta = c.get("metadata", {})
        doc_name = (meta.get("documento_norm") or meta.get("documento") or "").lower()
        seccion_doc = str(meta.get("seccion", "")).lower()

        if doc_filter and normalizar_nombre(doc_name) == doc_filter:
            final_score += 120

        contenido = c.get("contenido") or ""

        # limpiar espacios que rompen palabras
        contenido = re.sub(
            r'\b([A-ZÁÉÍÓÚÑ])\s+([A-ZÁÉÍÓÚÑ])\s+([A-ZÁÉÍÓÚÑ])',
            lambda m: m.group(0).replace(" ", ""),
            contenido
        )
        
        contenido = re.sub(
            r'R\s*E\s*S\s*O\s*L\s*U\s*C\s*I\s*O\s*N',
            'RESOLUCION',
            contenido,
            flags=re.I
        )
        
        # eliminar chunks demasiado cortos o demasiado largos
        if len(contenido) < 40 or len(contenido) > 5000:
            continue

        contenido_norm = normalizar(contenido)

        contenido_tokens = set(tokens(contenido_norm))

        try:
            
            modo_cita = (
                '"' in pregunta
                or "cita" in pregunta_l
                or "frase textual" in pregunta_l
                or "literal" in pregunta_l
                or "extrae" in pregunta_l
            )

            score_lex = score_chunk(contenido_norm, tokens_query, modo_cita=modo_cita)

            # proteger si algún día devuelve lista
            if isinstance(score_lex, (list, tuple)):
                score_lex = sum(score_lex)

            score_lex = float(score_lex)

        except Exception:
            score_lex = 0.0

        vector_score = float(c.get("score") or 0) * 100

        coverage = sum(1 for t in tokens_query if t in contenido_tokens) / max(len(tokens_query),1) * 100

        density = density_score(tokens_query, contenido_norm)

        noise = ruido_penalty(contenido)

        # penalizar chunks muy largos
        if len(contenido) > 2500:
            noise += 5

        final_score = (
            score_lex * 0.40 +
            vector_score * 0.45 +
            coverage * 0.25 +
            density * 0.05
        )

        final_score -= noise

        if "resuelvo" in contenido_norm:
            final_score += 40

        if "apruebase" in contenido_norm or "apruebanse" in contenido_norm:
            final_score += 40

        if "bases del concurso" in contenido_norm:
            final_score += 35

        for q in quoted:

            qn = normalizar(q)

            if qn in contenido_norm:
                final_score += 260

            # coincidencia parcial fuerte
            if any(w in contenido_norm for w in qn.split()):
                final_score += 90

        if all(t in contenido_norm for t in tokens_query[:3]):
            final_score += 120

        # ---------------------------------
        # BOOST FUERTE POR SECCIÓN
        # ---------------------------------

        if seccion:

            if seccion_doc == seccion:
                final_score += 140

            elif seccion in seccion_doc:
                final_score += 90

            if seccion and seccion in contenido_norm:
                final_score += 80

        # fallback por tokens

        if any(t.startswith("objetiv") for t in tokens_query) and "objetivo" in seccion_doc:
            final_score += 60

        if any(t.startswith("requisit") for t in tokens_query) and "requisito" in seccion_doc:
            final_score += 60

        if any(t.startswith("postul") for t in tokens_query) and "postul" in seccion_doc:
            final_score += 60

        # guardar score final
        c["rerank_score"] = final_score

        scored.append(c)

    scored.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return scored[:60]


# -----------------------------
# EXTRACCIÓN DE FRASES
# -----------------------------

def extraer_frase(texto: str, palabra: str | None = None):

    if not texto:
        return None

    # arreglar palabras separadas por OCR (ej: p l a z o)
    texto = re.sub(
        r'\b(?:[a-zA-ZáéíóúÁÉÍÓÚñÑ]\s+){2,}[a-zA-ZáéíóúÁÉÍÓÚñÑ]\b',
        lambda m: m.group(0).replace(" ", ""),
        texto
    )

    # limpiar espacios
    texto = re.sub(r'\s+', ' ', texto)

    frases = re.split(
        r'(?<=[\.\:\;])\s+|\n{2,}',
        texto
    )

    # --------------------------------------------------
    # PRIORIDAD: detectar sección indexada
    # --------------------------------------------------

    m = re.search(r"SECCION:\s*([^\n]+)", texto, re.I)

    if m:

        seccion = m.group(1).strip().lower()

        # extraer contenido de la sección
        cuerpo = texto.split("\n", 1)[-1]

        if "objetivo" in seccion:
            frase = re.search(r"objetivo[^\.]{40,400}", cuerpo, re.I)
            if frase:
                return frase.group(0).strip()[:900]

        if "requisito" in seccion:
            frase = re.search(r"requisit[^\.]{40,400}", cuerpo, re.I)
            if frase:
                return frase.group(0).strip()[:900]

        if "postul" in seccion:
            frase = re.search(r"postul[^\.]{40,400}", cuerpo, re.I)
            if frase:
                return frase.group(0).strip()[:900]

    # --------------------------------------------------
    # 1️⃣ prioridad absoluta: palabra solicitada
    # --------------------------------------------------

    if palabra:

        palabra_norm = normalizar(palabra)

        for f in frases:

            fn = normalizar(f)

            if palabra_norm in fn:
                return f.strip()[:900]

            # fallback parcial
            if palabra_norm[:6] in fn:
                return f.strip()[:900]

    # --------------------------------------------------
    # 2️⃣ detectar encabezados de secciones ANID
    # --------------------------------------------------

    patrones_secciones = [

        r"objetivo\s+del\s+concurso",
        r"objetivo\s+general",
        r"objetivo\s+del\s+presente\s+concurso",

        r"requisitos?\s+de\s+postulaci[oó]n",
        r"requisitos?\s+para\s+postular",

        r"podr[aá]n\s+postular",
        r"pueden\s+postular",

        r"apruebase\s+las\s+bases",
        r"apruebanse\s+las\s+bases",
        r"aprueba\s+las\s+bases",

        r"fondecyt",
        r"concurso",
        r"investigaci[oó]n",
        r"i\s*\+\s*d"
        ]

    for f in frases:

        f_low = f.lower()

        for p in patrones_secciones:

            if re.search(p, f_low):
                return f.strip()[:900]

    # --------------------------------------------------
    # 3️⃣ fallback: frase con más información legal
    # --------------------------------------------------

    mejores = []

    for f in frases:

        score = 0
        f_low = f.lower()

        if "objetivo" in f_low:
            score += 4

        if "concurso" in f_low:
            score += 3

        if "postul" in f_low:
            score += 3

        if "investigacion" in f_low:
            score += 2

        if score > 0:
            mejores.append((score, f))

    if mejores:

        mejores.sort(key=lambda x: x[0], reverse=True)

        return mejores[0][1].strip()[:900]

    return None

# -----------------------------
# FUNCIÓN PRINCIPAL RAG
# -----------------------------

def obtener_contexto(pregunta, documento=None):

    if documento is None:
        documento = detectar_documento(pregunta)

    palabra = extraer_palabra_clave(pregunta)

    # consultas tipo cita
    if es_consulta_cita(pregunta):

        docs = busqueda_lexica(pregunta, documento)

        for d in docs[:40]:

            frase = extraer_frase(
                d.get("contenido", ""),
                palabra
            )

            if frase:

                return {
                    "contexto": frase,
                    "fuente": "RAG (extracción directa)"
                }

        return {
            "contexto": None,
            "fuente": "RAG (sin evidencia)"
        }

    # consultas normales
    docs = busqueda_vectorial(pregunta, documento)

    docs = [d for d in docs if d.get("rerank_score", 0) > 0]

    docs.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    if not docs:

        return {
            "contexto": None,
            "fuente": "RAG (sin evidencia)"
        }

    contextos = []

    docs_por_doc = {}

    for d in docs:
        doc = d.get("metadata", {}).get("documento_norm","")
        docs_por_doc.setdefault(doc, []).append(d)

    seleccion = []
    for doc_chunks in docs_por_doc.values():
        seleccion.extend(doc_chunks[:3])

    docs = seleccion[:30]

    for d in docs:

        t = d.get("contenido","")

        if len(t) > 900:
            t = t[:900]

        contextos.append(t)

    contexto = "\n\n".join(contextos)
    MAX_CONTEXT_CHARS = 4000

    contexto = contexto[:MAX_CONTEXT_CHARS]

    return {
        "contexto": contexto,
        "fuente": "RAG (vectorial)"
    }
