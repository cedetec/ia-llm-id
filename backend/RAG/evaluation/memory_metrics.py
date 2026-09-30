# LLM/evaluation/memory_metrics.py

import os

import psutil


class MemoryMetrics:

    def __init__(self):

        self.process = psutil.Process(
            os.getpid()
        )

        self.before = None

        self.after = None

    def iniciar(self):

        self.before = (
            self.process.memory_info()
        )

    def terminar(self):

        self.after = (
            self.process.memory_info()
        )

    def resumen(self):

        return {

            "ram_before_mb":

                round(
                    self.before.rss
                    /1024/1024,
                    2
                ),

            "ram_after_mb":

                round(
                    self.after.rss
                    /1024/1024,
                    2
                ),

            "ram_delta_mb":

                round(

                    (
                        self.after.rss
                        -
                        self.before.rss
                    )/1024/1024,

                    2

                )

        }