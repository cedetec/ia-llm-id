import re

CITA_TRIGGERS = (
    "cita",
    "textual",
    "frase textual",
    "cita textual",
)

def _modo_cita(pregunta: str) -> bool:
    p = (pregunta or "").lower()
    return bool(re.search(
        r"\b(cita|textual|frase\s+textual|cita\s+textual)\b",
        p
    ))

def construir_prompt(pregunta: str, contexto: str) -> str:
    pregunta = (pregunta or "").strip()
    contexto = (contexto or "").strip()

    return f"""
ROL: Asistente académico extractivo.

INSTRUCCIÓN PRINCIPAL:
Responde SOLO usando el CONTEXTO. No uses conocimiento externo.

REGLAS ESTRICTAS (OBLIGATORIAS):
1) NO inventes ni completes con suposiciones.
2) Responde en una sola frase o párrafo breve.
3) Si la pregunta menciona un número/ID/fecha/resolución:
   - Solo puedes responder si ese dato aparece literalmente en el CONTEXTO.
   - Copia la frase exacta sin modificar palabras.
4) Si NO encuentras literalmente el dato solicitado, responde EXACTAMENTE:
No encontrado en el contexto.

PREGUNTA:
{pregunta}

CONTEXTO (TEXTO DOCUMENTAL):
<<<
{contexto}
>>>

SALIDA:
""".strip()