FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV ANONYMIZED_TELEMETRY=False

WORKDIR /app

#
# Dependencias del sistema
#

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

#
# Instalar dependencias Python
#

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

#
# Actualizar algunas librerías
#

RUN pip install --upgrade ollama posthog

#
# Pre-descargar el modelo CrossEncoder en la imagen para no demorar el arranque
#

RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

#
# Copiar el proyecto
#

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]