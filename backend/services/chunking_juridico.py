# chunking_juridico.py

import re
import hashlib
from backend.services.normalizador_pdf_juridico import normalizar_texto_juridico
from backend.services.retrieval_text_utils import normalizar, safe_split


# ==========================================
# 🔥 LIMPIEZA OCR (CRÍTICO)
# ==========================================

def limpiar_texto(texto: str) -> str:
    texto = normalizar_texto_juridico(texto)
    t = texto.lower()

    palabras = safe_split(t)
    if not palabras:
        return ""

    # ✅ filtro suave (no destructivo)
    validas = [
        p for p in palabras
        if sum(c in "aeiouáéíóú" for c in p) >= 1
        or p.isupper()
        or any(c.isdigit() for c in p)
    ]

    # 🔥 bajar umbral (antes 60%)
    if len(validas) < len(palabras) * 0.15:
        return ""

    # ❌ SOLO si es MUY extremo
    if len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{7,}', t)) >= 5:
        return ""

    # limpieza normal
    texto = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ.,;:()/%\s-]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()


# ==========================================
# 🔥 SPLIT JURÍDICO PRINCIPAL
# ==========================================

SECCIONES = re.compile(
    r'\b('
    r'VISTOS|CONSIDERANDO|RESUELV[EO]|'
    r'\d+\.\s*(OBJETIVO|FINALIDAD|PROPOSITO)|'
    r'\d+\.\s*(REQUISITOS?)|'
    r'\d+\.\s*(QUIENES PUEDEN POSTULAR|BENEFICIARIOS?)|'
    r'\d+\.\s*(FINANCIAMIENTO)|'
    r'\d+\.\s*(DURACION|PLAZO)|'
    r'\d+\.\s*(EVALUACION)'
    r')\b',
    re.IGNORECASE
)


# ==========================================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================================

def chunkear_documento(fragmentos: list[str]):

    # 1️⃣ unir texto
    texto = "\n".join([f for f in fragmentos if f and len(f.strip()) > 20])
    texto = limpiar_texto(texto)

    # ==========================================
    # 🔬 DEBUG PROFUNDO
    # ==========================================

    print("\n==============================")
    print("📄 DEBUG DOCUMENTO")
    print("LARGO ORIGINAL:", len(texto))

    if not texto.strip():
        print("❌ TEXTO VACÍO DESPUÉS DE LIMPIEZA")
        return []

    print("PALABRAS:", len(safe_split(texto)))
    print("PREVIEW:", texto[:300])

    if not texto or len(safe_split(texto)) < 25:
        # ⚠️ fallback en vez de matar documento
        return fallback_chunking(texto)

    # 2️⃣ dividir por secciones jurídicas
    partes = re.split(SECCIONES, texto)

    print("SECCIONES DETECTADAS:", len(partes))

    chunks = []

    # 3️⃣ reconstrucción estructurada
    for i in range(1, len(partes), 2):

        if len(chunks) > 220:
            break

        titulo = partes[i]
        contenido = partes[i+1] if i+1 < len(partes) else ""

        bloque = f"{titulo} {contenido}".strip()

        print("\n--- BLOQUE ---")
        print("TITULO:", titulo)
        print("LARGO BLOQUE:", len(safe_split(bloque)))

        # filtros anti ruido
        if len(bloque) < 80:
            continue

        if len(safe_split(bloque)) < 30:
            continue

        # metadata base
        meta = {
            "seccion": detectar_tipo_chunk(titulo),
            "tipo_chunk": detectar_tipo_chunk(bloque),
            "char_length": len(bloque),
            "es_resolutivo": bool(re.search(r'resuelv', titulo, re.I))
        }

        # dividir si es muy grande
        subchunks = dividir_si_grande(bloque)

        # 🔥 limitar subchunks por bloque (EVITA EXPLOSIÓN DE CHUNKS)
        if len(subchunks) > 6:
            subchunks = subchunks[:6]

        # límite por documento (MUY IMPORTANTE)
        if len(chunks) > 220:
            break

        print("SUBCHUNKS GENERADOS:", len(subchunks))

        for sub in subchunks:

            if len(chunks) > 220:
                break

            # ❌ evitar OCR residual
            if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', sub.lower()):
                continue

            if len(safe_split(sub)) < 15:
                continue

            tipo_real = detectar_tipo_chunk(sub)  # 🔥 FIX CLAVE

            # 🔥 DESCARTE CRÍTICO (AQUÍ)
            if tipo_real == "general" and len(safe_split(sub)) < 25:
                continue

            meta_sub = {
                **meta,
                "tipo_chunk": tipo_real
            }

            chunks.append({
                "contenido": sub.strip(),
                "metadata": meta_sub
            })

    print("CHUNKS ANTES DE FALLBACK:", len(chunks))

    # 4️⃣ fallback si no detecta secciones
    if not chunks:
        chunks = fallback_chunking(texto)

    # 🔥 límite global definitivo
    if len(chunks) > 220:
        chunks = chunks[:220]

    print("✅ CHUNKS FINALES:", len(chunks))

    # 5️⃣ eliminar duplicados
    return eliminar_duplicados(chunks)


# ==========================================
# 🔥 DIVISIÓN DE CHUNKS GRANDES
# ==========================================

def dividir_si_grande(texto: str):

    MAX = 1200
    OVERLAP = 120
    MIN_CHARS = 300
    MAX_PARTES = 6

    if len(texto) <= MAX:
        return [texto]

    partes = []
    i = 0

    while i < len(texto) and len(partes) < MAX_PARTES:
        sub = texto[i:i+MAX]

        if len(sub.strip()) < MIN_CHARS:
            i += MAX - OVERLAP
            continue

        # 🔥 cortar por párrafo o punto (MEJOR)
        corte_parrafo = sub.rfind("\n")
        if corte_parrafo > 300:
            sub = sub[:corte_parrafo]
        else:
            corte = sub.rfind(". ")
            if corte > 300:
                sub = sub[:corte]

        partes.append(sub.strip())
        i += MAX - OVERLAP

    return partes

# ==========================================
# 🔥 FALLBACK
# ==========================================

def fallback_chunking(texto: str):

    MAX = 1600
    OVERLAP = 200
    MAX_CHUNKS = 80   # 🔥 límite fallback

    chunks = []
    i = 0

    while i < len(texto) and len(chunks) < MAX_CHUNKS:
        sub = texto[i:i+MAX]

        if len(safe_split(sub)) > 15:
            chunks.append({
                "contenido": sub.strip(),
                "metadata": {
                    "seccion": "general",
                    "tipo_chunk": "general",
                    "char_length": len(sub)
                }
            })

        i += MAX - OVERLAP

    return chunks


# ==========================================
# 🔥 DETECTOR DE TIPO (CLAVE PARA RANKING)
# ==========================================

def detectar_tipo_chunk(texto: str):

    t = normalizar(texto)
    t_low = t.lower()

    # 🔥 evitar textos basura muy cortos
    if len(safe_split(t_low)) < 20:
        return "general"

    scores = {
        "objetivo": 0,
        "requisito": 0,
        "beneficiarios": 0,
        "resolucion": 0,
        "considerando": 0,
        "financiamiento": 0,
        "duracion": 0,
        "evaluacion": 0,
        "plazos": 0,
        "adjudicacion": 0,
        "formalizacion": 0,
        "definiciones": 0
    }

    # ==========================================
    # 🔥 HEADERS (ULTRA FUERTE)
    # ==========================================

    inicio = t_low[:200]

    if re.search(r'^\s*(objetivo|finalidad|proposito)', inicio):
        scores["objetivo"] += 80

    if re.search(r'^\s*(requisitos?)', inicio):
        scores["requisito"] += 80

    if re.search(r'^\s*(quienes pueden postular|beneficiarios?)', inicio):
        scores["beneficiarios"] += 80

    if re.search(r'^\s*(resuelv|aprueb)', inicio):
        scores["resolucion"] += 100

    if re.search(r'^\s*considerando', inicio):
        scores["considerando"] += 100

    # ==========================================
    # 🔥 OBJETIVO
    # ==========================================

    if "objetivo" in t_low:
        scores["objetivo"] += 40

    if re.search(r'tiene\s+por\s+objetivo', t_low):
        scores["objetivo"] += 60

    if "finalidad" in t_low or "proposito" in t_low:
        scores["objetivo"] += 35

    if re.search(r'objetivo\s+del\s+concurso', t_low):
        scores["objetivo"] += 50

    # ==========================================
    # 🔥 REQUISITOS
    # ==========================================

    if "requisito" in t_low:
        scores["requisito"] += 50

    if re.search(r'deberan\s+(cumplir|presentar)', t_low):
        scores["requisito"] += 40

    if re.search(r'se\s+requiere', t_low):
        scores["requisito"] += 30

    if re.search(r'es\s+necesario', t_low):
        scores["requisito"] += 25

    # ==========================================
    # 🔥 BENEFICIARIOS
    # ==========================================

    if "postulante" in t_low:
        scores["beneficiarios"] += 30

    if "beneficiario" in t_low:
        scores["beneficiarios"] += 40

    if re.search(r'podran\s+(postular|participar)', t_low):
        scores["beneficiarios"] += 50

    if re.search(r'quienes\s+pueden\s+postular', t_low):
        scores["beneficiarios"] += 60

    if "instituciones participantes" in t_low:
        scores["beneficiarios"] += 30

    # ==========================================
    # 🔥 RESOLUCIÓN
    # ==========================================

    if "resuelv" in t_low:
        scores["resolucion"] += 70

    if "aprueb" in t_low:
        scores["resolucion"] += 60

    if "resolucion exenta" in t_low:
        scores["resolucion"] += 50

    # ==========================================
    # 🔥 CONSIDERANDO
    # ==========================================

    if "considerando" in t_low:
        scores["considerando"] += 50

    # ==========================================
    # 🔥 FINANCIAMIENTO
    # ==========================================

    if "monto" in t_low:
        scores["financiamiento"] += 50

    if "financiamiento" in t_low:
        scores["financiamiento"] += 45

    if "subsidio" in t_low:
        scores["financiamiento"] += 40

    if re.search(r'\$\s?\d', t_low):
        scores["financiamiento"] += 35


    # ==========================================
    # 🔥 DURACIÓN
    # ==========================================

    if "duracion" in t_low:
        scores["duracion"] += 45

    if "meses" in t_low:
        scores["duracion"] += 35

    if "anos" in t_low or "años" in t_low:
        scores["duracion"] += 35

    if re.search(r'\d+\s*(mes|meses|ano|anos|año|años)', t_low):
        scores["duracion"] += 40

    # ==========================================
    # 🔥 EVALUACIÓN
    # ==========================================

    if "evaluacion" in t_low:
        scores["evaluacion"] += 50

    if "criterios de evaluacion" in t_low:
        scores["evaluacion"] += 60


    # ==========================================
    # 🔥 PLAZOS
    # ==========================================

    if "plazo" in t_low:
        scores["plazos"] += 40

    if re.search(r'\d+\s*(dias|meses)', t_low):
        scores["plazos"] += 30


    # ==========================================
    # 🔥 ADJUDICACIÓN
    # ==========================================

    if "adjudicacion" in t_low:
        scores["adjudicacion"] += 50

    if "adjudicar" in t_low:
        scores["adjudicacion"] += 40


    # ==========================================
    # 🔥 FORMALIZACIÓN
    # ==========================================

    if "formalizacion" in t_low:
        scores["formalizacion"] += 50

    if "firma del convenio" in t_low:
        scores["formalizacion"] += 40


    # ==========================================
    # 🔥 DEFINICIONES
    # ==========================================

    if "definiciones" in t_low:
        scores["definiciones"] += 60

    # ==========================================
    # 🔥 PENALIZACIONES (CLAVE)
    # ==========================================

    # evitar falsos positivos de objetivo
    if "objetivo" in t_low and len(safe_split(t_low)) > 400:
        scores["objetivo"] -= 20

    # evitar beneficiarios inflado
    if scores["beneficiarios"] > 0 and "requisito" in t_low:
        scores["beneficiarios"] -= 20

    # ==========================================
    # 🔥 DECISIÓN FINAL
    # ==========================================

    tipo_final = max(scores, key=scores.get)
    score_max = scores[tipo_final]

    # 🔥 umbral mínimo (CRÍTICO)
    if score_max < 40:
        return "general"

    return tipo_final

def eliminar_duplicados(chunks):

    vistos = set()
    resultado = []

    for c in chunks:

        texto = c["contenido"]

        key = hashlib.md5(texto[:500].encode()).hexdigest()

        if key not in vistos:
            vistos.add(key)
            resultado.append(c)

    return resultado
