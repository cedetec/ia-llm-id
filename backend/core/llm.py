# backend/core/llm.py

from __future__ import annotations
import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

class LLMTimeoutError(RuntimeError): ...
class LLMConnectionError(RuntimeError): ...
class LLMHTTPError(RuntimeError): ...

def consultar_llm(prompt: str, timeout: Optional[int] = None) -> str:
    if not prompt:
        return ""

    to = int(timeout) if timeout is not None else OLLAMA_TIMEOUT

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 120,
            "top_p": 0.9,
        },
    }

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=to,
        )

        r.raise_for_status()
        data = r.json()

        return (data.get("response") or "").strip()

    except requests.exceptions.ReadTimeout as e:
        logger.error("LLM timeout: %s", e)
        raise LLMTimeoutError(f"Ollama timeout after {to}s") from e

    except requests.exceptions.ConnectionError as e:
        logger.error("LLM connection error: %s", e)
        raise LLMConnectionError("No se pudo conectar a Ollama") from e

    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        logger.error("LLM HTTP error (%s): %s", status, e)
        raise LLMHTTPError(f"HTTP error from Ollama ({status})") from e

    except Exception as e:
        logger.exception("Unexpected LLM error")
        raise