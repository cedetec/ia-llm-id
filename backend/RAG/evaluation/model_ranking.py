# LLM/evaluation/model_ranking.py


class ModelRanking:

    def ordenar(
        self,
        resultados
    ):

        ranking = []

        rags = []

        for resultado in resultados:

            if resultado["rag"] not in rags:

                rags.append(
                    resultado["rag"]
                )

        for rag in rags:

            resultados_rag = [

                r

                for r in resultados

                if r["rag"] == rag

            ]

            resultados_rag = sorted(

                resultados_rag,

                key=lambda r: (
                    (
                        float("-inf")
                        if r["ragas"].get("context_recall") is None
                        else r["ragas"]["context_recall"]
                    ),
                    -r["latencia"]["total"],
                    -r["memoria"]["ram_delta_mb"]
                ),

                reverse=True

            )

            ranking.extend(
                resultados_rag
            )

        return ranking