# backend/services/retrieval/citation_utils.py

import re
import unicodedata


def _normalizar(txt: str) -> str:

    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ascii", "ignore").decode("ascii")
    txt = txt.lower()

    # colapsar espacios
    txt = re.sub(r'\s+', ' ', txt)

    # corregir OCR tipo "o b j e t i v o"
    txt = re.sub(r'([a-z])\s+(?=[a-z])', r'\1', txt)

    return txt.strip()


def _extraer_palabras_clave(pregunta: str):

    palabras = re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)

    return [
        _normalizar(p)
        for p in palabras
    ]


def aplicar_filtro_cita(pregunta, texto, modo_documento_fijado):

    if not isinstance(texto, str):
        texto = str(texto or "")

    texto_norm = _normalizar(texto)

    palabras = _extraer_palabras_clave(pregunta)

    match = None

    # ----------------------------------------------------
    # 1️⃣ búsqueda por palabras entre comillas
    # ----------------------------------------------------

    if palabras:

        for palabra in palabras:

            for palabra in palabras:

                pat = re.escape(palabra)

                match = re.search(pat, texto_norm, re.IGNORECASE)

                if match:
                    break

    # ----------------------------------------------------
    # 2️⃣ patrones jurídicos si no hay palabra explícita
    # ----------------------------------------------------

    if not match:

        patrones = [

            # --------------------------------
            # OBJETIVO DEL CONCURSO (robusto)
            # --------------------------------

            r"objetivo.{0,20}concurso",
            r"objetivo.{0,40}finalidad",
            r"objetivo.{0,40}proposito",
            r"tiene\s+por\s+objetivo",
            r"tiene\s+por\s+finalidad",
            r"el\s+presente\s+concurso\s+tiene\s+por\s+objetivo",

            # --------------------------------
            # TITULOS DE SECCION
            # --------------------------------

            r"\d+\.\s*objetivo",
            r"\d+\.\s*objetivo\s+del\s+concurso",
            r"\d+\.\s*objetivo\s+general",

            r"\d+\.\s*beneficiarios",

            r"\d+\.\s*requisitos",
            r"\d+\.\s*requisitos\s+de\s+postulacion",

            r"\d+\.\s*postulacion",

            # --------------------------------
            # REQUISITOS
            # --------------------------------

            r"requisitos.{0,20}postulacion",
            r"requisitos.{0,40}postular",

            # --------------------------------
            # POSTULANTES
            # --------------------------------

            r"podran.{0,20}postular",
            r"quienes.{0,20}pueden.{0,20}postular",

            # --------------------------------
            # PROGRAMAS
            # --------------------------------

            r"\bidea\b",
            r"i\s*\+\s*d",
            r"investigacion.{0,20}desarrollo",
            r"f\s*o\s*n\s*d\s*e\s*c\s*y\s*t",

            # --------------------------------
            # BASES
            # --------------------------------

            r"aprue?b[a-z]*\s+las?\s+bases",
            r"aprue?b[a-z]*\s+las?\s+bases\s+del\s+concurso",
            r"aprue?b[a-z]*.{0,20}bases",
            r"resolucion\s+exenta",
            r"resolucion\s+n[°o]\s*\d+",
            r"res\.?\s*n[°o]\s*\d+",

            # --------------------------------
            # FECHAS
            # --------------------------------

            r"\b\d{1,2}/\d{1,2}/\d{4}\b"

            r"aprueban\s+las\s+bases",
            r"apruebese\s+las\s+bases",
            r"aprueban\s+las\s+bases\s+del\s+concurso",


            r"el\s+presente\s+concurso\s+tiene\s+por\s+objetivo",
            r"objetivo\s+general\s+del\s+concurso",
            r"el\s+objetivo\s+del\s+concurso",
            r"podran\s+postular",
            r"podran\s+presentar\s+proyectos",
            r"beneficiarios\s+del\s+concurso",

            r"el\s+objetivo\s+de\s+este\s+concurso",
            r"el\s+objetivo\s+del\s+concurso",
            r"objetivo\s+de\s+este\s+concurso",
            r"objetivo\s+general",
            r"podran\s+postular",
            r"postulacion\s+debera\s+ser",
            r"apruebanse\s+las\s+bases",
            r"apruebase\s+las\s+bases",
            r"aprueban\s+las\s+bases",
        ]

        for p in patrones:

            match = re.search(p, texto_norm)

            if match:
                break

    if not match:

        # si el documento está fijado,
        # devolver fragmento del texto en vez de descartarlo
        if modo_documento_fijado:

            texto = texto.strip()

            if len(texto) > 200:
                return texto[:200]

            return texto

        return texto

    # ----------------------------------------------------
    # 3️⃣ extraer frase alrededor
    # ----------------------------------------------------

    delimitadores = ['.', ';', ':', ',', '\n']

    inicio = -1

    for d in delimitadores:

        pos = texto.rfind(d, 0, match.start())

        if pos > inicio:
            inicio = pos

    fin_candidates = [
        texto.find('.', match.end()),
        texto.find(';', match.end()),
        texto.find(':', match.end()),
        texto.find('\n', match.end())
    ]

    fin_candidates = [f for f in fin_candidates if f != -1]

    fin = min(fin_candidates) if fin_candidates else len(texto)

    inicio = 0 if inicio == -1 else inicio + 1
    fin = len(texto) if fin == -1 else fin + 1

    frase = texto[inicio:fin].strip()

    if len(frase) < 40:

        # intentar ampliar alrededor del match
        start = max(0, match.start() - 120)
        end = min(len(texto), match.end() + 120)

        return texto[start:end].strip()

    return frase
