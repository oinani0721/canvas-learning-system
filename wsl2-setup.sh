#!/bin/bash
# Canvas Learning System - WSL2 Environment Setup
# Automates Phase 0 of the WSL2 + Agent Teams deployment plan.
#
# Usage: bash wsl2-setup.sh
# Run inside WSL2 Ubuntu 24.04 (not Windows CMD/PowerShell)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Guard: must run inside WSL2
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    error "This script must run inside WSL2 (Ubuntu), not Windows."
fi

info "=== Phase 0.1: System packages ==="
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential tmux jq python3 python3-pip python3-venv python-is-python3

# tmux config for large Agent output buffers
if ! grep -q "history-limit 50000" ~/.tmux.conf 2>/dev/null; then
    echo "set -g history-limit 50000" >> ~/.tmux.conf
    info "tmux history-limit set to 50000"
fi

info "=== Phase 0.2: Node.js via NVM ==="
if command -v nvm &>/dev/null || [ -d "$HOME/.nvm" ]; then
    info "NVM already installed, skipping"
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
fi
# Source NVM for this script session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

if ! command -v node &>/dev/null || ! node -v | grep -q "v20"; then
    nvm install 20
    nvm alias default 20
fi
NODE_PATH=$(which node)
if [[ "$NODE_PATH" == /mnt/c/* ]]; then
    warn "Node.js resolves to Windows path ($NODE_PATH). Should be ~/.nvm/..."
    warn "Run: nvm use 20"
else
    info "Node.js: $(node -v) at $NODE_PATH"
fi

info "=== Phase 0.3: Claude Code ==="
if command -v claude &>/dev/null; then
    info "Claude Code already installed: $(claude --version 2>/dev/null || echo 'installed')"
else
    npm install -g @anthropic-ai/claude-code
    info "Claude Code installed. Run 'claude login' to authenticate."
fi

info "=== Phase 0.4: Python tools (uv, mutmut, vulture, etc.) ==="
if command -v uv &>/dev/null; then
    info "uv already installed"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# Source uv for this session (required even if already installed)
[ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"
export PATH="$HOME/.local/bin:$PATH"

# Install Python CLI tools via uv tool (PEP 668 safe, no --break-system-packages)
for tool in mutmut vulture ruff pytest hypothesis; do
    if command -v "$tool" &>/dev/null; then
        info "$tool already installed"
    else
        uv tool install "$tool" && info "Installed $tool" || warn "Failed to install $tool"
    fi
done
# pytest plugins need to go into pytest's tool venv
uv tool install pytest --with pytest-cov --with pytest-asyncio 2>/dev/null || true

info "=== Phase 0.5: Clone project to WSL2 native filesystem ==="
CANVAS_DIR="$HOME/canvas/canvas-learning-system"
if [ -d "$CANVAS_DIR/.git" ]; then
    info "Project already cloned at $CANVAS_DIR"
    cd "$CANVAS_DIR"
    git pull --rebase origin main 2>/dev/null || warn "git pull failed (may have local changes)"
else
    mkdir -p "$HOME/canvas"
    cd "$HOME/canvas"
    git clone https://github.com/oinani0721/canvas-learning-system-backup.git canvas-learning-system
    cd canvas-learning-system

    # Add origin remote (main repo)
    git remote add origin https://github.com/oinani0721/canvas-learning-system.git 2>/dev/null || true
    # Rename default remote to backup for consistency with Windows setup
    git remote rename origin backup 2>/dev/null || true
fi

info "=== Phase 0.5b: Install project dependencies ==="
cd "$CANVAS_DIR"

# Frontend deps
if [ -f "frontend/package.json" ]; then
    cd frontend && npm install && cd ..
    info "Frontend dependencies installed"
fi

# Backend deps (use uv venv to avoid PEP 668)
if [ -f "backend/pyproject.toml" ] || [ -f "backend/setup.py" ]; then
    cd backend
    if [ ! -d ".venv" ]; then
        uv venv
    fi
    uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
    cd ..
    info "Backend dependencies installed (in backend/.venv)"
    info "Activate with: source backend/.venv/bin/activate"
fi

info "=== Phase 0.6: Agent Teams environment ==="
# Persist CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
if ! grep -q "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'ENVEOF'

# Canvas Learning System - Agent Teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
ENVEOF
    info "Agent Teams env var added to ~/.bashrc"
fi

info "=== Phase 0.7: Verify Docker connectivity ==="
DOCKER_OK=true

# Check ollama
if curl -sf http://localhost:11434 >/dev/null 2>&1; then
    info "Ollama reachable at localhost:11434"
else
    warn "Ollama not reachable at localhost:11434 — start it on Windows first"
    DOCKER_OK=false
fi

# Check neo4j-test
if python3 -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7692', auth=('neo4j','testpassword'))
d.verify_connectivity()
d.close()
print('OK')
" 2>/dev/null; then
    info "neo4j-test reachable at localhost:7692"
else
    warn "neo4j-test not reachable — run: docker compose --profile test up -d neo4j-test"
    DOCKER_OK=false
fi

# Check neo4j (Graphiti)
if python3 -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7689', auth=('neo4j','demodemo'))
d.verify_connectivity()
d.close()
print('OK')
" 2>/dev/null; then
    info "neo4j (Graphiti) reachable at localhost:7689"
else
    warn "neo4j (Graphiti) not reachable at localhost:7689"
fi

echo ""
info "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. cd $CANVAS_DIR"
echo "  2. claude login          # authenticate (opens Windows browser)"
echo "  3. bash wsl2-verify.sh   # run full verification"
echo "  4. tmux new-session -s dev"
echo "  5. ./ralph-runner.sh     # start the Ralph Loop"
echo ""
if [ "$DOCKER_OK" = false ]; then
    warn "Some Docker services not reachable. On Windows, run:"
    echo "  docker compose --profile test up -d neo4j-test ollama"
fi
echo ""
echo "Windows file access: \\\\wsl\$\\Ubuntu-24.04$CANVAS_DIR"
