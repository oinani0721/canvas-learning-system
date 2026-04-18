#!/usr/bin/env bash
# Story 1.13: Pre-deployment checklist
# Run before `docker compose up -d` to catch common issues.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"
PASS="✅ PASS"
FAIL="❌ FAIL"
ERRORS=0

echo "═══════════════════════════════════════════════"
echo "  Canvas Learning System — Pre-Deploy Checklist"
echo "═══════════════════════════════════════════════"
echo ""

# 1. Docker Desktop
if command -v docker &>/dev/null && docker info &>/dev/null; then
  echo "$PASS Docker Desktop is running"
else
  echo "$FAIL Docker Desktop not running"
  echo "  Fix: Open Docker Desktop or run: open -a Docker"
  ERRORS=$((ERRORS + 1))
fi

# 2. .env exists with required vars
if [ -f "$ENV_FILE" ]; then
  MISSING_VARS=()
  for VAR in NEO4J_USER NEO4J_PASSWORD CANVAS_BASE_PATH; do
    VAL=$(grep -E "^${VAR}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2-)
    if [ -z "$VAL" ]; then
      MISSING_VARS+=("$VAR")
    fi
  done
  if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo "$PASS .env exists with required variables"
  else
    echo "$FAIL .env missing required variables: ${MISSING_VARS[*]}"
    echo "  Fix: cp .env.example .env && edit .env"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "$FAIL .env file not found"
  echo "  Fix: cp .env.example .env && edit .env"
  ERRORS=$((ERRORS + 1))
fi

# 3. Port availability
for PORT_INFO in "7478:Neo4j HTTP" "7691:Neo4j Bolt" "8001:Backend API"; do
  PORT="${PORT_INFO%%:*}"
  NAME="${PORT_INFO#*:}"
  if lsof -i ":$PORT" -sTCP:LISTEN &>/dev/null; then
    echo "$FAIL Port $PORT ($NAME) already in use"
    echo "  Fix: lsof -i :$PORT   # find and stop the process"
    ERRORS=$((ERRORS + 1))
  else
    echo "$PASS Port $PORT ($NAME) available"
  fi
done

# 4. Ollama running (Mac native)
if command -v ollama &>/dev/null; then
  if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "$PASS Ollama is running"
  else
    echo "$FAIL Ollama installed but not running"
    echo "  Fix: ollama serve  # or: brew services start ollama"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "$FAIL Ollama not installed"
  echo "  Fix: brew install ollama && ollama serve"
  ERRORS=$((ERRORS + 1))
fi

# 5. bge-m3 model downloaded
if command -v ollama &>/dev/null && ollama list 2>/dev/null | grep -q "bge-m3"; then
  echo "$PASS Ollama bge-m3 model available"
else
  echo "$FAIL bge-m3 embedding model not found"
  echo "  Fix: ollama pull bge-m3"
  ERRORS=$((ERRORS + 1))
fi

# 6. CORS includes Obsidian
if [ -f "$ENV_FILE" ]; then
  CORS=$(grep -E "^CORS_ORIGINS=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if echo "$CORS" | grep -q "obsidian.md"; then
    echo "$PASS CORS config includes app://obsidian.md"
  else
    echo "$FAIL CORS missing Obsidian origin"
    echo "  Fix: Add app://obsidian.md to CORS_ORIGINS in .env"
    ERRORS=$((ERRORS + 1))
  fi
fi

# 7. Vault path exists
if [ -f "$ENV_FILE" ]; then
  VAULT_PATH=$(grep -E "^CANVAS_BASE_PATH=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"')
  if [ -n "$VAULT_PATH" ] && [ -d "$VAULT_PATH" ]; then
    echo "$PASS Vault path exists: $VAULT_PATH"
  elif [ -n "$VAULT_PATH" ]; then
    echo "$FAIL Vault path does not exist: $VAULT_PATH"
    echo "  Fix: Create the directory or update CANVAS_BASE_PATH in .env"
    ERRORS=$((ERRORS + 1))
  fi
fi

echo ""
echo "═══════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
  echo "  All checks passed! Run: docker compose up -d"
else
  echo "  $ERRORS issue(s) found. Fix them before deploying."
fi
echo "═══════════════════════════════════════════════"
exit $ERRORS
