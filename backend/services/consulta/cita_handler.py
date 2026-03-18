# cita_handler.py

from backend.services.consulta_extract_frases import (
    extraer_frase_con_patron,
    recortar_frase_limpia,
)

from backend.services.consulta_utils_text import score_semantico

import re
import unicodedata

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def limpiar_texto_final(texto):
    # eliminar caracteres raros
    texto = re.sub(r'[^A-Za-z0-9áéíóúÁÉÍÓÚñÑ.,;:()/%\- ]+', ' ', texto)

    # eliminar palabras basura tipo OCR (TODO MAYÚSCULA sin sentido)
    texto = re.sub(r'\b[A-Z]{6,}\b', '', texto)

    # normalizar espacios
    texto = re.sub(r'\s+', ' ', texto)

        # 🔥 arreglar I+D roto
    texto = re.sub(r'I\s+D', 'I+D', texto)

    # 🔥 eliminar barras raras
    texto = re.sub(r'/+', ' ', texto)

    # 🔥 eliminar repeticiones raras tipo "DE / DE"
    texto = re.sub(r'\b(DE\s+){2,}', 'DE ', texto)

    return texto.strip()

def manejar_cita(pregunta_low, contexto, pregunta):

    # -------------------------------------------------
    # VALIDACIÓN INICIAL (FIX BUG dict.split)
    # -------------------------------------------------

    if isinstance(contexto, dict):
        contexto = (
            contexto.get("contenido")
            or contexto.get("texto")
            or ""
        )

    if not isinstance(contexto, str) or not contexto.strip():
        return None

    patrones = []

    # 🔥 BOOST por metadata (CRÍTICO)
    if "resolucion" in str(contexto).lower():
        patrones += ["apruebase", "resuelvo", "aprueba"]

    # -------------------------------------------------
    # LIMPIEZA CONTEXTO (OCR + ruido científico)
    # -------------------------------------------------

    contexto = re.split(
        r'JOURNAL|SCOPUS|IMPACT FACTOR|PRODUCTIVIDAD CIENTIFICA',
        contexto,
        flags=re.I
    )[0]

    # normalización OCR
    contexto = re.sub(
        r'r\s*e\s*s\s*o\s*l\s*u\s*c\s*i\s*o\s*n',
        'resolucion',
        contexto,
        flags=re.I
    )

    contexto = re.sub(r'\bresoluci[oó]n\b', 'resolucion', contexto, flags=re.I)

    # 🔥 normalizar variantes de resolución
    contexto = re.sub(r'res\s*\.\s*n', 'resolucion n', contexto, flags=re.I)
    contexto = re.sub(r'res\s*\.', 'resolucion', contexto, flags=re.I)
    contexto = re.sub(r'n[°º]\s*', 'n ', contexto, flags=re.I)

    # abreviaturas
    contexto = re.sub(r'\bres\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)
    contexto = re.sub(r'\bresol\.\s*exenta\b', 'resolucion exenta', contexto, flags=re.I)

    # limpieza general
    contexto = re.sub(r'\n+', '\n', contexto)
    contexto = re.sub(r'\s{2,}', ' ', contexto)

    contexto = re.sub(r'\bI\s+D\b', 'I+D', contexto)

    # -------------------------------------------------
    # PATRONES SEGÚN INTENCIÓN
    # -------------------------------------------------

    if "resol" in pregunta_low:
        patrones += [
            "resolucion",
            "resolucion exenta",
            "resuelvo",
            "resuelve",
            "rex",
            "res n",
            "res.",
            "resol.",
        ]

    if "aprueb" in pregunta_low or "bases" in pregunta_low:
        patrones += [
            "apruebase",
            "apruebanse",
            "aprueba",
            "aprueban",
            "se aprueban",
            "aprueban las bases",
            "apruebase las bases",
            "aprueba bases",
            "aprueba las bases",
            "bases del concurso",
            "bases concursales",
        ]

    if "objetivo" in pregunta_low:
        patrones += [
            "objetivo",
            "objetivo del concurso",
            "objetivo general",
            "tiene por objetivo",
            "tiene como objetivo",
        ]

    if "postular" in pregunta_low or "requisito" in pregunta_low:
        patrones += [
            "requisitos",
            "requisitos de postulacion",
            "pueden postular",
            "podran postular",
        ]

    patrones_norm = [p.lower() for p in patrones]

    # -------------------------------------------------
    # DIVIDIR CONTEXTO (MEJORADO)
    # -------------------------------------------------

    chunks = re.split(r'\[Fragmento \d+\]', contexto)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 40]

    chunks = chunks[:5]  # 🔥 SOLO LOS MEJORES

    if not chunks:
        return None

    frases = []

    # 🔥 PRIORIZAR EL MEJOR CHUNK (CRÍTICO)
    top_chunk = chunks[0]

    # 🔥 FORZAR inclusión del mejor chunk SI es resolutivo
    top_chunk_norm = normalizar(top_chunk)

    if any(x in top_chunk_norm for x in ["apruebase", "aprueba", "resuelve"]):
        frases.insert(0, top_chunk.strip())

    if (
        any(x in top_chunk.lower() for x in ["aprueba", "apruebase", "resuelve", "resolucion"])
        and len(top_chunk.split()) < 120
    ):
        frases.insert(0, top_chunk.strip())

    # -------------------------------------------------
    # EXTRACCIÓN DE FRASES
    # -------------------------------------------------

    for chunk in chunks:

        chunk_norm = normalizar(chunk)

        # 🔥 evitar headers/ruido institucional (a nivel chunk)
        if all(x in chunk.lower() for x in [
            "agencia nacional",
            "contralor"
        ]):
            continue

        # 🔥 EXTRAER FRASES DIRECTAS DEL CHUNK COMPLETO (MUY IMPORTANTE)
        if any(x in chunk_norm for x in ["apruebase", "aprueba", "resuelve", "resolucion", "resolucion exenta"]):
            if len(chunk.split()) < 120:
                frases.append(chunk.strip())

        # split más inteligente
        subfrases = re.split(r'(?<=[\.\!\?])\s+|\n+|(?=APRUEBA|APRUÉBASE)', chunk)


        for sub in subfrases:

            sub = sub.strip()

            sub_norm = normalizar(sub)

            if len(sub) < 10:
                continue

            # 🔥 evitar basura OCR
            if re.search(r'\b[A-Z]{8,}\b', sub):
                continue

            # 🔥 evitar fragmentos raros
            if sub.count(",") > 12:
                continue

            matched = False

            for pat in patrones:
                if pat in sub_norm:
                    frases.append(sub)
                    matched = True
                    break

            # 🔥 permitir frases relevantes aunque no tengan patrón exacto
            if not matched and len(sub) > 80:
                if any(x in sub.lower() for x in [
                    "objetivo", "aprueba", "resuelve",
                    "resolucion", "bases", "concurso"
                ]):
                    frases.append(sub)

    # -------------------------------------------------
    # POST PROCESO FRASES (FUERA DEL LOOP 🔥)
    # -------------------------------------------------

    frases = list(dict.fromkeys(frases))

    # 🔥 eliminar frases con ruido jurídico típico OCR
    frases = [
        f for f in frases
        if not re.search(r'JUR[IÍ]DICO|IVPL|JPIC|[A-Z]{6,}', f)
    ]

    if not frases:
        return None

    # -------------------------------------------------
    # FILTROS (ARREGLADO 🔥)
    # -------------------------------------------------

    frases_filtradas = []

    for f in frases:

        f_norm = normalizar(f)

        # 🔥 NUNCA eliminar resolutivos reales
        if any(x in f_norm for x in ["resuelv", "aprueb"]):
            frases_filtradas.append(f)
            continue

        # filtro normal
        if any(p in f_norm for p in patrones_norm) \
        or any(x in f_norm for x in ["resolucion", "objetivo"]) \
        or (15 < len(f.split()) < 80):  # 🔥 FIX longitud

            frases_filtradas.append(f)

    frases = frases_filtradas

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    print("\nCANDIDATOS CITA:")
    for f in frases[:5]:
        print("-", f[:150])

    # 🔥 usar solo top chunks (opcional pero potente)
    frases = frases[:50]

    # -------------------------------------------------
    # SCORING MEJORADO
    # -------------------------------------------------

    # 🔥 detectar si el contexto viene de resolución
    chunk_es_resolutivo = "resolucion" in str(contexto).lower()

    def score_total(f):

        f_low = normalizar(f)

        s_sem = score_semantico(f, pregunta)

        s_pat = sum(
            1 for p in patrones_norm
            if p in f_low
        )

        s_legal = 0

        # 🔥 boost por metadata estructural
        if chunk_es_resolutivo:
            s_legal += 5

        # 🔥 frases realmente buenas
        if "apruebase" in f_low or "se aprueba" in f_low:
            s_legal += 10

        if "resuelvo" in f_low or "resuelve" in f_low:
            s_legal += 5

        # 🔥 BOOST OBJETIVO
        if "objetivo" in f_low:
            s_legal += 1.5

        # 🔥 PENALIZAR FRASES BASURA DE CONTEXTO
        if "y en las resoluciones" in f_low:
            s_legal -= 1

        if "objetivo" in pregunta.lower() and "objetivo" in f_low:
            s_sem += 2

        if "aprueba" in pregunta.lower() and "aprueba" in f_low:
            s_legal += 10

        if "aprueba bases" in f_low or "apruebase las bases" in f_low:
            s_legal += 10

        if f_low.startswith("apruebase"):
            s_legal += 10
        
        # 🔥 boost brutal para resoluciones correctas
        if "apruebase las bases" in f_low:
            s_legal += 10

        if "objetivo del concurso" in f_low:
            s_legal += 2.5

        if "podran postular" in f_low or "pueden postular" in f_low:
            s_legal += 0.8

        if "resolucion" in f_low:
            s_legal += 2

        if "resolucion exenta" in f_low:
            s_legal += 3

        if "resuelvo" in f_low:
            s_legal += 5

        # 🔥 penalizar basura OCR
        if re.search(r'\b[A-Z]{8,}\b', f):
            s_legal -= 1.5

        # 🔥 PRIORIDAD ABSOLUTA AL TOP CHUNK
        if f.strip() == top_chunk.strip():
            s_legal += 10

        # 🔥 MEGA BOOST si la frase parte correctamente
        if f_low.startswith("apruebase") or f_low.startswith("aprueba"):
            s_legal += 6

        # penalizar frases largas
        if len(f) > 400:
            s_legal -= 1

        # 🔥 premiar frases claras y directas
        if len(f.split()) < 20 and any(x in f_low for x in ["objetivo", "aprueba", "resuelve"]):
            s_legal += 1

        # 🔥 PRIORIDAD REAL A RESOLUCIONES
        if any(x in f_low for x in ["apruebase", "aprueba", "resuelve"]):
            s_legal += 15

        # 🔥 penalizar frases sin keywords fuertes
        if not any(p in f_low for p in patrones_norm):
            s_legal -= 1

        # 🔥 penalizar frases raras muy cortas
        if len(f.split()) < 8:
            s_legal -= 0.5

        # longitud óptima
        s_len = min(len(f) / 300, 1)

        return (s_sem * 0.3) + (s_pat * 0.3) + (s_len * 0.1) + s_legal


    # -------------------------------------------------
    # SELECCIÓN MEJOR FRASE
    # -------------------------------------------------

    print("\nTOP FRASES RANKEADAS:")
    for f in sorted(frases, key=score_total, reverse=True)[:5]:
        print(score_total(f), "->", f[:120])

    mejor = None

    # 🔥 prioridad máxima: frases resolutivas correctas
    for f in frases:
        f_norm = normalizar(f)

        if (
            "apruebase las bases" in f_norm
            or f_norm.startswith("apruebase")
            or f_norm.startswith("aprueba")
        ):
            mejor = f
            break

    # fallback
    if not mejor:
        mejor = max(frases, key=score_total)

    top_chunk_norm = normalizar(top_chunk)

    if any(x in top_chunk_norm for x in ["apruebase", "aprueba", "resuelve"]) \
        and len(top_chunk.split()) < 120 \
        and score_total(top_chunk) > score_total(mejor):

            mejor = top_chunk

    # -------------------------------------------------
    # FALLBACK SIMPLE
    # -------------------------------------------------

    if score_total(mejor) < 0.05 and mejor != top_chunk:
        mejor = frases[0]

    # -------------------------------------------------
    # 🔥 FALLBACK INTELIGENTE (ANTES DE LIMPIAR)
    # -------------------------------------------------

    if not any(p in normalizar(mejor) for p in patrones_norm):
        for f in frases:
            if any(p in normalizar(f) for p in patrones_norm):
                mejor = f
                break

    # 🔥 FILTRO FINAL DE CALIDAD (CRÍTICO)
    if not any(p in normalizar(mejor) for p in patrones_norm):

        if not any(x in normalizar(mejor) for x in ["aprueb", "resuelv", "resolucion", "objetivo"]):

            # 🔥 fallback suave en vez de matar
            if len(mejor.split()) < 6:
                return None
        # -------------------------------------------------
    # LIMPIEZA FINAL
    # -------------------------------------------------

    # cortar oración
    match = re.search(r'(.{40,}?\.)', mejor)
    if match:
        respuesta = match.group(1)
    else:
        respuesta = mejor

    # 🔥 unir números de resolución cortados
    if re.match(r'^resolucion\s+n\.?$', normalizar(respuesta)):
        for f in frases:
            if re.search(r'\d{3,}', f):
                respuesta = f
                break

    # 🔥 evitar frases demasiado cortas
    if len(respuesta.split()) < 6:
        respuesta = mejor

    # 🔥 SOLO cortar si es ruido, NO resoluciones
    if ":" in respuesta and not re.search(r'resuelv|aprueb', normalizar(respuesta)):
        respuesta = respuesta.split(":")[0]

    # eliminar ruido estructural
    respuesta = re.split(r'JURÍDICO|Inicio de trascripción', respuesta, flags=re.I)[0]

    # eliminar colas
    respuesta = re.sub(r'(Inicio de.*|JURÍDICO.*)$', '', respuesta, flags=re.I)

    # limpiar texto
    respuesta = limpiar_texto_final(respuesta)

    # limpiar guiones
    respuesta = re.sub(r'^[-–]\s*', '', respuesta)

    # cortar por múltiples frases
    if " - " in respuesta:
        respuesta = respuesta.split(" - ")[0]

    # limitar largo
    if len(respuesta) > 300:
        respuesta = respuesta[:300].rsplit(' ', 1)[0]

    # asegurar punto final
    if not respuesta.endswith('.'):
        respuesta += '.'

    # -------------------------------------------------
    # MÉTRICAS (DESPUÉS DE TODO)
    # -------------------------------------------------

    score_sem = score_semantico(mejor, pregunta)

    score_lex = sum(
        1 for t in pregunta_low.split()
        if t in mejor.lower()
    )

    respuesta = re.sub(r'\s+', ' ', respuesta)
    respuesta = re.sub(r'([a-z])([A-Z])', r'\1 \2', respuesta)

    # 🔥 capitalizar inicio
    if respuesta:
        respuesta = respuesta[0].upper() + respuesta[1:]

    print("\nCHUNKS REALES:")
    for c in chunks[:3]:
        print("----")
        print(c[:200])

    # 🔥 limpiar guiones iniciales
    respuesta = re.sub(r'^[-–]\s*', '', respuesta)

    # 🔥 evitar frases con mucho ruido OCR
    if respuesta.count('/') > 5:
        return None

    # 🔥 evitar respuestas vacías o basura
    if not respuesta or len(respuesta.strip()) < 10:
        return None

    # 🔥 evitar frases incompletas de resolución
    if re.match(r'^resolucion\s+n\.?$', normalizar(respuesta)):
        return None

    return {
        "respuesta": respuesta.strip(),
        "fuente": "RAG (extracción directa)",
        "score_semantico": round(score_sem, 3),
        "score_lexico": score_lex,
    }
