#!/bin/bash
# Canvas Learning System - WSL2 Environment Verification
# Validates that all tools and services are correctly set up.
#
# Usage: bash wsl2-verify.sh
# Run inside WSL2 after wsl2-setup.sh completes.

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() { echo -e "  ${GREEN}PASS${NC} $*"; PASS=$((PASS+1)); }
check_fail() { echo -e "  ${RED}FAIL${NC} $*"; FAIL=$((FAIL+1)); }
check_warn() { echo -e "  ${YELLOW}WARN${NC} $*"; WARN=$((WARN+1)); }

echo "=== Canvas Learning System - WSL2 Environment Check ==="
echo ""

# --- 1. WSL2 environment ---
echo "[1/8] WSL2 Environment"
if grep -qi microsoft /proc/version 2>/dev/null; then
    check_pass "Running inside WSL2"
else
    check_fail "Not running inside WSL2"
fi

# Filesystem check: should NOT be on /mnt/c/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "$SCRIPT_DIR" == /mnt/c/* ]]; then
    check_fail "Project is on /mnt/c/ (slow 9P). Move to ~/canvas/"
else
    check_pass "Project on native WSL2 filesystem: $SCRIPT_DIR"
fi

# --- 2. Node.js ---
echo ""
echo "[2/8] Node.js"
if command -v node &>/dev/null; then
    NODE_VER=$(node -v)
    NODE_PATH=$(which node)
    if [[ "$NODE_PATH" == /mnt/c/* ]]; then
        check_warn "Node.js at Windows path: $NODE_PATH (use NVM version)"
    else
        check_pass "Node.js $NODE_VER at $NODE_PATH"
    fi
else
    check_fail "Node.js not found"
fi

if command -v npx &>/dev/null; then
    check_pass "npx available"
else
    check_fail "npx not found"
fi

# --- 3. Claude Code ---
echo ""
echo "[3/8] Claude Code"
if command -v claude &>/dev/null; then
    CLAUDE_VER=$(claude --version 2>/dev/null || echo "unknown")
    check_pass "Claude Code installed: $CLAUDE_VER"
else
    check_fail "Claude Code not found — run: npm install -g @anthropic-ai/claude-code"
fi

# Agent Teams env
if [ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ]; then
    check_pass "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
else
    check_warn "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS not set (add to ~/.bashrc)"
fi

# --- 4. Python + tools ---
echo ""
echo "[4/8] Python & Quality Tools"
for tool in python3 pip pytest mutmut vulture ruff uv; do
    if command -v "$tool" &>/dev/null; then
        check_pass "$tool: $(${tool} --version 2>&1 | head -1)"
    else
        check_fail "$tool not found"
    fi
done

# --- 5. tmux ---
echo ""
echo "[5/8] tmux"
if command -v tmux &>/dev/null; then
    check_pass "tmux: $(tmux -V)"
    if grep -q "history-limit 50000" ~/.tmux.conf 2>/dev/null; then
        check_pass "tmux history-limit: 50000"
    else
        check_warn "tmux history-limit not configured (echo 'set -g history-limit 50000' >> ~/.tmux.conf)"
    fi
else
    check_fail "tmux not found"
fi

# --- 6. Docker services ---
echo ""
echo "[6/8] Docker Services (via localhost)"

# ollama
if curl -sf http://localhost:11434 >/dev/null 2>&1; then
    check_pass "Ollama: localhost:11434"
else
    check_warn "Ollama not reachable — start on Windows: docker compose up -d ollama"
fi

# neo4j-test (test instance)
if python3 -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7692', auth=('neo4j','testpassword'))
d.verify_connectivity(); d.close()
" 2>/dev/null; then
    check_pass "neo4j-test: bolt://localhost:7692"
else
    check_warn "neo4j-test not reachable — docker compose --profile test up -d neo4j-test"
fi

# neo4j (Graphiti, port 7689)
if python3 -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7689', auth=('neo4j','demodemo'))
d.verify_connectivity(); d.close()
" 2>/dev/null; then
    check_pass "neo4j (Graphiti): bolt://localhost:7689"
else
    check_warn "neo4j (Graphiti) at 7689 not reachable"
fi

# neo4j (canvas, port 7691)
if python3 -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7691', auth=('neo4j','password'))
d.verify_connectivity(); d.close()
" 2>/dev/null; then
    check_pass "neo4j (canvas): bolt://localhost:7691"
else
    check_warn "neo4j (canvas) at 7691 not reachable"
fi

# --- 7. Project files ---
echo ""
echo "[7/8] Project Infrastructure Files"
cd "$SCRIPT_DIR"

for f in \
    ".claude/hooks/post-tool-router.sh" \
    ".claude/hooks/pretool-guard.js" \
    ".claude/hooks/mock-import-guard.js" \
    ".claude/hooks/context-inject.js" \
    ".claude/hooks/stop-test-runner.js" \
    ".claude/settings.json" \
    ".claude/commands/auto-epic.md" \
    ".mcp.json" \
    "ralph-runner.sh" \
    "backend/setup.cfg" \
    "frontend/stryker.config.json" \
    "frontend/vitest.config.ts" \
    ".gitattributes" \
    "docker-compose.yml"; do
    if [ -f "$f" ]; then
        check_pass "$f"
    else
        check_fail "$f missing"
    fi
done

# --- 8. MCP servers quick test ---
echo ""
echo "[8/8] MCP Server Smoke Test"

# sequential-thinking (npx)
if npx -y @modelcontextprotocol/server-sequential-thinking --help >/dev/null 2>&1; then
    check_pass "sequential-thinking MCP: npx resolvable"
else
    check_warn "sequential-thinking MCP: npx resolution failed (may work on first real use)"
fi

# context7 (npx)
if npx -y @upstash/context7-mcp@latest --help >/dev/null 2>&1; then
    check_pass "context7 MCP: npx resolvable"
else
    check_warn "context7 MCP: npx resolution failed (may work on first real use)"
fi

# --- Summary ---
echo ""
echo "════════════════════════════════════════"
echo -e "  ${GREEN}PASS${NC}: $PASS   ${RED}FAIL${NC}: $FAIL   ${YELLOW}WARN${NC}: $WARN"
echo "════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Some checks failed. Fix FAILs before proceeding.${NC}"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}Some warnings. Non-critical but review recommended.${NC}"
    exit 0
else
    echo -e "${GREEN}All checks passed! Ready for Agent Teams.${NC}"
    exit 0
fi
