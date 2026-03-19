# chunking_juridico.py
import re
import hashlib
from backend.services.normalizador_pdf_juridico import normalizar_texto_juridico
from backend.services.preprocessing.chunking_service import subdividir_bloque
from backend.services.retrieval_text_utils import normalizar

# ==============================
# 1️⃣ DETECTOR DE SECCIONES BASES
# ==============================

SECCION_BASES = re.compile(
    r'(?:^|\n{2,})'
    r'\s*'
    r'(?:\d+[\.\-]?\s*)?'
    r'('
    r'RESOLUCI[OÓ]N\s+EXENT[AO]\s+N°?|'
    r'VISTOS|'
    r'CONSIDERANDO|'
    r'RESUELV[EO]|'
    r'ANTECEDENTES|'
    r'DEFINICIONES?|'
    r'T[ÍI]TULO\s+[IVXLCDM]+|'
    r'CAP[ÍI]TULO\s+[IVXLCDM]+|'
    r'T[ÓO]MESE\s+RAZ[ÓO]N|'
    r'OBJETIVO(?:\s+GENERAL)?(?:\s+DEL\s+CONCURSO)?|'
    r'RESULTADOS?\s+ESPERADOS?|'
    r'PLAZOS?\s+DE\s+POSTULACI[OÓ]N|'
    r'DURACI[OÓ]N\s+DEL\s+PROYECTO|'
    r'ELEGIBILIDAD|'
    r'ADMISIBILIDAD|'
    r'REQUISITOS?(?:\s+DE\s+POSTULACI[OÓ]N)?|'
    r'CONDICIONES?\s+DE\s+POSTULACI[OÓ]N|'
    r'PROCESO\s+DE\s+POSTULACI[OÓ]N|'
    r'MODALIDAD\s+DE\s+POSTULACI[OÓ]N|'
    r'[¿]?\s*QUI[ÉE]N(?:ES)?\s+PUEDEN\s+POSTULAR|'
    r'PODR[ÁA]N\s+POSTULAR|'
    r'BENEFICIARIOS?|'
    r'FINANCIAMIENTO(?:\s+DEL\s+PROYECTO)?|'
    r'MONTO\s+(?:M[ÁA]XIMO|DEL\s+SUBSIDIO)|'
    r'GASTOS?\s+FINANCIABLES|'
    r'CRITERIOS?\s+DE\s+EVALUACI[OÓ]N|'
    r'PROCESO\s+DE\s+EVALUACI[OÓ]N|'
    r'OBLIGACIONES?|'
    r'APRUEBANSE\s+LAS\s+BASES(?:\s+CONCURSALES)?|'
    r'APRUEBAN\s+LAS\s+BASES|'
    r'PLAZO\s+DE\s+EJECUCI[OÓ]N|'
    r'PLAZO\s+DE\s+ADJUDICACI[OÓ]N|'
    r'INFORMES?\s+T[ÉE]CNICOS?|'
    r'SEGUIMIENTO\s+DEL\s+PROYECTO|'
    r'ADJUDICACI[OÓ]N|'
    r'FORMALIZACI[OÓ]N|'
    r'RENDICI[OÓ]N\s+DE\s+CUENTAS|'
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

        bloques = []

        for p in posibles:

            if len(p) > 1200:
                bloques.extend(subdividir_bloque(p))
            else:
                bloques.append(p)

        posibles = [p.strip() for p in bloques if len(p.split()) > 10]

        if len(posibles) > 3:

            secciones = []

            MAX_CHARS = 1100
            OVERLAP = 150

            for p in posibles:

                if len(p) <= MAX_CHARS:
                    secciones.append(p)

                else:

                    i = 0
                    L = len(p)

                    while i < L:

                        sub = p[i:i+MAX_CHARS]

                        if len(sub.split()) > 12:
                            secciones.append(sub.strip())

                        i += MAX_CHARS - OVERLAP

            return secciones

        # ---------------------------------
        # 🔥 Fallback final por tamaño
        # ---------------------------------

        step = 1200
        overlap = 150

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

        header = normalizar_texto_juridico(header)
        contenido = texto[inicio_real:fin].strip()

        titulo = header.strip()

        bloque = f"SECCION: {titulo}\n\n{contenido}"

        # 🔎 detector tipo de chunk jurídico
        if re.search(r'\bCONSIDERANDO\b', contenido, re.I):
            tipo = "considerando"

        elif re.search(r'\bRESUELV[EO]\b', contenido, re.I):
            tipo = "resolucion"

        else:
            tipo = "seccion"

        # limpieza adicional
        bloque = re.sub(r'Página \d+ de \d+', '', bloque, flags=re.I)
        bloque = re.sub(r'https?://\S+', '', bloque)
        bloque = re.sub(r'\s+\n', '\n', bloque)

        MAX_LEN = 1200
        OVERLAP = 200
        MAX_ABSOLUTE = 2600

        if len(contenido) > MAX_ABSOLUTE:

            i = 0
            L = len(contenido)

            while i < L:

                sub = contenido[i:i+MAX_LEN]

                # cortar en salto de línea si es posible
                cut = sub.rfind("\n")

                if cut > MAX_LEN * 0.5:
                    sub = sub[:cut]

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

            for art in articulos:

                secciones_finales.append({
                    "contenido": art["contenido"],
                    "metadata": {
                        "seccion": "resolucion",
                        "articulo": art["articulo"],
                        "tipo_chunk": "articulo_resolucion"
                    }
                })

        else:
            secciones_finales.append(sec)

    # eliminar duplicados semánticos
    unicos = []
    vistos = set()

    for s in secciones_finales:

        if isinstance(s, dict):
            contenido = s["contenido"]
            meta = s["metadata"]
        else:
            contenido = s
            meta = {}

        key = hashlib.md5(contenido[:600].encode()).hexdigest()

        if key not in vistos:
            vistos.add(key)

            unicos.append({
                "contenido": contenido,
                "metadata": meta
            })

    unicos = [u for u in unicos if len(u["contenido"].split()) > 8]

    chunks_finales = []

    for u in unicos:

        # dividir chunks gigantes que hayan sobrevivido
        MAX_CHARS = 1100

        if len(u["contenido"]) <= MAX_CHARS:

            contenido = u["contenido"]

            # 🔎 detector tipo de chunk jurídico
            if re.search(r'\bCONSIDERANDO\b', contenido, re.I):
                tipo = "considerando"

            elif re.search(r'\bRESUELV[EO]\b', contenido, re.I):
                tipo = "resolucion"

            else:
                tipo = "seccion"

            seccion_detectada = extraer_nombre_seccion(contenido)

            tipo = detectar_tipo_chunk(contenido, seccion_detectada)

            chunks_finales.append({
                "contenido": contenido,
                "metadata": {
                    "seccion": seccion_detectada,
                    "titulo": "",
                    "articulo": None,
                    "tipo_chunk": tipo,  # 🔥 CLAVE
                    "char_length": len(u["contenido"]),
                    "has_resuelvo": bool(re.search(r'\bRESUELV[EO]\b', u["contenido"], re.I))
                }
            })

        else:

            step = MAX_CHARS
            overlap = 120
            i = 0

            while i < len(u["contenido"]):

                sub = u["contenido"][i:i+step]

                if len(sub.split()) > 12:

                    seccion_detectada = extraer_nombre_seccion(sub)

                    tipo = detectar_tipo_chunk(sub, seccion_detectada)

                    chunks_finales.append({
                        "contenido": sub,
                        "metadata": {
                            "seccion": seccion_detectada,
                            "titulo": "",
                            "articulo": None,
                            "tipo_chunk": tipo,  # 🔥 AQUÍ TAMBIÉN
                            "tokens": len(sub.split()),
                            "char_length": len(sub),
                            "has_resuelvo": bool(re.search(r'\bRESUELV[EO]\b', sub, re.I))
                        }
                    })

                i += step - overlap

    chunks_finales = sorted(
        chunks_finales,
        key=lambda x: (
            x["metadata"].get("seccion") or "",
            x["metadata"].get("tipo_chunk") or ""
        )
    )

    # ==============================
    # MERGE SEMÁNTICO SIMPLE
    # ==============================

    chunks_merged = []
    buffer = None

    for c in chunks_finales:

        if buffer is None:
            buffer = c
            continue

        if (
            buffer["metadata"]["seccion"] ==
            c["metadata"]["seccion"]
            and
            len(buffer["contenido"]) < 900
        ):
            buffer["contenido"] += "\n\n" + c["contenido"]

        else:
            chunks_merged.append(buffer)
            buffer = c

    if buffer:
        chunks_merged.append(buffer)

    return chunks_merged


# ==============================
# 2️⃣ DIVISIÓN DE RESUELVO
# ==============================

NUMERAL_BASES = re.compile(
    r"""
    \n\s*
    (
        # artículos clásicos
        ART[ÍI]?C?\.?\s*ULO?\s+\d+°?|
        ART\.?\s+\d+°?|
        ART\s+\d+°?|

        # artículos escritos
        ART[ÍI]?C?\.?\s*ULO?\s+
        (PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|
         S[EÉ]PTIMO|OCTAVO|NOVENO|D[EÉ]CIMO)

        |

        # numerales escritos
        PRIMERO\.|
        SEGUNDO\.|
        TERCERO\.|
        CUARTO\.|
        QUINTO\.|
        SEXTO\.|
        S[EÉ]PTIMO\.|
        OCTAVO\.|
        NOVENO\.|
        D[EÉ]CIMO\.

        |

        # numerales tipo lista
        \d+\.\-?
    )
    """,
    re.IGNORECASE | re.VERBOSE
)


def dividir_resuelvo_en_articulos(texto: str) -> list[str]:

    # normalizar variantes OCR comunes de ARTICULO
    texto = re.sub(r'\bART[IÍ]CULO\b', 'ARTÍCULO', texto, flags=re.I)
    texto = re.sub(r'\bARTICULO\b', 'ARTÍCULO', texto, flags=re.I)
    texto = re.sub(r'\bART\.\s*(\d+)', r'ARTÍCULO \1', texto, flags=re.I)
    texto = re.sub(r'\bART\s+(\d+)', r'ARTÍCULO \1', texto, flags=re.I)


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

            MAX_CHARS = 1100

            if len(texto_final) > MAX_CHARS:

                subchunks = [
                    texto_final[i:i+MAX_CHARS]
                    for i in range(0, len(texto_final), MAX_CHARS)
                ]

                for sub in subchunks:
                    if len(sub.split()) > 12:
                        chunks.append(sub)

            else:

                chunks.append({
                    "contenido": texto_final,
                    "articulo": m.group(1)
                })

    return chunks

def detectar_tipo_chunk(texto: str, seccion: str = "") -> str:

    if not texto:
        return "otro"

    t = normalizar(texto)
    s = normalizar(seccion or "")

    inicio = t[:400]  # 🔥 clave: priorizar inicio del chunk

    # --------------------------------------------------
    # 1. ARTÍCULO DE RESOLUCIÓN (máxima prioridad)
    # --------------------------------------------------

    if re.search(r'\bart[ií]culo\s+\d+', inicio):
        if any(x in t for x in ["resuelvo", "resuelve", "aprueba", "dispone"]):
            return "articulo_resolucion"

        # fallback: artículo genérico
        return "articulo"

    # --------------------------------------------------
    # 2. RESOLUCIÓN (parte resolutiva)
    # --------------------------------------------------

    if any(x in inicio for x in [
        "resuelvo",
        "resuelve",
        "se resuelve",
        "aprueba",
        "otorga",
        "concédase",
        "concedase",
        "dispónese",
        "disponese"
    ]):
        return "resolucion"

    # --------------------------------------------------
    # 3. CONSIDERANDOS (fundamentos)
    # --------------------------------------------------

    if (
        "considerando" in inicio
        or inicio.strip().startswith("que ")
        or "que," in inicio[:80]
    ):
        return "considerando"

    # --------------------------------------------------
    # 4. BASES DE CONCURSO
    # --------------------------------------------------

    if any(x in s for x in [
        "bases", "postulacion", "postulación",
        "requisitos", "evaluacion", "evaluación"
    ]):
        return "bases_concurso"

    if any(x in inicio for x in [
        "podran postular",
        "podrán postular",
        "requisitos de postulacion",
        "criterios de evaluacion",
        "criterios de evaluación",
        "admisibilidad",
        "seleccion de proyectos",
        "selección de proyectos"
    ]):
        return "bases_concurso"

    # --------------------------------------------------
    # 5. DEFINICIONES
    # --------------------------------------------------

    if any(x in inicio for x in [
        "se entendera por",
        "se entenderá por",
        "para efectos de",
        "definicion",
        "definición"
    ]):
        return "definicion"

    # --------------------------------------------------
    # 6. PROCEDIMIENTO
    # --------------------------------------------------

    if any(x in inicio for x in [
        "el proceso",
        "procedimiento",
        "etapas del proceso",
        "calendario",
        "plazo",
        "fechas"
    ]):
        return "procedimiento"

    # --------------------------------------------------
    # 7. FALLBACK INTELIGENTE POR SECCIÓN
    # --------------------------------------------------

    if "considerando" in s:
        return "considerando"

    if any(x in s for x in ["resolucion", "resuelve"]):
        return "resolucion"

    if "articulo" in s:
        return "articulo"

    if any(x in s for x in ["bases", "requisitos"]):
        return "bases_concurso"

    # --------------------------------------------------
    # DEFAULT
    # --------------------------------------------------

    return "otro"

def extraer_nombre_seccion(chunk: str):

    m = re.search(r'SECCION:\s*([A-ZÁÉÍÓÚÑ ]+)', chunk)

    if not m:
        return None

    nombre = m.group(1).strip().lower()

    mapa = {

        # objetivos
        "objetivo del concurso": "objetivo",
        "objetivo general del concurso": "objetivo",
        "objetivo general": "objetivo",
        "objetivo": "objetivo",

        # postulacion
        "quienes pueden postular": "postulacion",
        "podran postular": "postulacion",
        "postul": "postulacion",

        # requisitos
        "requisito": "requisitos",
        "condiciones": "requisitos",
        "certific": "requisitos",
        "autoriz": "requisitos",

        # financiamiento
        "financiamiento": "financiamiento",
        "recursos": "financiamiento",
        "monto": "financiamiento",

        # evaluacion
        "evalu": "evaluacion",
        "criterios": "evaluacion",

        # beneficiarios
        "benef": "beneficiarios",
        "investigador": "beneficiarios",

        # convocatoria
        "convocatoria": "convocatoria",

        # resolucion
        "aprueba": "aprobacion_bases",
        "aprueban": "aprobacion_bases",
        "apruebanse": "aprobacion_bases",
        "resuelvo": "resolucion",
        "resolucion": "resolucion",

        "anteced": "antecedentes",
        "defin": "definiciones",
        "duracion": "financiamiento",
        "plazo": "postulacion",
        "gastos": "financiamiento",
        "monto": "financiamiento",
        "subsidio": "financiamiento",
        "oblig": "obligaciones",
    }


    for k, v in mapa.items():
        if k in nombre:
            return v

    return nombre[:30]
