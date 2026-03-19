# ranking_heuristicas_legales.py

def heuristicas_juridicas(texto):

    score = 0

    if "resuelvo" in texto and "bases" in texto:
        score += 3.5

    if "aprueb" in texto and "bases" in texto:
        score += 5

    if "bases concursales" in texto:
        score += 1.8

    if "objetivo del concurso" in texto:
        score += 8.5

    if "objetivo general del concurso" in texto:
        score += 9

    if "apruebanse las bases" in texto:
        score += 20

    return score
