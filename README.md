## Primer Lanzamiento

1. Colocar los archivos PDF en `backend/data/pdfs/`.

2. Levantar contenedores:
```bash
docker compose up -d --build
# En producción: docker compose -f docker-compose.prod.yml up -d --build
```

3. Esperar la descarga de modelos:
```bash
docker compose logs -f ollama-pull-models
```

4. Indexar documentos:
```bash
./ingest.sh
# En producción: ./ingest.sh --prod
```

5. Reiniciar backend para cargar el nuevo índice:
```bash
docker compose restart backend-retrieval backend-generation
# En producción: docker compose -f docker-compose.prod.yml restart backend-retrieval backend-generation
```

## Re-indexación de Documentos

Para indexar nuevos PDFs o cambios en `backend/data/pdfs/`:

```bash
./ingest.sh
docker compose restart backend-retrieval backend-generation

# En producción:
# ./ingest.sh --prod
# docker compose -f docker-compose.prod.yml restart backend-retrieval backend-generation
```
