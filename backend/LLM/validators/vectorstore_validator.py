# LLM/validators/vectorstore_validator.py

from LLM.config.debug_settings import (
    DEBUG_VECTORSTORE
)

def validar_vectorstore(vectorstore):

    if not DEBUG_VECTORSTORE:
        return

    print("\n========== VECTORSTORE ==========\n")

    print(
        f"Chunks: {vectorstore._collection.count()}"
    )

    datos = vectorstore.get(

        include=[

            "documents",

            "metadatas"

        ]

    )

    limite = min(

        10,

        len(datos["documents"])

    )

    for i in range(limite):

        print("=" * 80)

        print(datos["metadatas"][i])

        print(datos["documents"][i][:300])