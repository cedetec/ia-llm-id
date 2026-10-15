"""
paths.py

Rutas compartidas utilizadas por los distintos
servicios del backend.
"""

from pathlib import Path

# =====================================================
# Directorio base del proyecto
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# =====================================================
# Directorios principales
# =====================================================

DATA_DIR = BASE_DIR / "data"

PDF_DIR = DATA_DIR / "pdfs"

VECTORSTORE_DIR = DATA_DIR / "vectorstore"

CHROMA_DIR = VECTORSTORE_DIR / "chroma"

CHROMA_NOMIC_DIR = VECTORSTORE_DIR / "chroma_nomic"

CHROMA_GEMMA_DIR = VECTORSTORE_DIR / "chroma_embeddinggemma"

LOG_DIR = BASE_DIR / "logs"

TEMP_DIR = BASE_DIR / "temp"

# =====================================================
# Crear directorios automáticamente
# =====================================================

DIRECTORIOS = (

    DATA_DIR,

    PDF_DIR,

    VECTORSTORE_DIR,

    CHROMA_DIR,

    LOG_DIR,

    TEMP_DIR,

)

for directorio in DIRECTORIOS:

    directorio.mkdir(
        parents=True,
        exist_ok=True
    )
