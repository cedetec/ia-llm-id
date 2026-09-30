# LLM/evaluation/latency_metrics.py

import time


class LatencyMetrics:

    def __init__(self):

        self._inicio = {}

        self._fin = {}

    def iniciar(self, etapa):

        self._inicio[etapa] = (
            time.perf_counter()
        )

    def terminar(self, etapa):

        self._fin[etapa] = (
            time.perf_counter()
        )

    def tiempo_ms(self, etapa):

        return round(

            (
                self._fin[etapa]
                -
                self._inicio[etapa]
            ) * 1000,

            2

        )

    def resumen(self):

        return {

            etapa: self.tiempo_ms(etapa)

            for etapa in self._inicio

        }