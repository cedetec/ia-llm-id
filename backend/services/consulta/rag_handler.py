#rag_handler
from backend.services.retrieval_service import obtener_contexto
from backend.services.retrieval_text_utils import normalizar


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

        resultado = sorted(
            resultado,
            key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0,
            reverse=True
        )

        for r in resultado:

            if isinstance(r, dict):
                texto = r.get("contenido") or r.get("texto") or ""

                if isinstance(texto, str) and len(texto) > 20:

                    key = texto[:120]

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

    contexto = "\n\n".join(textos)

    MAX_CONTEXT = 40000
    contexto = contexto[:MAX_CONTEXT]

    print("------ CONTEXTO RAG ------")
    print(contexto[:800])
    print("--------------------------")

    return contexto
