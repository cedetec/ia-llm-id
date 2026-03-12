# backend/services/consulta_utils_llm.py
from __future__ import annotations
import re
import json

def limpiar_salida_llm(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"```(?:json)?\s*", "", texto, flags=re.IGNORECASE)
    texto = texto.replace("```", "")

    basura = [
        "</start_of_turn>", "<start_of_turn>",
        "<|start_of_turn|>", "<|end_of_turn|>",
        "<|eot_id|>", "<|endoftext|>",
    ]
    for b in basura:
        texto = texto.replace(b, "")

    return texto.strip()


def extraer_json(texto: str) -> dict | None:
    if not texto:
        return None

    stack = []
    start = None

    for i, ch in enumerate(texto):
        if ch == "{":
            if not stack:
                start = i
            stack.append(ch)
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    candidato = texto[start:i+1]
                    try:
                        return json.loads(candidato)
                    except Exception:
                        return None
    return None


def recortar_contexto_para_llm(contexto: str, *, max_chars_total: int = 6000) -> str:
    c = (contexto or "").strip()
    if not c:
        return ""

    if len(c) <= max_chars_total:
        return c

    corte = c[:max_chars_total]

    # cortar en último doble salto
    idx = corte.rfind("\n\n")
    if idx > 1000:
        return corte[:idx]

    # fallback: último punto
    idx = corte.rfind(". ")
    if idx > 500:
        return corte[:idx+1]

    return corte
