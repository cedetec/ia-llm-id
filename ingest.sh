#!/bin/bash
COMPOSE_FILE=""
if [ "$1" == "--prod" ]; then
    COMPOSE_FILE="-f docker-compose.prod.yml"
    echo "Usando configuración de PRODUCCIÓN..."
fi

# Asegurarnos de que los servicios base estén corriendo
docker compose $COMPOSE_FILE up -d ollama mongodb

# Esperar a que Ollama esté listo (por si se acaban de prender)
echo "Esperando a que Ollama despierte..."
docker compose $COMPOSE_FILE exec -T ollama bash -c "until ollama list > /dev/null 2>&1; do sleep 2; done" || true

# docker compose run --rm levanta el contenedor temporalmente,
# ejecuta el script interno y luego destruye el contenedor automáticamente.
docker compose $COMPOSE_FILE run --rm backend-ingestion bash scripts/index_batch.sh

echo "=========================================================="
echo "Indexación completada. El contenedor temporal fue cerrado."
echo "=========================================================="
