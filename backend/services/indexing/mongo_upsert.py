# services/indexing/mongo_upsert.py

from database import index_collection
from datetime import datetime


def upsert_chunk(chunk_id, contenido, metadata, embedding, content_hash):

    now = datetime.utcnow()

    return index_collection.update_one(
        {"chunk_id": chunk_id},
        {
            "$set": {
                "contenido": contenido,
                "embedding": embedding,
                "content_hash": content_hash,
                "metadata": metadata,
            },
            "$setOnInsert": {
                "created_at": now,
            },
            "$currentDate": {
                "touched_at": True
            }
        },
        upsert=True
    )