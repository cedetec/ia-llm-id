# rerank_metrics.py

class RerankMetrics:

    def __init__(self):

        self.before = 0
        self.after = 0

        self.score_max = 0
        self.score_min = 0
        self.score_mean = 0

    def registrar(

        self,

        antes,

        despues

    ):

        self.before = len(antes)

        self.after = len(despues)

        if not despues:
            self.score_max = 0
            self.score_min = 0
            self.score_mean = 0
            return

        scores = [

            resultado.score_final

            for resultado in despues

        ]

        self.score_max = max(scores)

        self.score_min = min(scores)

        self.score_mean = (
            sum(scores) / len(scores)
        )

    def resumen(self):

        return {

            "antes": self.before,

            "despues": self.after,

            "score_max":
                self.score_max,

            "score_min":
                self.score_min,

            "score_mean":
                self.score_mean

        }
