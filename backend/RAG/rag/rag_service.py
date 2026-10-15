# LLM/rag/rag_service.py

import logging

from langchain_core.prompts import ChatPromptTemplate

from LLM.prompts.system_prompt import SYSTEM_PROMPT

from RAG.rag.context_builder import (
    construir_contexto
)

from RAG.rag.retrieval_pipeline import (
    RetrievalPipeline
)



from RAG.evaluation.rag_metrics import (
    RAGMetrics
)

from RAG.config.llm_config import (
    cambiar_modelo
)

from LLM.llm.ollama_client import (
    crear_llm
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

        llm,

        top_k=4

    ):

        self.llm = llm

        self.pipeline = RetrievalPipeline(

            retriever=retriever,

            top_k=top_k

        )

        self.prompt = ChatPromptTemplate.from_messages(

            [

                (

                    "system",

                    SYSTEM_PROMPT

                ),

                (

                    "human",

                    """
Pregunta:
    pass

{input}

Responde únicamente en español.

No traduzcas la pregunta al inglés.

Utiliza solamente el contexto entregado.
"""

                )

            ]

        )

    def cambiar_modelo(
        self,
        modelo
    ):
    
        cambiar_modelo(
            modelo
        )
    
        self.llm = crear_llm()
    

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

    def _debug_prompt(

        self,

        mensajes

    ):

        prompt = "\n".join(

            mensaje.content

            for mensaje in mensajes.messages

        )

        logger.debug(

            "Prompt (%s caracteres)",

            len(prompt)

        )


    # =====================================================
    # Invocación principal
    # =====================================================

    def invoke(
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

            documentos_detectados = (
                detectar_documentos(
                    pregunta
                )
            )

            #
            # Activar el modo multidocumento
            # solo cuando realmente haya más
            # de un documento detectado.
            #

            if len(documentos_detectados) > 1:

                documentos_relevantes = [

                    [
                        item["documento"],
                        item["anio"]
                    ]

                    for item
                    in documentos_detectados

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
        # Contextos individuales para evaluación RAGAS.
        #

        contextos_ragas = [

            doc.page_content

            for doc in documentos

        ]

        #
        # Construcción del contexto.
        #

        contexto = construir_contexto(

            documentos

        )

        #
        # Construcción del prompt.
        #

        mensajes = self.prompt.invoke(

            {

                "context": contexto,

                "input": pregunta

            }

        )

        #
        # Depuración opcional.
        #

        if DEBUG:

            self._debug_contexto(

                documentos,

                contexto

            )

            self._debug_prompt(

                mensajes

            )

        #
        # Invocar el modelo.
        #

        respuesta = self.llm.invoke(

            mensajes

        )

        #
        # Registrar métricas.
        #

        metricas.answer.registrar(

            respuesta={

                "texto": respuesta.content,

                "documentos": documentos

            }

        )

        #
        # Validar salida.
        #


        #
        # Resultado.
        #

        return {

            "answer": respuesta.content,

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

    llm,

    top_k=4

):

    return RAGService(

        retriever,

        llm,

        top_k

    )
