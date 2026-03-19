#ranking_filters.py

def es_texto_administrativo(texto):

    return any(x in texto for x in [
        "anotese y comuniquese",
        "contralor general",
        "oficial de partes",
        "repositorio de archivo"
    ])
