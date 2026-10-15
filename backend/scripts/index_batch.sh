#!/bin/bash
# Script para correr la indexación manual offline

echo "========================================"
echo "Iniciando proceso de indexación offline"
echo "========================================"

cd /app
python /app/scripts/run_indexing.py

echo "========================================"
echo "Indexación completada"
echo "========================================"
