#!/bin/sh
# Entrypoint script para Railway

# Usa a variável PORT do Railway ou 8001 como fallback
PORT=${PORT:-8001}

# Inicia o uvicorn usando python -m para garantir que o módulo seja encontrado
exec python -m uvicorn server:app --host 0.0.0.0 --port "$PORT" --workers 2
