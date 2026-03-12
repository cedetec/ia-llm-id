# services/indexing/text_cleaning.py

import re
import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    # eliminar invisibles
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)

    # unir palabras cortadas por salto
    text = re.sub(r'(\w)\n(\w)', r'\1\2', text)

    # unir sílabas separadas con guión
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

    # reparar vertical OCR
    text = re.sub(
        r'(?:\b[A-ZÁÉÍÓÚÑ]\s*\n){3,}[A-ZÁÉÍÓÚÑ]',
        lambda m: m.group(0).replace(" ", "").replace("\n", ""),
        text
    )

    # OCR horizontal
    text = re.sub(
        r'\b(?:[A-ZÁÉÍÓÚÑ]\s){4,}[A-ZÁÉÍÓÚÑ]\b',
        lambda m: m.group(0).replace(" ", ""),
        text
    )

    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()