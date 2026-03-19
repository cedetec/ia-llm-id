#ranking_boosts_anid.py
import re


def aplicar_boosts_anid(
    total,
    cont_l,
    inicio,
    seccion,
    intent,
    preg_benef
):

    # -------------------------------------------------
    # BOOST POR ENCABEZADOS NUMERADOS ANID
    # -------------------------------------------------

    if re.search(r'\b1\s*[\.\-\)]?\s*(objetivo|finalidad)', cont_l):
        total += 22

    if re.search(r'\b2\s*[\.\-\)]?\s*(requisitos?)', cont_l):
        total += 35

    if re.search(r'\b3\s*[\.\-\)]?\s*(postul|benefici)', cont_l):
        total += 32

    if re.search(r'\b4\s*[\.\-\)]?\s*(evaluacion)', cont_l):
        total += 30

    if re.search(r'\b5\s*[\.\-\)]?\s*(financ)', cont_l):
        total += 28

    # -------------------------------------------------
    # OBJETIVO
    # -------------------------------------------------

    if intent == "objetivo":

        if "objetivo del concurso" in inicio or "objetivo general del concurso" in inicio:
            total += 28

        if "objetivo del concurso" in cont_l:
            total += 22

        if re.search(r'\b1\s*[\.\-\)]?\s*(objetivo|finalidad|proposito)', cont_l):
            total += 22

        if cont_l.startswith("objetivo"):
            total += 18

        if "tiene por objetivo" in cont_l:
            total += 12

        if "objetivo" in seccion:
            total += 30
        else:
            total -= 8

    # -------------------------------------------------
    # REQUISITOS
    # -------------------------------------------------

    elif intent == "requisitos":

        if "requisitos de postulacion" in inicio:
            total += 24

        if re.search(r'\b2\s*[\.\-\)]?\s*(requisitos?)', cont_l):
            total += 22

        if re.search(r'^\s*requisitos', cont_l):
            total += 16

        if "requisito" in seccion:
            total += 28
        else:
            total -= 6

    # -------------------------------------------------
    # POSTULACIÓN / BENEFICIARIOS
    # -------------------------------------------------

    elif intent == "postulacion":

        if re.search(r'notificara|notificacion|resultado|carta certificada|plataforma en linea', cont_l):
            total -= 20

        if preg_benef:

            if re.search(r'quienes\s+pueden\s+postular', cont_l):
                total += 65

            elif re.search(r'podran\s+postular', cont_l):
                total += 55

            elif re.search(r'pueden\s+postular', cont_l):
                total += 45

        if re.search(r'\b(podran\s+postular|podra\s+postular|podran\s+participar|podran\s+presentar)\b', cont_l):
            total += 30

        if re.search(r'\b3\s*[\.\-\)]?\s*(postul|benefici)', cont_l):
            total += 20

        if re.search(r'^\s*(postulacion|postulantes)', cont_l):
            total += 14

        if "postul" in seccion:
            total += 26
        else:
            total -= 6

    # -------------------------------------------------
    # BASES / RESOLUCIONES
    # -------------------------------------------------

    elif intent in ["bases", "resolucion"]:

        if re.search(r'\b(resuelvo|apruebase|apruebanse|aprueba[n]?|se\s+aprueba[n]?)\b', cont_l):
            total += 42

        if re.search(r'\bapruebanse\s+las\s+bases\s+del\s+concurso', cont_l):
            total += 45

        if "aprueba las bases" in cont_l or "aprueban las bases" in cont_l:
            total += 45

        if "bases del concurso" in cont_l:
            total += 12

        if "bases concursales" in cont_l:
            total += 10

        if seccion in ["beneficiarios", "evaluacion"]:
            total -= 10

    # -------------------------------------------------
    # BOOST RESOLUCIONES
    # -------------------------------------------------

    if intent == "resolucion":

        if "resolucion exenta" in cont_l:
            total += 14

        if "resolucion n" in cont_l:
            total += 10

        if "resuelvo" in cont_l:
            total += 10

    # -------------------------------------------------
    # ENTIDADES IMPORTANTES
    # -------------------------------------------------

    if "agencia nacional de investigacion y desarrollo" in cont_l:
        total += 12

    if "investigador responsable" in cont_l:
        total += 9

    if "institucion patrocinante" in cont_l:
        total += 9

    # -------------------------------------------------
    # SECCIONES JURÍDICAS IMPORTANTES
    # -------------------------------------------------

    if "resolucion" in seccion:
        total += 12

    if "aprobacion" in seccion:
        total += 11

    if "bases" in seccion:
        total += 10

    if "convocatoria" in seccion:
        total += 8

    # -------------------------------------------------
    # SECTION-AWARE BOOST
    # -------------------------------------------------

    if intent:

        if seccion == intent:
            total += 45

        elif intent in seccion:
            total += 32

        elif seccion in ["bases", "convocatoria"]:
            total += 10

    if seccion and intent and seccion != intent:

        if seccion in ["evaluacion", "financiamiento"] and intent == "postulacion":
            total -= 20

        if seccion == "objetivo" and intent == "requisitos":
            total -= 15

        if seccion == "requisitos" and intent == "objetivo":
            total -= 10

    # -------------------------------------------------
    # BOOST ENCABEZADOS DIRECTOS
    # -------------------------------------------------

    if cont_l.startswith("objetivo"):
        total += 28

    if cont_l.startswith("requisitos"):
        total += 28

    if cont_l.startswith("quienes pueden postular"):
        total += 32

    if intent and cont_l.startswith(intent):
        total += 30

    # -------------------------------------------------
    # BOOST POR MARCA DE SECCIÓN
    # -------------------------------------------------

    if "seccion:" in cont_l[:60]:
        total += 15

    # -------------------------------------------------
    # CONTROL SCORE
    # -------------------------------------------------

    total = min(total, 500)

    return total
