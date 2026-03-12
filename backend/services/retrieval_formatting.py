# backend/services/retrieval/formatting.py
from __future__ import annotations
from typing import Dict, Any, Optional
from backend.services.retrieval_text_utils import normalizar
import re

def gate_ant_contaminacion(docname: str, origen: str, cont: str, claves: list[str]) -> bool:
    if not claves:
        return True

    evidencia_local = f"{docname}\n{origen}\n{cont}"
    t = normalizar(evidencia_local).lower()

    for c in claves:
        if not c:
            continue
        c_norm = normalizar(c).lower()
        if re.search(rf"\b{re.escape(c_norm)}\b", t):
            return True

    return False


def header_chunk(meta: Dict[str, Any], *, total: int, bonus: int, pres: int, occ: int, pen: int) -> str:
    docname = meta.get("documento", "N/D")
    tipo = meta.get("tipo", "N/D")
    origen = meta.get("origen", "N/D")

    pag = meta.get("pagina") or meta.get("pag") or meta.get("page")
    seg = (
        meta.get("segmento")
        or meta.get("seg")
        or meta.get("chunk_index")
        or meta.get("chunk")
    )

    header = f"[DOC={docname} | TIPO={tipo} | ORIGEN={origen}"

    if isinstance(pag, (int, str)):
        header += f" | PAG={pag}"

    if isinstance(seg, (int, str)):
        header += f" | SEG={seg}"

    header += "]"

    return header
