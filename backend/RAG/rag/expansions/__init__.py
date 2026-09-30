# LLM/rag/expansions/__init__.py

from .common import (
    EXPANSIONES_COMUNES
)

from .cabo_hornos import (
    EXPANSIONES_CABO_HORNOS
)

from .embarcaciones import (
    EXPANSIONES_EMBARCACIONES
)

from .fondecyt import (
    EXPANSIONES_FONDECYT
)

from .ingenieria2030 import (
    EXPANSIONES_INGENIERIA2030
)


EXPANSIONES_DOCUMENTO = {

    "CABO_HORNOS":
        EXPANSIONES_CABO_HORNOS,

    "EMBARCACIONES":
        EXPANSIONES_EMBARCACIONES,

    "FONDECYT_REGULAR":
        EXPANSIONES_FONDECYT,

    "FONDECYT_INICIACION":
        EXPANSIONES_FONDECYT,

    "INGENIERIA_2030":
        EXPANSIONES_INGENIERIA2030

}