#!/bin/bash
# Canvas Learning System - Ollama Model Initialization
# Story 1.1 Task 1.3: Auto-pull bge-m3 embedding model after Ollama starts
#
# Usage (manual): docker exec canvas-learning-system-ollama bash /init-models.sh
# This script is also referenced by docker-compose for automated setup.

set -e

echo "[init-models] Waiting for Ollama to be ready..."
until curl -sf http://localhost:11434/ > /dev/null 2>&1; do
  sleep 2
done

echo "[init-models] Ollama is ready. Pulling bge-m3 embedding model..."
ollama pull bge-m3

echo "[init-models] bge-m3 model pulled successfully."
