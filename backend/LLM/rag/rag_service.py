# LLM/rag/rag_service.py

import logging

from RAG.rag.context_builder import (
    construir_contexto
)

from RAG.rag.retrieval_pipeline import (
    RetrievalPipeline
)

from RAG.evaluation.rag_metrics import (
    RAGMetrics
)

from RAG.rag.document_detector import (
    detectar_documentos
)


logger = logging.getLogger(__name__)

DEBUG = False


class RAGService:

    def __init__(
        self,
        retriever,
        top_k=4
    ):

        self.pipeline = RetrievalPipeline(
            retriever=retriever,
            top_k=top_k
        )

    # =====================================================
    # Métodos privados de depuración
    # =====================================================

    def _debug_contexto(
        self,
        documentos,
        contexto
    ):

        logger.debug(
            "Contexto: %s documentos (%s caracteres)",
            len(documentos),
            len(contexto)
        )

        for doc in documentos:

            logger.debug(
                "%s | %s | %s",
                doc.metadata.get("documento"),
                doc.metadata.get("pagina"),
                doc.metadata.get("seccion")
            )

    # =====================================================
    # Recuperación principal
    # =====================================================

    def recuperar(
        self,
        pregunta,
        documento=None,
        documentos_relevantes=None
    ):

        #
        # Detectar automáticamente documentos
        # cuando /chat no los entrega explícitamente.
        #

        if documentos_relevantes is None:

            documentos_detectados = detectar_documentos(
                pregunta
            )

            if len(documentos_detectados) > 1:

                documentos_relevantes = [
                    [
                        item["documento"],
                        item["anio"]
                    ]
                    for item in documentos_detectados
                ]

        #
        # Recuperación
        #

        metricas = RAGMetrics()

        pregunta_busqueda = pregunta.lower()

        documentos = self.pipeline.recuperar(
            pregunta_busqueda,
            pregunta,
            metricas,
            documento=documento,
            documentos_relevantes=documentos_relevantes
        )

        #
        # Contextos individuales para RAGAS
        #

        contextos_ragas = [
            doc.page_content
            for doc in documentos
        ]

        #
        # Construcción del contexto
        #

        contexto = construir_contexto(
            documentos
        )

        #
        # Depuración
        #

        if DEBUG:

            self._debug_contexto(
                documentos,
                contexto
            )

        return {

            "context": documentos,

            "context_text": contexto,

            "contextos_ragas": contextos_ragas,

            "metricas": {

                "retrieval":
                    metricas.retrieval.resumen(),

                "rerank":
                    metricas.rerank.resumen(),

                "respuesta":
                    metricas.answer.resumen()

            }

        }


def construir_rag(
    retriever,
    top_k=4
):

    return RAGService(
        retriever,
        top_k
    )
