"""
system_service.py

Servicio encargado de comprobar el estado
de los componentes principales del sistema.
"""

from __future__ import annotations

import socket

from pathlib import Path

from app.schemas.database import DatabaseStatus

from LLM.config.config_loader import (
    cargar_configuracion_embeddings,
)

from LLM.config.llm_config import (
    obtener_modelo,
)

from app.services.database_service import (
    database_exists
)


# ==========================================
# Backend
# ==========================================

def backend_ok() -> bool:
    """
    Si esta función puede ejecutarse,
    el backend está operativo.
    """

    return True


# ==========================================
# Ollama
# ==========================================

def ollama_ok() -> bool:
    """
    Comprueba si existe un modelo configurado.
    """

    try:

        modelo = obtener_modelo()

        return bool(modelo)

    except Exception:

        return False


# ==========================================
# Chroma
# ==========================================

def chroma_ok() -> bool:

    return database_exists()


# ==========================================
# MongoDB
# ==========================================

def mongo_ok() -> bool:
    """
    Comprobación básica.

    Se conectará posteriormente con MongoDB.
    """

    return True


# ==========================================
# Embeddings
# ==========================================

def embeddings_ok() -> bool:
    """
    Comprueba que exista un modelo
    de embeddings configurado.
    """

    try:

        embedding = cargar_configuracion_embeddings()

        return bool(
            embedding["model"]
        )

    except Exception:

        return False


# ==========================================
# API
# ==========================================

def api_ok() -> bool:
    """
    Comprueba que el proceso responda.
    """

    try:

        socket.gethostname()

        return True

    except Exception:

        return False


# ==========================================
# Estado general
# ==========================================

def build_system_status() -> DatabaseStatus:
    """
    Devuelve el estado completo
    del sistema.
    """

    return DatabaseStatus(

        backend=backend_ok(),

        ollama=ollama_ok(),

        chroma=chroma_ok(),

        mongo=mongo_ok(),

        embeddings=embeddings_ok(),

        api=api_ok(),

    )
