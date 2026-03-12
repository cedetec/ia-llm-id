# services/preprocessing/text_normalizer.py

import re
import unicodedata
from backend.services.censurador_service import censurar_texto


def normalizar_espaciado_legal(texto: str) -> str:
    texto = re.sub(
        r'(?:\b[A-ZÁÉÍÓÚÑ]\s){3,}[A-ZÁÉÍÓÚÑ]\b',
        lambda m: m.group(0).replace(" ", ""),
        texto
    )
    return texto


def reparar_texto_pdf(texto: str) -> str:
    texto = re.sub(r'(\w)-\n(\w)', r'\1\2', texto)
    texto = re.sub(r'([a-záéíóúñ])\n([a-záéíóúñ])', r'\1\2', texto, flags=re.I)
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()


def reconstruir_parrafos(texto: str) -> str:
    lineas = texto.split("\n")
    nuevas = []
    buffer = ""

    for l in lineas:
        l = l.strip()
        if not l:
            continue

        if len(l) < 80:
            buffer += " " + l
        else:
            if buffer:
                nuevas.append((buffer + " " + l).strip())
                buffer = ""
            else:
                nuevas.append(l)

    if buffer:
        nuevas.append(buffer.strip())

    return "\n\n".join(nuevas)


def normalizar_texto_completo(texto: str) -> str:
    texto = censurar_texto(texto or "")
    texto = unicodedata.normalize("NFKC", texto)
    texto = texto.replace("\u00A0", " ")
    texto = texto.replace("\r", "\n")

    texto = normalizar_espaciado_legal(texto)
    texto = reparar_texto_pdf(texto)
    texto = reconstruir_parrafos(texto)
    texto = normalizar_espaciado_legal(texto)

    texto = re.sub(r"\s{2,}", " ", texto).strip()
    return texto