# services/indexing/embedding_pipeline.py

from backend.services.embedding_service import embed_text


def generar_embedding(texto: str, tipo_doc: str):

    prefijo = {
        "bases":
            "bases de concurso ANID investigacion objetivos requisitos postulacion financiamiento evaluacion ",
        "resolucion_aprobatoria":
            "resolucion administrativa gobierno chile acto administrativo aprobacion bases considerando resuelvo ",
        "otro":
            "documento institucional administrativo chile "
    }

    texto_final = prefijo.get(tipo_doc, "") + texto

    return embed_text(texto_final, "passage")