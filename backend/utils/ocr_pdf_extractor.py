# backend/utils/ocr_pdf_extractor.py

import fitz
import pytesseract
from pdf2image import convert_from_path
from pdf2image import pdfinfo_from_path

import re

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def limpiar_texto_pdf(texto: str) -> str:

    texto = texto.replace("\xa0", " ")
    texto = texto.replace("\u200b", "")
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    texto = re.sub(r'([a-z])([A-ZÁÉÍÓÚÑ])', r'\1 \2', texto)
    texto = re.sub(r'([a-z])([A-Z])', r'\1 \2', texto)

    # unir encabezados partidos comunes en PDFs ANID
    texto = re.sub(
        r'\bOBJETIVO\s*\n\s*DEL\s*\n\s*CONCURSO\b',
        'OBJETIVO DEL CONCURSO',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'\bREQUISITOS\s*\n\s*DE\s*\n\s*POSTULACION\b',
        'REQUISITOS DE POSTULACION',
        texto,
        flags=re.I
    )

    texto = re.sub(
        r'\bQUIENES\s*\n\s*PUEDEN\s*\n\s*POSTULAR\b',
        'QUIENES PUEDEN POSTULAR',
        texto,
        flags=re.I
    )

    return texto.strip()


def texto_valido(texto: str) -> bool:
    if not texto:
        return False

    palabras = texto.split()
    if len(palabras) < 40:
        return False

    letras = sum(c.isalpha() for c in texto)
    ratio = letras / max(len(texto), 1)

    # bajar umbral para documentos administrativos
    return ratio > 0.35

def es_pagina_administrativa(texto: str) -> bool:
    texto_upper = texto.upper()

    patrones = [
        "TOMADO DE RAZÓN",
        "CONTRALOR GENERAL",
        "POR ORDEN DEL CONTRALOR"
    ]

    coincidencias = sum(p in texto_upper for p in patrones)

    # Solo si es corta y claramente página final
    return coincidencias >= 2 and len(texto) < 800

def extract_text_smart(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""

    # extracción directa
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))

        for block in blocks:
            text += block[4] + "\n"

    doc.close()

    # reparar encabezados partidos por OCR o layout
    text = re.sub(
        r'OBJETIVO\s*\n\s*DEL\s*\n\s*CONCURSO',
        'OBJETIVO DEL CONCURSO',
        text,
        flags=re.I
    )

    text = re.sub(
        r'REQUISITOS\s*\n\s*DE\s*\n\s*POSTULACION',
        'REQUISITOS DE POSTULACION',
        text,
        flags=re.I
    )

    if texto_valido(text):
        print("📄 PDF con texto digital detectado")
        return limpiar_texto_pdf(text)

    print("🧠 PDF escaneado detectado → activando OCR...")

    info = pdfinfo_from_path(pdf_path)
    num_pages = info["Pages"]

    MAX_PAGES_OCR = 200

    if num_pages > MAX_PAGES_OCR:
        print(f"⚠️ PDF muy grande ({num_pages} páginas), limitando OCR")
        num_pages = MAX_PAGES_OCR

    ocr_text = ""

    for page in range(1, num_pages + 1):

        images = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=page,
            last_page=page,
            fmt="jpeg",
            thread_count=1
        )

        img = images[0]

        page_text = pytesseract.image_to_string(
            img,
            lang="spa",
            config="--oem 3 --psm 6 -c preserve_interword_spaces=1"
        )

        if es_pagina_administrativa(page_text):
            print(f"🚫 Página administrativa ignorada ({page})")
            continue

        ocr_text += page_text + "\n"

    DEBUG_OCR = False

    if DEBUG_OCR:
        print("----- DEBUG OCR -----")
        print("Largo texto extraído:", len(ocr_text))
        print(ocr_text[:500])
        print("---------------------")

    if len(ocr_text.strip()) < 1000:
        print("⚠️ OCR sospechoso: muy poco contenido útil")

    return limpiar_texto_pdf(ocr_text)
