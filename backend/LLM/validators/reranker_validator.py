# reranker_validator.py

from LLM.config.debug_settings import (
    DEBUG_RERANKER
)


def validar_ranking(ranking):

    if not DEBUG_RERANKER:
        return

    print("\n========== RERANK ==========\n")

    for i, resultado in enumerate(ranking):

        print("=" * 80)

        print(
            f"Posición        : {i + 1}"
        )

        print(
            f"Tipo consulta   : "
            f"{resultado.tipo_consulta}"
        )

        print(
            f"Categoría       : "
            f"{resultado.categoria}"
        )

        print(
            f"Documento       : "
            f"{resultado.documento.metadata.get('documento')}"
        )

        print(
            f"Sección         : "
            f"{resultado.documento.metadata.get('seccion')}"
        )

        print(
            f"Página          : "
            f"{resultado.documento.metadata.get('pagina')}"
        )

        print(
            f"Score original  : "
            f"{resultado.score_original:.4f}"
        )

        print(
            f"Bonus           : "
            f"{resultado.bonus:.4f}"
        )

        print(
            f"Score ajustado  : "
            f"{resultado.score_final:.4f}"
        )

        print()

        print(
            resultado.documento.page_content[:300]
        )

        print()

