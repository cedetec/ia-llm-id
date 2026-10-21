# schemas_old.py

from typing import Optional

from pydantic import BaseModel


class Pregunta(BaseModel):

    pregunta: str

    conversation_id: Optional[str] = None

    modelo: Optional[str] = None

    rag: Optional[str] = "embeddinggemma"
