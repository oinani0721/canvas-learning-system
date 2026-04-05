#!/bin/bash
# Start MLX Embedding Server for jina-code-embeddings-1.5b
# Usage: ./start.sh [--dim 1024] [--port 11435]
#
# The server exposes an Ollama-compatible /api/embeddings endpoint.
# codebase-memory MCP connects to this server for semantic code search.

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/.venv/bin/activate"

echo "Starting MLX Embedding Server (jina-code-embeddings-1.5b)..."
echo "  Port: ${2:-11435}"
echo "  Dimensions: ${2:-1024}"
echo "  Endpoint: http://localhost:${2:-11435}/api/embeddings"
echo ""

python "$DIR/server.py" "$@"
