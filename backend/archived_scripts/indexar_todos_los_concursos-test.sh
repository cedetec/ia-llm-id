#!/bin/bash
# ==========================================================
# Script de automatización: carga, preprocesamiento, indexación
# Procesa TODOS los PDFs del directorio Documentos ANID
# ==========================================================

set -e  # cortar ante errores graves

BACKEND_URL="http://127.0.0.1:8090"

# 👉 AJUSTA ESTA RUTA A TU SISTEMA (según la captura)
PDF_DIR="$HOME/Documentos/DocumentosAnid/test1"

echo "🚀 Iniciando indexación masiva de fondos concursables ANID"
echo "📂 Directorio origen: $PDF_DIR"
echo "---------------------------------------------------------"

# Validación básica
if [ ! -d "$PDF_DIR" ]; then
  echo "❌ ERROR: El directorio no existe: $PDF_DIR"
  exit 1
fi

PDF_COUNT=$(find "$PDF_DIR" -type f -iname "*.pdf" | wc -l)
echo "📊 PDFs detectados: $PDF_COUNT"

if [ "$PDF_COUNT" -eq 0 ]; then
  echo "❌ ERROR: No se encontraron PDFs para procesar."
  exit 1
fi

echo ""

# 1️⃣ Subir todos los PDFs
echo "📤 Subiendo documentos..."
echo "---------------------------------------------------------"

find "$PDF_DIR" -type f -iname "*.pdf" | while read -r file; do
    filename=$(basename "$file")
    echo "📄 Subiendo: $filename"

    curl -s -X POST "$BACKEND_URL/documentos" \
        -F "file=@$file" \
        | jq -c '.'

done

echo ""
echo "🧹 Ejecutando preprocesamiento..."
echo "---------------------------------------------------------"
curl -s -X POST "$BACKEND_URL/preprocesar" | jq

echo ""
echo "🧠 Ejecutando indexación..."
echo "---------------------------------------------------------"
curl -s -X POST "$BACKEND_URL/indexar" | jq
