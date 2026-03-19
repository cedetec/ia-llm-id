# chunking_juridico.py

import re
import hashlib
from backend.services.normalizador_pdf_juridico import normalizar_texto_juridico
from backend.services.retrieval_text_utils import normalizar


# ==========================================
# 🔥 LIMPIEZA OCR (CRÍTICO)
# ==========================================

def limpiar_texto(texto: str) -> str:
    texto = normalizar_texto_juridico(texto)

    # eliminar caracteres raros OCR
    texto = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ.,;:()/%\s-]', ' ', texto)

    # eliminar palabras corruptas (OCR basura)
    texto = re.sub(r'\b[A-Z]{7,}\b', '', texto)

    # espacios
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()


# ==========================================
# 🔥 SPLIT JURÍDICO PRINCIPAL
# ==========================================

SECCIONES = re.compile(
    r'\b(VISTOS|CONSIDERANDO|RESUELV[EO])\b',
    re.IGNORECASE
)


# ==========================================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================================

def chunkear_documento(fragmentos: list[str]):

    # 1️⃣ unir texto
    texto = "\n".join([f for f in fragmentos if f and len(f.strip()) > 20])
    texto = limpiar_texto(texto)

    # 2️⃣ dividir por secciones jurídicas
    partes = re.split(SECCIONES, texto)

    chunks = []

    # 3️⃣ reconstrucción estructurada
    for i in range(1, len(partes), 2):

        titulo = partes[i]
        contenido = partes[i+1] if i+1 < len(partes) else ""

        bloque = f"{titulo} {contenido}".strip()

        # filtros anti ruido
        if len(bloque) < 80:
            continue

        if len(bloque.split()) < 15:
            continue

        # metadata base
        meta = {
            "seccion": titulo.lower(),
            "tipo_chunk": detectar_tipo_chunk(bloque),
            "char_length": len(bloque),
            "es_resolutivo": bool(re.search(r'resuelv', titulo, re.I))
        }

        # dividir si es muy grande
        subchunks = dividir_si_grande(bloque)

        for sub in subchunks:
            if len(sub.split()) < 12:
                continue

            chunks.append({
                "contenido": sub.strip(),
                "metadata": meta
            })

    # 4️⃣ fallback si no detecta secciones
    if not chunks:
        chunks = fallback_chunking(texto)

    # 5️⃣ eliminar duplicados
    return eliminar_duplicados(chunks)


# ==========================================
# 🔥 DIVISIÓN DE CHUNKS GRANDES
# ==========================================

def dividir_si_grande(texto: str):

    MAX = 1100
    OVERLAP = 150

    if len(texto) <= MAX:
        return [texto]

    partes = []
    i = 0

    while i < len(texto):
        sub = texto[i:i+MAX]

        # cortar en salto si se puede
        corte = sub.rfind(". ")
        if corte > 200:
            sub = sub[:corte]

        partes.append(sub.strip())
        i += MAX - OVERLAP

    return partes


# ==========================================
# 🔥 FALLBACK
# ==========================================

def fallback_chunking(texto: str):

    MAX = 1000
    OVERLAP = 150

    chunks = []
    i = 0

    while i < len(texto):
        sub = texto[i:i+MAX]

        if len(sub.split()) > 12:
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

    inicio = t[:400]

    # resolución (máxima prioridad)
    if any(x in inicio for x in [
        "resuelvo", "resuelve", "aprueba", "dispone"
    ]):
        return "resolucion"

    # objetivo
    if "objetivo" in inicio:
        return "objetivo"

    # postulacion
    if any(x in inicio for x in [
        "podran postular", "podrán postular", "beneficiarios"
    ]):
        return "postulacion"

    # requisitos
    if "requisito" in inicio:
        return "requisito"

    # considerando
    if "considerando" in inicio or inicio.startswith("que "):
        return "considerando"

    return "general"


# ==========================================
# 🔥 ELIMINAR DUPLICADOS
# ==========================================

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
