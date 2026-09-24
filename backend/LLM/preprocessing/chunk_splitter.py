# LLM/preprocessing/chunk_splitter.py

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 200

SEPARATORS = [

    "\n\n",

    "\n",

    ". ",

    " ",

    ""

]

splitter = RecursiveCharacterTextSplitter(

    chunk_size=CHUNK_SIZE,

    chunk_overlap=CHUNK_OVERLAP,

    separators=SEPARATORS

)


def dividir_subchunks(documento):

    print(

        "[CHUNK SPLITTER]",

        {

            "chunk_size": CHUNK_SIZE,

            "chunk_overlap": CHUNK_OVERLAP,

            "separators": SEPARATORS

        }

    )

    print(

        "[DOCUMENTO ENTRADA]",

        {

            "palabras": len(documento.page_content.split()),

            "lineas": len(documento.page_content.splitlines()),

            "inicio": " ".join(

                documento.page_content.split()[:20]

            )

        }

    )

    print(repr(documento.page_content[:1000]))

    subchunks = splitter.split_documents(

        [documento]

    )

    print(

        "[RESULTADO SPLITTER]",

        {

            "subchunks": len(subchunks)

        }

    )

    for i, chunk in enumerate(subchunks):

        print(

            "[SUBCHUNK]",

            {

                "indice": i,

                "palabras": len(chunk.page_content.split()),

                "lineas": len(chunk.page_content.splitlines()),

                "inicio": " ".join(

                    chunk.page_content.split()[:15]

                )

            }

        )

    return subchunks
