# services/preprocessing/chunk_id_builder.py

import hashlib


def build_chunk_id(doc_id, documento, tipo, origen, index, texto):
    base = f"{doc_id}|{documento}|{tipo}|{origen}|{index}|{texto[:50]}"
    return hashlib.sha1(base.encode()).hexdigest()