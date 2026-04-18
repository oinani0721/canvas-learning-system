#!/usr/bin/env bash
# Story 1.11: Sync shared variables from root .env to backend/.env
# Creates backup before overwriting.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_ENV="$ROOT_DIR/.env"
BACKEND_ENV="$ROOT_DIR/backend/.env"

if [ ! -f "$ROOT_ENV" ]; then
  echo "❌ Root .env not found: $ROOT_ENV"
  exit 1
fi

if [ ! -f "$BACKEND_ENV" ]; then
  echo "❌ Backend .env not found: $BACKEND_ENV"
  exit 1
fi

# Shared variables to sync
SHARED_VARS=(
  NEO4J_USER
  NEO4J_PASSWORD
  NEO4J_HTTP_PORT
  NEO4J_BOLT_PORT
  CANVAS_BASE_PATH
  VAULTS_ROOT
  ACTIVE_VAULT
  OLLAMA_HOST
  CORS_ORIGINS
  DEBUG
)

# Backup
BACKUP="$BACKEND_ENV.backup.$(date +%Y%m%d_%H%M%S)"
cp "$BACKEND_ENV" "$BACKUP"
echo "✅ Backup: $BACKUP"

SYNCED=0
for VAR in "${SHARED_VARS[@]}"; do
  ROOT_VAL=$(grep -E "^${VAR}=" "$ROOT_ENV" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if [ -z "$ROOT_VAL" ]; then
    continue
  fi

  if grep -qE "^${VAR}=" "$BACKEND_ENV"; then
    # Replace existing
    sed -i '' "s|^${VAR}=.*|${VAR}=${ROOT_VAL}|" "$BACKEND_ENV"
  else
    # Append
    echo "${VAR}=${ROOT_VAL}" >> "$BACKEND_ENV"
  fi
  SYNCED=$((SYNCED + 1))
done

echo "✅ Synced $SYNCED shared variables from root .env → backend/.env"
