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
        contexto = resultado

    elif isinstance(resultado, list):

        textos = []

        for r in resultado:

            if isinstance(r, str):
                textos.append(r)

            elif isinstance(r, dict):
                texto = r.get("contenido") or r.get("texto") or ""
                if texto:
                    textos.append(texto)

        contexto = "\n".join(textos)

    else:
        return None

    MAX_CONTEXT = 8000
    contexto = contexto[:MAX_CONTEXT]

    print("------ CONTEXTO RAG ------")
    print(contexto[:800])
    print("--------------------------")

    return contexto