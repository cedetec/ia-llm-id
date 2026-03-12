# backend/utils/document_utils.py

import re
import unicodedata


def normalizar_nombre_doc(s: str) -> str:
    if not s:
        return ""

    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"\.pdf$", "", s)
    s = re.sub(r"[^a-z0-9]+", "", s)

    return s.strip()