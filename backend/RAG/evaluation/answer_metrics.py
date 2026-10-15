# answer_metrics.py

class AnswerMetrics:

    def __init__(self):

        self.longitud = 0

        self.tokens = 0

        self.tiempo = 0

        self.documentos = 0

    def registrar(
        self,
        respuesta
    ):

        self.longitud = len(
            respuesta["texto"]
        )

        self.tokens = len(
            respuesta["texto"].split()
        )

        self.documentos = len(
            respuesta["documentos"]
        )

    def resumen(self):

        return {

            "caracteres":

                self.longitud,

            "tokens":

                self.tokens,

            "documentos":

                self.documentos

        }
