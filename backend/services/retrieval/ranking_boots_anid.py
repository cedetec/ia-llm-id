# ranking_boosts_anid.py
import re


def aplicar_boosts_anid(
    total,
    cont_l,
    inicio,
    seccion,
    intent,
    preg_benef
):

    # ---------------------------------------------
    # 🔒 NORMALIZACIÓN DEFENSIVA
    # ---------------------------------------------
    cont_l = cont_l or ""
    inicio = inicio or ""
    seccion = (seccion or "").lower()
    intent = (intent or "").lower()

    # Unificar intent
    if intent == "requisito":
        intent = "requisitos"

    # ---------------------------------------------
    # 🔥 BOOST POR ENCABEZADOS NUMERADOS ANID
    # ---------------------------------------------
    if re.search(r'\b1\s*[\.\-\)]?\s*(objetivo|finalidad)', cont_l):
        total += 18

    if re.search(r'\b2\s*[\.\-\)]?\s*(requisitos?)', cont_l):
        total += 28

    if re.search(r'\b3\s*[\.\-\)]?\s*(postul|benefici)', cont_l):
        total += 26

    if re.search(r'\b4\s*[\.\-\)]?\s*(evaluacion)', cont_l):
        total += 22

    if re.search(r'\b5\s*[\.\-\)]?\s*(financ)', cont_l):
        total += 20

    # ---------------------------------------------
    # 🎯 OBJETIVO
    # ---------------------------------------------
    if intent == "objetivo":

        if "objetivo del concurso" in inicio:
            total += 20

        if "objetivo del concurso" in cont_l:
            total += 15

        if cont_l.startswith("objetivo"):
            total += 15

        if "tiene por objetivo" in cont_l:
            total += 10

        if "objetivo" in seccion:
            total += 20
        else:
            total -= 5  # 🔥 penalización más suave

    # ---------------------------------------------
    # 📋 REQUISITOS
    # ---------------------------------------------
    elif intent == "requisitos":

        if "requisitos de postulacion" in inicio:
            total += 18

        if re.search(r'\b2\s*[\.\-\)]?\s*(requisitos?)', cont_l):
            total += 18

        if re.search(r'^\s*requisitos', cont_l):
            total += 12

        if "requisito" in seccion:
            total += 20
        else:
            total -= 4

    # ---------------------------------------------
    # 👥 POSTULACIÓN / BENEFICIARIOS
    # ---------------------------------------------
    elif intent in ["postulacion", "beneficiarios"]:

        # ❗ ruido típico
        if re.search(r'notificara|notificacion|resultado', cont_l):
            total -= 12

        if preg_benef:

            if re.search(r'quienes\s+pueden\s+postular', cont_l):
                total += 45

            elif re.search(r'podran\s+postular', cont_l):
                total += 35

            elif re.search(r'pueden\s+postular', cont_l):
                total += 25

        if re.search(r'\b(podran\s+postular|podra\s+postular|participar)\b', cont_l):
            total += 20

        if re.search(r'\b3\s*[\.\-\)]?\s*(postul|benefici)', cont_l):
            total += 15

        if re.search(r'^\s*(postulacion|postulantes)', cont_l):
            total += 10

        if "postul" in seccion:
            total += 18
        else:
            total -= 4

    # ---------------------------------------------
    # 📜 BASES / RESOLUCIONES
    # ---------------------------------------------
    elif intent in ["bases", "resolucion"]:

        if re.search(r'\b(resuelvo|aprueba[n]?|apruebase)\b', cont_l):
            total += 28

        if "aprueba las bases" in cont_l:
            total += 30

        if "bases del concurso" in cont_l:
            total += 10

        if seccion in ["beneficiarios", "evaluacion"]:
            total -= 6

    # ---------------------------------------------
    # ⚖️ BOOST RESOLUCIÓN
    # ---------------------------------------------
    if intent == "resolucion":

        if "resolucion exenta" in cont_l:
            total += 10

        if "resolucion n" in cont_l:
            total += 8

        if "resuelvo" in cont_l:
            total += 8

    # ---------------------------------------------
    # 🏛️ ENTIDADES
    # ---------------------------------------------
    if "agencia nacional de investigacion y desarrollo" in cont_l:
        total += 8

    if "investigador responsable" in cont_l:
        total += 6

    if "institucion patrocinante" in cont_l:
        total += 6

    # ---------------------------------------------
    # 📚 SECCIONES IMPORTANTES
    # ---------------------------------------------
    if "resolucion" in seccion:
        total += 8

    if "bases" in seccion:
        total += 6

    # ---------------------------------------------
    # 🎯 SECTION-AWARE (CLAVE)
    # ---------------------------------------------
    if intent:

        if seccion == intent:
            total += 30

        elif intent in seccion:
            total += 20

        elif seccion in ["bases", "convocatoria"]:
            total += 8

    if seccion and intent and seccion != intent:

        if seccion in ["evaluacion", "financiamiento"] and intent == "postulacion":
            total -= 10

        if seccion == "objetivo" and intent == "requisitos":
            total -= 8

        if seccion == "requisitos" and intent == "objetivo":
            total -= 6

    # ---------------------------------------------
    # 🧠 ENCABEZADOS DIRECTOS
    # ---------------------------------------------
    if cont_l.startswith("objetivo"):
        total += 18

    if cont_l.startswith("requisitos"):
        total += 18

    if cont_l.startswith("quienes pueden postular"):
        total += 22

    # ---------------------------------------------
    # 🏷️ MARCA DE SECCIÓN
    # ---------------------------------------------
    if "seccion:" in cont_l[:60]:
        total += 10

    # ---------------------------------------------
    # 🔒 CONTROL FINAL
    # ---------------------------------------------
    total = max(min(total, 400), -100)

    return total
