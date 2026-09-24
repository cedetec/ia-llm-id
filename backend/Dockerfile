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
# Instalar modelos Argos
#

COPY install_argos_models.py /tmp/

RUN python /tmp/install_argos_models.py

#
# Copiar el proyecto
#

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]