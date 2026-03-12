# chunking_juridico.py
import re
import hashlib
from backend.services.normalizador_pdf_juridico import normalizar_texto_juridico

# ==============================
# 1️⃣ DETECTOR DE SECCIONES BASES
# ==============================

SECCION_BASES = re.compile(
    r'(?:^|\n{2,})'
    r'\s*'
    r'(?:\d+[\.\-]?\s*)?'
    r'('
    r'RESOLUCI[OÓ]N\s+EXENTA\s+N°?|'
    r'RESOLUCI[OÓ]N\s+EXENTO\s+N°?|'
    r'VISTOS|'
    r'CONSIDERANDO|'
    r'RESUELVO|'
    r'T[ÍI]TULO\s+[IVXLCDM]+|'
    r'CAP[ÍI]TULO\s+[IVXLCDM]+|'
    r'T[ÓO]MESE\s+RAZ[ÓO]N|'
    r'OBJETIVO\s+DEL\s+CONCURSO|'
    r'OBJETIVO\s+GENERAL\s+DEL\s+CONCURSO|'
    r'QUIEN(?:ES)?\s+PUEDEN\s+POSTULAR|'
    r'PODR[ÁA]N\s+POSTULAR|'
    r'REQUISITOS\s+DE\s+POSTULACI[OÓ]N|'
    r'CONDICIONES\s+DE\s+POSTULACI[OÓ]N|'
    r'PROCESO\s+DE\s+POSTULACI[OÓ]N|'
    r'FINANCIAMIENTO\s+DEL\s+PROYECTO|'
    r'CRITERIOS?\s+DE\s+EVALUACI[OÓ]N|'
    r'BENEFICIARIOS?|'
    r'APRUEBANSE\s+LAS\s+BASES\s+CONCURSALES|'
    r'APRUEBANSE\s+LAS\s+BASES|'
    r'APRUEBAN\s+LAS\s+BASES'
    r')\b',
    re.IGNORECASE | re.MULTILINE
)

def reconstruir_secciones(fragmentos: list[str]) -> list[str]:

    fragmentos = [
        normalizar_texto_juridico(f)
        for f in fragmentos
        if f and len(f.strip()) > 30
    ]

    texto = "\n".join(fragmentos)

    # corregir numerales OCR rotos
    # eliminar numerales excesivos tipo 1.1.1
    texto = re.sub(r'\b\d+\.\d+\.\d+\b', '', texto)
    texto = re.sub(r'(\d)\s+\.', r'\1.', texto)
    texto = re.sub(r'\.\s+\.', '.', texto)

    # 3️⃣ limpiar saltos excesivos
    texto = re.sub(r'\n{4,}', '\n\n', texto)

    # 4️⃣ detectar encabezados jurídicos
    matches = list(SECCION_BASES.finditer(texto))

    if not matches:

        # 🔥 Intento estructural secundario
        posibles = re.split(
            r'\n(?=\s*(?:'
            r'\d+[\.\-]?\s+|'
            r'art[ií]culo\s+\d+|'
            r't[ií]tulo\s+[ivxlcdm]+|'
            r'cap[ií]tulo\s+\d+|'
            r'antecedentes|'
            r'definiciones?|'
            r'resultados?\s+esperados?|'
            r'objeti?vo?s?|'
            r'requisitos?|'
            r'quien(?:es)?\s+pueden\s+postular|'
            r'financiamiento|'
            r'evaluaci[oó]n|'
            r'resuelvo|'
            r'considerando|'
            r'resoluci[oó]n|'
            r't[oó]mese\s+raz[oó]n'
            r')\b)',
            texto,
            flags=re.IGNORECASE
        )

        posibles = [p.strip() for p in posibles if len(p.split()) > 10]

        if len(posibles) > 3:
            return posibles

        # ---------------------------------
        # 🔥 Fallback final por tamaño
        # ---------------------------------

        step = 4000
        overlap = 400

        chunks = []
        i = 0
        L = len(texto)

        while i < L:

            chunk = texto[i:i+step]

            if len(chunk.split()) > 8:
                chunks.append(chunk.strip())

            i += step - overlap


        # ---------------------------------
        # 🔧 FORZAR MÍNIMO CHUNKS
        # ---------------------------------

        if len(chunks) == 1 and len(texto) > 1200:

            mitad = len(texto) // 2

            chunks = [
                texto[:mitad].strip(),
                texto[mitad:].strip()
            ]

        if len(chunks) == 2 and len(texto) > 2000:

            tercio = len(texto) // 3

            chunks = [
                texto[:tercio].strip(),
                texto[tercio:2*tercio].strip(),
                texto[2*tercio:].strip()
            ]

        return chunks

    secciones = []

    for i, m in enumerate(matches):

        inicio = m.start()

        if i + 1 < len(matches):
            fin = matches[i + 1].start()
        else:
            fin = len(texto)

        inicio_real = inicio
        header = m.group(1).strip()
        contenido = texto[inicio_real:fin].strip()

        bloque = f"SECCION: {header}\n\n{contenido}"

        # limpieza adicional
        bloque = re.sub(r'Página \d+ de \d+', '', bloque, flags=re.I)
        bloque = re.sub(r'https?://\S+', '', bloque)
        bloque = re.sub(r'\s+\n', '\n', bloque)

        MAX_LEN = 1400
        OVERLAP = 200

        if len(contenido) > MAX_LEN * 1.2:

            i = 0
            L = len(contenido)

            while i < L:

                sub = contenido[i:i+MAX_LEN]
                sub = f"SECCION: {header}\n\n{sub}"

                if len(sub.split()) > 15:
                    secciones.append(sub.strip())

                i += MAX_LEN - OVERLAP

        else:
            if len(bloque.split()) > 10:
                secciones.append(bloque.strip())

    # ✅ FUERA DEL FOR
    secciones_finales = []

    for sec in secciones:
        articulos = dividir_resuelvo_en_articulos(sec)

        if articulos:
            secciones_finales.extend(articulos)
        else:
            secciones_finales.append(sec)

    # eliminar duplicados semánticos
    unicos = []
    vistos = set()

    for s in secciones_finales:
        key = hashlib.md5(s[:600].encode()).hexdigest()
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)

    unicos = [u for u in unicos if len(u.split()) > 8]
    return unicos


# ==============================
# 2️⃣ DIVISIÓN DE RESUELVO
# ==============================

NUMERAL_BASES = re.compile(
    r"""
    \n\s*
    (
        ART[ÍI]CULO\s+\d+°?|
        PRIMERO\.|
        SEGUNDO\.|
        TERCERO\.|
        CUARTO\.|
        QUINTO\.|
        SEXTO\.|
        SÉPTIMO\.|
        OCTAVO\.|
        NOVENO\.|
        DÉCIMO\.|
        \d+\.\-?       # 1.- 2.- 3.-
    )
    """,
    re.IGNORECASE | re.VERBOSE
)

def dividir_resuelvo_en_articulos(texto: str) -> list[str]:

    if not re.search(r'\bRESUELV[EO]\b', texto, re.I):
        return []

    encabezado = "RESUELVO:\n"

    chunks = []

    matches = list(NUMERAL_BASES.finditer(texto))

    matches = sorted(matches, key=lambda m: m.start())

    for i, m in enumerate(matches):

        inicio = m.start()

        if i + 1 < len(matches):
            fin = matches[i + 1].start()
        else:
            fin = len(texto)

        bloque = texto[inicio:fin].strip()

        bloque = re.sub(r'\s+\n', '\n', bloque)
        bloque = re.sub(r'\n{3,}', '\n\n', bloque)

        texto_final = encabezado + bloque

        if len(texto_final.split()) > 40:
            chunks.append(texto_final)

    return chunks

def extraer_nombre_seccion(chunk: str):

    m = re.search(r'SECCION:\s*([A-ZÁÉÍÓÚÑ ]+)', chunk)

    if not m:
        return None

    nombre = m.group(1).strip().lower()

    mapa = {
        "objetivo del concurso": "objetivo_concurso",
        "objetivo general del concurso": "objetivo_concurso",
        "objetivo": "objetivo",
        "requisito": "requisitos",
        "postul": "postulacion",
        "financ": "financiamiento",
        "certific": "requisitos",
        "autoriz": "requisitos",
        "evalu": "evaluacion",
        "benef": "beneficiarios",
        "convocatoria": "convocatoria",

        "aprueba": "aprobacion_bases",
        "aprueban": "aprobacion_bases",
        "apruebanse": "aprobacion_bases",
        "resuelvo": "resolucion",
        "resolucion": "resolucion",
    }

    for k, v in mapa.items():
        if k in nombre:
            return v

    return nombre[:30]
