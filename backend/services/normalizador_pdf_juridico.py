#normalizador_pdf_juridico.py
import re

def normalizar_texto_juridico(texto: str) -> str:

    texto = texto.replace("\u00A0", " ")

    # reparar palabras cortadas con guion
    texto = re.sub(r'(\w+)-\n(\w+)', r'\1\2', texto)

    # reparar palabras cortadas sin guion
    texto = re.sub(
        r'([a-záéíóúñ]{4,})\n([a-záéíóúñ]{3,})',
        r'\1\2',
        texto
    )

    # unir texto corrido
    texto = re.sub(
        r'(?<=[a-záéíóúñ])\n(?=[a-záéíóúñ])',
        ' ',
        texto
    )

    # reparar OCR corto
    texto = re.sub(
        r'(\w{4,})\s*\n\s*([a-záéíóúñ]{1,2})\b',
        r'\1\2',
        texto
    )

    # separar mayúsculas pegadas
    texto = re.sub(
        r'([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])',
        r'\1 \2',
        texto
    )

    # eliminar encabezado ANID
    texto = re.sub(
        r'^Agencia Nacional de Investigaci[oó]n y Desarrollo.*?$',
        '',
        texto,
        flags=re.IGNORECASE | re.MULTILINE
    )

    # eliminar numeración de página
    texto = re.sub(r'P[aá]gina \d+ de \d+', '', texto, flags=re.I)

    # normalizar espacios
    texto = re.sub(r'[ \t]{2,}', ' ', texto)

    return texto.strip()
