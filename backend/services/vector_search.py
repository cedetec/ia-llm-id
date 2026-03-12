#vector_search.py
from sentence_transformers import SentenceTransformer
from database.mongo import index_collection
from services.retrieval_text_utils import normalizar

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model


def buscar_semanticamente(pregunta, documento=None, k=6):

    model = _get_model()

    pregunta = pregunta.strip()

    query_embedding = model.encode(
        f"query: {pregunta}",
        normalize_embeddings=True
    )

    query_embedding = list(query_embedding)

    vector_stage = {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,
            "numCandidates": 600,
            "limit": k,
        }
    }

    if documento:

        documento_norm = normalizar(documento)

        vector_stage["$vectorSearch"]["filter"] = {
            "metadata.documento_norm": documento_norm
        }

    pipeline = [
        vector_stage,
        {
            "$project": {
                "contenido": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    return list(index_collection.aggregate(pipeline))
