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

    subchunks = splitter.split_documents(

        [documento]

    )

    return subchunks
