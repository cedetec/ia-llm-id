# services/indexing/metadata_builder.py

from backend.utils.document_utils import normalizar_nombre_doc


def build_metadata(row):

    documento_raw = row.get("documento")
    documento_norm = normalizar_nombre_doc(documento_raw)

    return {
        "documento": documento_raw,
        "documento_norm": documento_norm,
        "origen": row.get("origen"),
        "tipo": row.get("tipo"),
        "fecha": row.get("fecha"),
        "chunk_index": row.get("chunk_index"),
        "total_chunks": row.get("total_chunks"),
        "doc_id": row.get("doc_id"),
        "gridfs_id": row.get("gridfs_id"),
        "chunk_id": row.get("chunk_id"),
    }