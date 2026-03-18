#rag_handler.py

from backend.services.retrieval_service import obtener_contexto
from backend.services.retrieval_text_utils import normalizar
from backend.services.frase_ranker import rankear_frases
import re


def limpiar_texto(texto):
    texto = re.sub(r'[^\x00-\x7FáéíóúÁÉÍÓÚñÑ.,;:()0-9A-Za-z ]+', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def puntaje_extra(doc):
    score = 0
    
    metadata = doc.get("metadata", {})
    texto = doc.get("texto", "").lower()
    
    if metadata.get("es_resolutivo"):
        score += 3
        
    if metadata.get("seccion") == "objetivo":
        score += 2
        
    if metadata.get("tipo_chunk") == "resolucion":
        score += 2
        
    # BONUS PRO
    if "aprueba" in texto or "resuelve" in texto or "apruébase" in texto:
        score += 2
        
    return score


def recuperar_contexto(pregunta, modo_cita=False, docfile=None):

    if docfile:
        docfile = normalizar(docfile)

    resultado = obtener_contexto(
        pregunta,
        modo_cita=modo_cita,
        filtro_doc=docfile
    )

    if not resultado:
        return None

    if isinstance(resultado, str):
        return resultado

    # =====================================================
    # 🔥 PASO 1: CONSTRUIR DOCS CON METADATA
    # =====================================================

    docs = []

    if isinstance(resultado, list):

        for r in resultado:

            if isinstance(r, dict):
                texto = r.get("contenido") or r.get("texto") or ""

                if isinstance(texto, str) and len(texto) > 20:
                    docs.append({
                        "texto": texto,
                        "metadata": r.get("metadata", {}),
                        "score": r.get("score", 0) + r.get("pre_score", 0)
                    })

            elif isinstance(r, str):

                if len(r) > 20:
                    docs.append({
                        "texto": r,
                        "metadata": {},
                        "score": 0
                    })

    if not docs:
        return None

    # =====================================================
    # 🔥 PASO 2: RE-RANKING INTELIGENTE
    # =====================================================

    docs = sorted(
        docs,
        key=lambda d: d.get("score", 0) + puntaje_extra(d),
        reverse=True
    )

    # =====================================================
    # 🔥 PASO 3: EXTRAER TEXTOS LIMPIOS Y LIMITAR
    # =====================================================

    textos = []
    vistos = set()

    for d in docs[:40]:  # 🔥 límite importante
        texto = d["texto"]

        key = hash(texto[:300])

        if key not in vistos:
            textos.append(texto)
            vistos.add(key)

    if not textos:
        return None

    # =====================================================
    # 🔥 PASO 4: RANKEO DE FRASES
    # =====================================================

    tokens = normalizar(pregunta).split()
    frases_top = []

    for t in textos:

        t = t.replace("\n", " ").strip()

        if len(t) < 40:
            continue

        ranked = rankear_frases(t, tokens, top_k=3)
        frases_top.extend(ranked)

    if frases_top:
        textos = frases_top[:5]

    # =====================================================
    # 🔥 PASO 5: RE-RANKING EXTRA EN MODO CITA
    # =====================================================

    if modo_cita:

        frases_top = []

        for t in textos:
            ranked = rankear_frases(t, tokens, top_k=5)
            frases_top.extend(ranked)

        if frases_top:
            textos = frases_top[:5]

    # =====================================================
    # 🔥 PASO 6: LIMPIEZA FINAL
    # =====================================================

    contexto = ""

    for i, t in enumerate(textos):

        t = limpiar_texto(t)

        if len(t) < 30:
            continue

        contexto += f"\n\n[Fragmento {i+1}]\n{t}\n"

    MAX_CONTEXT = 4500
    contexto = contexto[:MAX_CONTEXT]

    print("------ CONTEXTO RAG ------")
    print(contexto[:800])
    print("--------------------------")

    return contexto
