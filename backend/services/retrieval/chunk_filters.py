# backend/services/retrieval/chunk_filters.py

def filtrar_posicional(docs, seccion_objetivo):

    if not seccion_objetivo:
        return docs

    def es_valido(d):

        meta = d.get("metadata", {})
        idx = meta.get("chunk_index")
        total = meta.get("total_chunks")

        cont = d.get("contenido", "")
        cont_l = cont.lower()

        # ⚠️ bypass inteligente si el texto contiene la sección
        if seccion_objetivo == "objetivo":
            if "objetivo del concurso" in cont_l or "objetivo de este concurso" in cont_l:
                return True

        if not total or idx is None:
            return True

        ratio = idx / total

        if seccion_objetivo == "objetivo":
            return 0.02 <= ratio <= 0.60

        if seccion_objetivo == "beneficiarios":
            return 0.10 <= ratio <= 0.60

        if seccion_objetivo == "requisitos":
            return 0.15 <= ratio <= 0.75

        if seccion_objetivo == "postulacion":
            return 0.15 <= ratio <= 0.80

        if seccion_objetivo == "resolucion":
            return ratio <= 0.20

        return True

    return [d for d in docs if es_valido(d)]