#!/bin/sh

set -e

OLLAMA_CONTAINER="tesis-2026-ollama-1"

echo "======================================"
echo " Instalación de modelos Ollama"
echo "======================================"

echo
echo ">> Comprobando Ollama..."

docker exec "$OLLAMA_CONTAINER" ollama list

echo
echo "======================================"
echo " MODELOS DE IA"
echo "======================================"

MODELS="
qwen2.5:latest
mistral:latest
gemma4:e2b
deepseek-r1:8b
"

for MODEL in $MODELS
do
    echo
    echo ">> Instalando modelo: $MODEL"
    docker exec "$OLLAMA_CONTAINER" ollama pull "$MODEL"
done

echo
echo "======================================"
echo " MODELOS RAG / EMBEDDINGS"
echo "======================================"

RAG_MODELS="
nomic-embed-text:latest
embeddinggemma:latest
"

for MODEL in $RAG_MODELS
do
    echo
    echo ">> Instalando embedding: $MODEL"
    docker exec "$OLLAMA_CONTAINER" ollama pull "$MODEL"
done

echo
echo "======================================"
echo " MODELOS INSTALADOS"
echo "======================================"

docker exec "$OLLAMA_CONTAINER" ollama list

echo
echo "======================================"
echo " Instalación completada"
echo "======================================"
