# LLM/rerank/rerank_service.py

from sentence_transformers import CrossEncoder

from LLM.config.reranker_settings import (
    DEFAULT_RERANKER_MODEL,
    DEFAULT_RERANK_TOP_K
)

from LLM.reranker.ranking import (
    construir_ranking
)

from LLM.validators.reranker_validator import (
    validar_ranking
)


def construir_texto_rerank(doc):
    """
    Construye el texto enriquecido que utilizará el
    CrossEncoder para evaluar la relevancia del chunk.
    """

    return f"""
DOCUMENT:
{doc.metadata.get("documento","")}

SECTION:
{doc.metadata.get("seccion","")}

PARENT:
{doc.metadata.get("titulo_padre","")}

CHILD:
{doc.metadata.get("titulo_hijo","")}

SUBTITLE:
{doc.metadata.get("subtitulo","")}

CONTENT:

{doc.page_content}

HEADER:
{doc.metadata.get("encabezado_original","")}
"""


class Reranker:

    def __init__(self, model_name=None):

        if model_name is None:
            model_name = DEFAULT_RERANKER_MODEL

        self.model = CrossEncoder(model_name)

    def rerank(

        self,

        pregunta,

        documentos,

        tipo_consulta,

        tipos_consulta,

        documento_pregunta,

        anio_pregunta,

        top_k=DEFAULT_RERANK_TOP_K,

        metricas=None

    ):

        if not documentos:
            return []

        pares = [

            (
                pregunta,
                construir_texto_rerank(doc)
            )

            for doc in documentos

        ]

        scores = self.model.predict(pares)

        print("=" * 80)
        print("[SCORES CROSS-ENCODER]")
        print("=" * 80)

        for doc, score in zip(documentos, scores):

            print(
                {
                    "score": round(float(score), 4),
                    "pagina": doc.metadata.get("pagina"),
                    "documento": doc.metadata.get("documento"),
                    "seccion": doc.metadata.get("seccion"),
                    "titulo_hijo": doc.metadata.get("titulo_hijo"),
                    "subtitulo": doc.metadata.get("subtitulo"),
                    "encabezado": doc.metadata.get("encabezado_original")
                }
            )

        ranking = construir_ranking(

            documentos=documentos,

            scores=scores,

            tipo_consulta=tipo_consulta,

            tipos_consulta=tipos_consulta,

            documento_pregunta=documento_pregunta,

            anio_pregunta=anio_pregunta

        )

        validar_ranking(ranking)

        if metricas is not None:

            metricas.rerank.registrar(

                antes=documentos,

                despues=ranking[:top_k]

            )

        return ranking[:top_k]

reranker = Reranker()


def rerank_documentos(

    pregunta,

    documentos,

    tipo_consulta,

    documento_pregunta,

    anio_pregunta,

    top_k=DEFAULT_RERANK_TOP_K,

    metricas=None,

    tipos_consulta=None

):

    return reranker.rerank(

        pregunta=pregunta,

        documentos=documentos,

        tipo_consulta=tipo_consulta,

        documento_pregunta=documento_pregunta,

        anio_pregunta=anio_pregunta,

        top_k=top_k,

        metricas=metricas,

        tipos_consulta=tipos_consulta

    )
