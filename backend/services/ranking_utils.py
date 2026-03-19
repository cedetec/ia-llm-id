# ranking_utils.py
import re
import unicodedata
import numpy as np

def cosine(v1, v2):
    try:
        v1 = np.array(v1)
        v2 = np.array(v2)

        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        if denom == 0:
            return 0.0

        return float(np.dot(v1, v2) / denom)
    except:
        return 0.0


def normalizar_txt(txt):

    if not txt:
        return ""

    txt = unicodedata.normalize("NFKD", txt)\
        .encode("ascii", "ignore")\
        .decode("ascii")\
        .lower()

    txt = re.sub(r'(?<=\b[a-z])\s+(?=[a-z]\b)', '', txt)
    txt = re.sub(r'\s+', ' ', txt)

    return txt


def similitud_textual(a, b):

    sa = set(a.split())
    sb = set(b.split())

    inter = sa & sb
    union = sa | sb

    if not union:
        return 0

    return len(inter) / max(len(union), 1)
