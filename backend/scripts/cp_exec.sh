#!/bin/bash

CONTENEDOR=$1
SCRIPT=$2

if [ -z "$CONTENEDOR" ] || [ -z "$SCRIPT" ]; then
    echo "Uso: $0 <contenedor> <script>"
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "No existe: $SCRIPT"
    exit 1
fi

DESTINO="/app/app"

NOMBRE=$(basename "$SCRIPT")

echo "Copiando $SCRIPT -> $DESTINO/$NOMBRE"

docker cp "$SCRIPT" "$CONTENEDOR":"$DESTINO/$NOMBRE"

echo "Ejecutando..."

docker exec -it "$CONTENEDOR" python "$DESTINO/$NOMBRE"