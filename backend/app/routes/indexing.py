# indexing.py

from fastapi import APIRouter

from RAG.indexing.indexing_service import (
    indexar_documentos
)

from app.startup import reinicializar_rag

router = APIRouter()


@router.post("/index")
def indexar():


    indexar_documentos()

    reinicializar_rag()


    return {
        "mensaje": "Indexación finalizada."
    }