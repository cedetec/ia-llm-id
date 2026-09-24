# ground_truth_loader.py

import json

from pathlib import Path


class GroundTruthLoader:

    def __init__(

        self,

        archivo="LLM/evaluation/evaluation_dataset.json"

    ):

        self.archivo = Path(
            archivo
        )

    def cargar(self):

        with open(

            self.archivo,

            encoding="utf8"

        ) as f:

            return json.load(f)
