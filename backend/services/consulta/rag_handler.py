#rag_handler
from backend.services.retrieval_service import obtener_contexto
from backend.services.retrieval_text_utils import normalizar
from backend.services.frase_ranker import rankear_frases
from backend.services.retrieval_text_utils import safe_split


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

    textos = []
    vistos = set()

    if isinstance(resultado, list):

        for r in resultado:

            if isinstance(r, dict):
                texto = r.get("contenido") or r.get("texto") or ""

                if isinstance(texto, str) and len(texto) > 20:

                    key = hash(texto[:300])

                    if key not in vistos:
                        textos.append(texto)
                        vistos.add(key)

            elif isinstance(r, str):

                if len(r) > 20:

                    key = r[:120]

                    if key not in vistos:
                        textos.append(r)
                        vistos.add(key)

    if not textos:
        return None

    # =====================================================
    # 🔥 SIEMPRE USAR FRASES (CLAVE RAG)
    # =====================================================

    tokens = safe_split(normalizar(pregunta))

    frases_top = []

    for t in textos:

        # 🔥 FIX CRÍTICO
        if isinstance(t, dict):
            t = t.get("contenido") or t.get("texto") or ""

        if not isinstance(t, str):
            continue

        t = re.sub(r'(?<=\d)l(?=\d)', '1', t)

        ranked = rankear_frases(t, tokens, pregunta=pregunta, top_k=3)
        frases_top.extend(ranked)

    # 🔥 eliminar duplicados
    frases_top = list(dict.fromkeys(frases_top))

    if frases_top:
        textos = frases_top[:5]

    # =====================================================
    # RE-RANKING DE FRASES
    # =====================================================

    if modo_cita:

        frases_top = []

        for t in textos:

            # 🔥 FIX CRÍTICO
            if isinstance(t, dict):
                t = t.get("contenido") or t.get("texto") or ""

            if not isinstance(t, str):
                continue

            ranked = rankear_frases(t, tokens, pregunta=pregunta, top_k=5)
            frases_top.extend(ranked)

        # 🔥 eliminar duplicados
        frases_top = list(dict.fromkeys(frases_top))

        if frases_top:
            textos = frases_top[:5]

    contexto = ""

    for i,t in enumerate(textos):
        contexto += f"\n\n[Fragmento {i+1}]\n{t}\n"

    MAX_CONTEXT = 4500
    contexto = contexto[:MAX_CONTEXT]

    print("------ CONTEXTO RAG ------")
    print(contexto[:800])
    print("--------------------------")

    return contexto
