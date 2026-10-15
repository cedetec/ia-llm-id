# ranking.py
from dataclasses import dataclass

from RAG.reranker.category_classifier import (
    clasificar_categoria
)

from RAG.reranker.bonus_calculator import (
    calcular_bonus
)


@dataclass
class ResultadoRanking:

    documento: object

    score_original: float

    bonus: float

    score_final: float

    categoria: str

    tipo_consulta: str


def construir_ranking(
    documentos,
    scores,
    tipo_consulta,
    tipos_consulta,
    documento_pregunta,
    anio_pregunta
):

    ranking = []

    for doc, score in zip(
        documentos,
        scores
    ):

        score_original = float(score)

        categoria = clasificar_categoria(
            doc
        )

        bonus_resultado = calcular_bonus(

            doc=doc,

            categoria=categoria["categoria"],

            seccion=categoria["seccion"],

            titulo_hijo=categoria["titulo_hijo"],

            encabezado=categoria["encabezado"],

            subtitulo=categoria["subtitulo"],

            score_original=score_original,

            tipo_consulta=tipo_consulta,

            tipos_consulta=tipos_consulta,

            documento_pregunta=documento_pregunta,

            anio_pregunta=anio_pregunta

        )

        score_final = float(
            bonus_resultado["score_final"]
        )

        bonus = (
            score_final
            - score_original
        )

        ranking.append(

            ResultadoRanking(

                documento=doc,

                score_original=score_original,

                bonus=bonus,

                score_final=score_final,

                categoria=categoria["categoria"],

                tipo_consulta=tipo_consulta

            )

        )


    for r in ranking:
        pass


    ranking.sort(

        key=lambda resultado:
            resultado.score_final,

        reverse=True

    )


    for i, r in enumerate(ranking, 1):
        pass


    return ranking
