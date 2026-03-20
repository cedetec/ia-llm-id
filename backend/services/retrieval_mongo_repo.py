#retrieval_mongo_repo.py
from __future__ import annotations
from typing import Dict, List, Any
from database.mongo import index_collection


def find_docs(filtro: Dict, *, scan: int) -> List[Dict[str, Any]]:

    # ----------------------------------------
    # Validación de scan
    # ----------------------------------------

    DEFAULT_SCAN = 800
    MAX_SCAN = 6000

    if not isinstance(scan, int) or scan <= 0:
        scan = DEFAULT_SCAN

    scan = max(scan, DEFAULT_SCAN)
    scan = min(scan, MAX_SCAN)

    query = dict(filtro) if isinstance(filtro, dict) else {}

    # ----------------------------------------
    # asegurar contenido válido
    # ----------------------------------------

    contenido_cond = {"contenido_norm": {"$exists": True, "$ne": ""}}

    if query:
        query = {
            "$and": [
                contenido_cond,
                query
            ]
        }
    else:
        query = contenido_cond

    # ----------------------------------------
    # consulta Mongo
    # ----------------------------------------

    cursor = (
        index_collection
        .find(
            query,
            {
                "contenido": 1,
                "contenido_norm": 1,  # 🔥 CRÍTICO
                "metadata": 1,
                "embedding": 1
            }
        )
        .limit(scan)
    )

    docs = list(cursor)

    # ----------------------------------------
    # seguridad de metadata
    # ----------------------------------------

    for d in docs:

        if "metadata" not in d or not isinstance(d["metadata"], dict):
            d["metadata"] = {}

        if "contenido" not in d:
            d["contenido"] = ""

        if "contenido_norm" not in d or not d["contenido_norm"]:
            d["contenido_norm"] = d.get("contenido", "")

    print("DOCS TRAIDOS:", len(docs))
    print("PRIMEROS DOCS:", [
        d["metadata"].get("seccion") for d in docs[:10]
    ])

    return docs
