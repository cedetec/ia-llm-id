#citation_utils.py

import re
import unicodedata


# --------------------------------------------------
# 🔧 Normalización eficiente
# --------------------------------------------------

def _normalizar(txt: str) -> str:
    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ascii", "ignore").decode("ascii").lower()

    txt = re.sub(r'\s+', ' ', txt)
    txt = re.sub(r'([a-z])\s+(?=[a-z])', r'\1', txt)

    return txt.strip()


# --------------------------------------------------
# 🔍 Extraer palabras entre comillas
# --------------------------------------------------

def _extraer_palabras_clave(pregunta: str):
    return [
        _normalizar(p)
        for p in re.findall(r'[\"“”]([^\"“”]+)[\"“”]', pregunta)
    ]


# --------------------------------------------------
# 🧠 Patrones compilados (más eficiente)
# --------------------------------------------------

PATRONES_CLAVE = re.compile(
    r"""
    objetivo.{0,40}(concurso|finalidad|proposito)|
    tiene\s+por\s+(objetivo|finalidad)|
    \d+\.\s*(objetivo|requisitos|postulacion|beneficiarios)|
    podran.{0,20}postular|
    aprueb[a-z]*\s+las?\s+bases|
    resolucion\s+(exenta|n)|
    res\.?\s*n|
    \b\d{1,2}/\d{1,2}/\d{4}\b|
    fondecyt|idea|i\s*\+\s*d
    """,
    re.VERBOSE
)

PATRON_RESOLUTIVO = re.compile(r'resuelv|aprueb')
PATRON_RESOLUCION = re.compile(r'resolucion|res\.')


# --------------------------------------------------
# 🎯 FUNCIÓN PRINCIPAL
# --------------------------------------------------

def aplicar_filtro_cita(pregunta, texto, modo_documento_fijado):

    if not isinstance(texto, str):
        texto = str(texto or "")

    texto_norm = _normalizar(texto)
    palabras = _extraer_palabras_clave(pregunta)

    # --------------------------------------------------
    # 🔍 MATCH PRINCIPAL
    # --------------------------------------------------

    match = None

    # 1. búsqueda por comillas
    for palabra in palabras:
        match = re.search(re.escape(palabra), texto_norm)
        if match:
            break

    # 2. fallback: patrones
    if not match:
        match = PATRONES_CLAVE.search(texto_norm)

    # 3. fallback jurídico básico
    if not match:
        match = PATRON_RESOLUCION.search(texto_norm)

    # --------------------------------------------------
    # 🚨 fallback si no hay nada
    # --------------------------------------------------

    if not match:
        if modo_documento_fijado:
            return texto.strip()[:200]
        return texto

    # --------------------------------------------------
    # ✂️ dividir en frases
    # --------------------------------------------------

    frases = re.split(r'(?<=[\.\!\?])\s+', texto)

    mejor_score = -1
    mejor_frase = None

    frases_resolutivas = []

    for f in frases:

        if not f.strip():
            continue

        f_norm = _normalizar(f)
        score = 0

        # ----------------------------------
        # 🎯 coincidencias fuertes
        # ----------------------------------

        if palabras and any(p in f_norm for p in palabras):
            score += 12

        if match:
            fragmento = texto_norm[match.start():match.end()]
            if fragmento and fragmento in f_norm:
                score += 10

        # ----------------------------------
        # ⚖️ peso jurídico
        # ----------------------------------

        if PATRON_RESOLUTIVO.search(f_norm):
            score += 25
            frases_resolutivas.append(f)

        elif PATRON_RESOLUCION.search(f_norm):
            score += 10

        # ----------------------------------
        # 📊 contexto útil
        # ----------------------------------

        if re.search(r'fondecyt|idea|i\+d', f_norm):
            score += 5

        if len(f.split()) > 8:
            score += 2

        # ----------------------------------
        # 🏆 mejor frase
        # ----------------------------------

        if score > mejor_score:
            mejor_score = score
            mejor_frase = f

    # --------------------------------------------------
    # 🔥 PRIORIDAD ABSOLUTA: resolutivas
    # --------------------------------------------------

    if frases_resolutivas:

        for f in frases_resolutivas:
            if re.search(r'aprueb.*bases', _normalizar(f)):
                return f.strip()

        return max(frases_resolutivas, key=lambda x: len(x.split())).strip()

    # --------------------------------------------------
    # fallback mejor frase
    # --------------------------------------------------

    respuesta = mejor_frase.strip() if mejor_frase else texto[:200]

    # --------------------------------------------------
    # 🧹 validaciones finales
    # --------------------------------------------------

    if len(respuesta.split()) < 6:
        respuesta = max(frases, key=lambda x: len(x.split()), default=texto[:200])

    if respuesta.count('/') > 3:
        respuesta = texto[:200]

    if len(respuesta) > 300:
        respuesta = respuesta[:300]

    return respuesta
