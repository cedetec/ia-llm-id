# backend/services/reranker_semantico.py
from sentence_transformers import SentenceTransformer, util
import re
import unicodedata

# modelo semántico (ahora será SOLO apoyo, no el juez principal)
_modelo = None

def _get_model():
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer("intfloat/multilingual-e5-base")
    return _modelo

# -----------------------------------------------------------
# NORMALIZADOR
# -----------------------------------------------------------

def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKC", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


# -----------------------------------------------------------
# EXTRACCIÓN DE PALABRAS CLAVE DESDE LA PREGUNTA
# -----------------------------------------------------------

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "a", "ante", "bajo", "con", "contra",
    "desde", "durante", "en", "entre", "hacia", "hasta",
    "mediante", "para", "por", "segun", "sin", "sobre", "tras",
    "cual", "que", "donde", "cuando", "cita", "frase", "textual",
    "responde", "solo", "aparezca"
}

def extraer_keywords(pregunta: str):
    p = _normalizar(pregunta)
    tokens = re.findall(r"[a-z0-9+#]+", p)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


# -----------------------------------------------------------
# PATRONES JURÍDICOS IMPORTANTES
# -----------------------------------------------------------

PATRONES_JURIDICOS = [
    r"aprueban? las bases",
    r"apruebese",
    r"apruebase",
    r"resolucion exenta",
    r"resolucion n",
    r"tomado de razon",
    r"considerando",
    r"resuelvo",
    r"fond[e]?cyt",
    r"concurso",
    r"objetivo general",
    r"quienes pueden postular",
    r"beneficiarios",
    r"decreto",
]

def puntaje_lexico(frase: str, keywords):

    frase = re.sub(r'([a-z])([A-Z])', r'\1 \2', frase)
    f = _normalizar(frase)

    score = 0

    # coincidencia por keywords
    for k in keywords:
        if k in f:
            score += 2

    # coincidencia jurídica fuerte
    for patron in PATRONES_JURIDICOS:
        if re.search(patron, f):
            score += 4

    # bonus: contiene número de resolución
    if re.search(r"n[°º]?\s?\d+\/?\d{0,4}", f):
        score += 2

    return score


# -----------------------------------------------------------
# SIMILITUD SEMÁNTICA (AHORA SECUNDARIA)
# -----------------------------------------------------------

def similitud_semantica_batch(frases, pregunta):

    model = _get_model()

    emb_q = model.encode(
        f"query: {pregunta}",
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    emb_f = model.encode(
        [f"passage: {f}" for f in frases],
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    scores = util.cos_sim(emb_f, emb_q).squeeze()

    scores = scores.tolist()

    # asegurar que siempre sea lista
    if isinstance(scores, float):
        scores = [scores]

    return scores


# -----------------------------------------------------------
# NUEVO RERANKER HÍBRIDO
# -----------------------------------------------------------

def rerankear_frases(frases, pregunta):

    if not frases:
        return None, 0.0

    # 🔒 Filtrar frases inválidas
    frases = [f for f in frases if isinstance(f, str) and f.strip()]

    if not frases:
        return None, 0.0

    # 🔒 Limitar tamaño y cantidad
    MAX_LEN = 800
    frases = [f[:MAX_LEN] for f in frases]
    frases = frases[:20]

    keywords = extraer_keywords(pregunta)

    # 1️⃣ FILTRO LÉXICO
    candidatos = []
    for f in frases:
        score_lex = puntaje_lexico(f, keywords)
        if score_lex > 0:
            candidatos.append((f, score_lex))

    if candidatos:
        candidatos.sort(key=lambda x: x[1], reverse=True)
        mejores = candidatos[:8]  # ya incluye score léxico
    else:
        # fallback: usar primeras frases con score léxico calculado
        mejores = [(f, puntaje_lexico(f, keywords)) for f in frases[:12]]

    # 2️⃣ SEMÁNTICA EN BATCH (E5 correcto)
    textos = [f for f, _ in mejores]
    scores_sem = similitud_semantica_batch(textos, pregunta)

    # 3️⃣ SCORE HÍBRIDO NORMALIZADO
    scored = []

    for (f, score_lex), score_sem in zip(mejores, scores_sem):

        # normalización simple del score léxico
        score_lex_norm = min(score_lex / 10, 1.0)

        score_final = (score_lex_norm * 0.6) + (score_sem * 0.4)

        scored.append((f, score_final))

    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0]


# -----------------------------------------------------------
# NIVEL DE CONFIANZA
# -----------------------------------------------------------

def nivel_confianza_semantico(score: float):

    if score >= 0.55:
        return "ALTO"

    if score >= 0.35:
        return "MEDIO"

    return "BAJO"
