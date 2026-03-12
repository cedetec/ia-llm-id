#embedding_service.py

from sentence_transformers import SentenceTransformer
import re

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model


def _normalize_for_embedding(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"\[DOC:[^\]]+\]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def embed_text(text: str, mode: str = "passage") -> list[float]:

    if not text or not text.strip():
        raise ValueError("Texto vacío no puede ser embebido")

    if mode not in {"query", "passage"}:
        raise ValueError("mode debe ser 'query' o 'passage'")

    text = _normalize_for_embedding(text)

    MAX_CHARS = 2000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    MAX_WORDS = 350
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])

    text = f"{mode}: {text}"

    model = _get_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding.tolist()
