# schemas/database.py

from pydantic import BaseModel, Field
from typing import List, Optional


# ==========================================
# Concurso indexado
# ==========================================

class IndexedContest(BaseModel):
    nombre: str = Field(
        ...,
        description="Nombre del concurso"
    )

    anio: int = Field(
        ...,
        description="Año del concurso"
    )

    estado: str = Field(
        ...,
        description="Estado de indexación"
    )

    chunks: int = Field(
        ...,
        description="Cantidad de chunks"
    )


# ==========================================
# Estadísticas base de datos
# ==========================================

class DatabaseStats(BaseModel):

    documentos: int

    chunks: int

    coleccion: str

    embedding: str

    modelo: str

    ultimaIndexacion: str

    tamanoIndice: str

    backend: str

    ollama: str

    chroma: str

    tiempoIndexacion: str

    concursos: List[IndexedContest]


# ==========================================
# Estado del sistema
# ==========================================

class DatabaseStatus(BaseModel):

    backend: bool

    ollama: bool

    chroma: bool

    mongo: bool

    embeddings: bool

    api: bool


# ==========================================
# Resultado de operaciones sobre la base
# ==========================================

class DatabaseOperationStatus(BaseModel):

    estado: str

    documentos: int

    chunks: int

    ultimaIndexacion: Optional[str] = None

    mensaje: str


# ==========================================
# Registro de eventos
# ==========================================

class DatabaseLog(BaseModel):

    hora: str

    mensaje: str


# ==========================================
# Respuesta upload
# ==========================================

class UploadResponse(BaseModel):

    ok: bool

    archivo: str

    mensaje: str


class DatabaseFile(BaseModel):

    nombre: str

    tamano: str

    fecha: str
