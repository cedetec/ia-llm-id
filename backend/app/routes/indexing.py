# indexing.py

from fastapi import APIRouter

from RAG.indexing.indexing_service import (
    indexar_documentos
)

from app.startup import reinicializar_rag

router = APIRouter()


@router.post("/index")
def indexar():

    print("=" * 80)
    print("ENTRANDO AL ENDPOINT /index")
    print("=" * 80)

    indexar_documentos()

    reinicializar_rag()

    print("=" * 80)
    print("SALIENDO DEL ENDPOINT /index")
    print("=" * 80)

    return {
        "mensaje": "Indexación finalizada."
    }