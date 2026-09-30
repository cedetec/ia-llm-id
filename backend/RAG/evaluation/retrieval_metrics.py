# LLM/evaluation/retrieval_metrics.py

class RetrievalMetrics:

    def __init__(self):

        self.chunks_recuperados = 0

        self.chunks_finales = 0

        self.documentos = set()

        self.documentos_recuperados = []

        self.paginas_recuperadas = []

        self.score_promedio = 0

        self.score_max = 0

        self.score_min = 0

    def registrar(

        self,

        documentos_recuperados,

        documentos_finales

    ):

        #
        # Retriever antes del filtrado
        #

        self.chunks_recuperados = len(
            documentos_recuperados
        )

        #
        # Chunks después del filtrado
        #

        self.chunks_finales = len(
            documentos_finales
        )

        #
        # Documentos distintos
        #

        self.documentos = {

            doc.metadata.get("documento")

            for doc in documentos_finales

            if doc.metadata.get("documento")

        }

        #
        # Guardar documentos recuperados
        # para métricas y análisis de contexto.
        #

        self.documentos_recuperados = [

            doc.metadata.get("documento")

            for doc in documentos_finales

            if doc.metadata.get("documento")

        ]

        #
        # Guardar documento + página.
        #

        self.paginas_recuperadas = [

            (

                doc.metadata.get("documento"),

                doc.metadata.get("pagina")

            )

            for doc in documentos_finales

        ]

        #
        # Scores
        #

        scores = []

        for doc in documentos_finales:

            score = doc.metadata.get(
                "retrieval_score"
            )

            if score is not None:

                scores.append(
                    float(score)
                )

        if scores:

            self.score_promedio = (

                sum(scores)

                /

                len(scores)

            )

            self.score_max = max(scores)

            self.score_min = min(scores)

        else:

            self.score_promedio = 0

            self.score_max = 0

            self.score_min = 0

    def resumen(self):

        return {

            "chunks_recuperados":

                self.chunks_recuperados,

            "chunks":

                self.chunks_finales,

            "documentos_distintos":

                len(self.documentos),

            #
            # Información adicional para análisis
            # del contexto recuperado.
            #

            "documentos":

                self.documentos_recuperados,

            "paginas":

                self.paginas_recuperadas,

            "score_promedio":

                round(
                    self.score_promedio,
                    3
                ),

            "score_max":

                round(
                    self.score_max,
                    3
                ),

            "score_min":

                round(
                    self.score_min,
                    3
                )

        }