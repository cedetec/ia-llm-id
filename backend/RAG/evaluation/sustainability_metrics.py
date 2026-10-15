# sustainability_metrics.py

import time

import psutil


class SustainabilityMetrics:

    def iniciar(self):

        self.t0 = time.perf_counter()

        self.cpu0 = psutil.cpu_times()


    def terminar(self):

        self.t1 = time.perf_counter()

        self.cpu1 = psutil.cpu_times()


    def resumen(self):

        return {

            "cpu_percent":

                psutil.cpu_percent(),

            "cpu_time_user":

                self.cpu1.user

                -

                self.cpu0.user,

            "cpu_time_system":

                self.cpu1.system

                -

                self.cpu0.system,

            "elapsed_seconds":

                self.t1

                -

                self.t0

        }