#!/bin/bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8090}"
PDF_DIR="${PDF_DIR:-/home/vicente/dev-tesis/backend/Archivos_pdf}"
MAX_FILES="${MAX_FILES:-5}"
ADMIN_TOKEN="${ADMIN_TOKEN:-super-secret-token}"

echo "🚀 Indexación masiva ANID"
echo "-----------------------------------------"
echo "🌐 Backend: $BACKEND_URL"
echo "📁 Directorio: $PDF_DIR"
echo "🔢 Máximo archivos: $MAX_FILES"
echo "-----------------------------------------"

# Verificar backend
echo "🔎 Verificando backend..."
curl -sS --fail "$BACKEND_URL/health/ping" > /dev/null || {
  echo "❌ Backend no disponible"
  exit 1
}

# Detectar PDFs
shopt -s nullglob
files=("$PDF_DIR"/*.pdf)
shopt -u nullglob

if (( ${#files[@]} == 0 )); then
  echo "⚠️ No hay PDFs en $PDF_DIR"
  exit 0
fi

count=0
for file in "${files[@]}"; do
  name="$(basename "$file")"

  echo "📤 Subiendo: $name"
  curl -sS --fail -X POST \
    "$BACKEND_URL/documentos" \
    -F "file=@$file" > /dev/null

  echo "🧾 Extrayendo texto: $name"
  curl -sS --fail -X POST \
    "$BACKEND_URL/documentos/extraer?doc=$name" > /dev/null

  echo "🧹 Preprocesando: $name"
  curl -sS --fail -X POST \
    "$BACKEND_URL/documentos/preprocesar?doc=$name" > /dev/null

  echo "🧠 Indexando: $name"
  curl -sS --fail -X POST \
    "$BACKEND_URL/documentos/indexar?mode=upsert&doc=$name" \
    -H "x-admin-token: super-secret-token" > /dev/null

  count=$((count+1))
  if (( count >= MAX_FILES )); then
    echo "🛑 Límite alcanzado"
    break
  fi
done

echo ""
echo "✅ Proceso finalizado"
echo "📌 Archivos procesados: $count"