#!/bin/bash
# Canvas Learning System - Specification Tools Setup Script
#
# 一键安装规范文档自动化所需的工具。
#
# 使用方法:
#   chmod +x scripts/spec-tools/setup-spec-tools.sh
#   ./scripts/spec-tools/setup-spec-tools.sh

set -e

echo "=== Canvas Learning System - Specification Tools Setup ==="
echo ""

# 检测操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    CYGWIN*|MINGW*|MSYS*)    PLATFORM=Windows;;
    *)          PLATFORM="Unknown"
esac
echo "Detected platform: $PLATFORM"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 1. 安装 Node.js 工具
# ═══════════════════════════════════════════════════════════════════════════════
echo "📦 Installing Node.js tools..."

# Dredd - API 合约测试
echo "  - Installing Dredd..."
npm install -g dredd 2>/dev/null || echo "    (skipped - may need sudo)"

# Spectral - OpenAPI Linting
echo "  - Installing Spectral..."
npm install -g @stoplight/spectral-cli 2>/dev/null || echo "    (skipped - may need sudo)"

# Pact CLI
echo "  - Installing Pact CLI..."
npm install -g @pact-foundation/pact-cli 2>/dev/null || echo "    (skipped - may need sudo)"

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 2. 安装 oasdiff
# ═══════════════════════════════════════════════════════════════════════════════
echo "📦 Installing oasdiff..."

if command -v oasdiff &> /dev/null; then
    echo "  oasdiff already installed: $(oasdiff --version 2>/dev/null || echo 'unknown version')"
else
    case "${PLATFORM}" in
        Mac)
            if command -v brew &> /dev/null; then
                brew install oasdiff 2>/dev/null || echo "  (skipped - brew install failed)"
            else
                echo "  Please install Homebrew first, then run: brew install oasdiff"
            fi
            ;;
        Linux)
            echo "  Installing from GitHub releases..."
            curl -sSL https://github.com/Tufin/oasdiff/releases/latest/download/oasdiff_linux_amd64.tar.gz | tar xz
            sudo mv oasdiff /usr/local/bin/ 2>/dev/null || mv oasdiff ~/.local/bin/
            ;;
        Windows)
            echo "  For Windows, download from: https://github.com/Tufin/oasdiff/releases"
            echo "  Or use: go install github.com/tufin/oasdiff@latest"
            ;;
        *)
            echo "  Unknown platform. Please install manually from:"
            echo "  https://github.com/Tufin/oasdiff/releases"
            ;;
    esac
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 安装 Python 依赖
# ═══════════════════════════════════════════════════════════════════════════════
echo "📦 Installing Python dependencies..."

cd backend 2>/dev/null || cd ../backend 2>/dev/null || echo "  (backend directory not found)"

if [ -f "requirements.txt" ]; then
    pip install pact-python pytest-asyncio 2>/dev/null || echo "  (skipped - pip install failed)"
fi

cd ..

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 4. 安装前端依赖
# ═══════════════════════════════════════════════════════════════════════════════
echo "📦 Installing frontend dependencies..."

FRONTEND_DIR="canvas-progress-tracker/obsidian-plugin"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"

    echo "  Installing Pact and MSW..."
    npm install @pact-foundation/pact msw --save-dev 2>/dev/null || echo "  (skipped - npm install failed)"

    echo "  Initializing MSW..."
    npx msw init public/ 2>/dev/null || echo "  (skipped - MSW init failed)"

    cd ../..
else
    echo "  Frontend directory not found: $FRONTEND_DIR"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 5. 验证安装
# ═══════════════════════════════════════════════════════════════════════════════
echo "=== Installation Summary ==="
echo ""

echo "Node.js tools:"
command -v dredd &> /dev/null && echo "  ✅ dredd: $(dredd --version 2>/dev/null | head -1)" || echo "  ❌ dredd: not installed"
command -v spectral &> /dev/null && echo "  ✅ spectral: $(spectral --version 2>/dev/null)" || echo "  ❌ spectral: not installed"
command -v pact &> /dev/null && echo "  ✅ pact-cli: installed" || echo "  ❌ pact-cli: not installed"

echo ""
echo "Go tools:"
command -v oasdiff &> /dev/null && echo "  ✅ oasdiff: installed" || echo "  ❌ oasdiff: not installed"

echo ""
echo "Python tools:"
python -c "import pact" 2>/dev/null && echo "  ✅ pact-python: installed" || echo "  ❌ pact-python: not installed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Run 'npm run test:pact' in frontend to generate pact files"
echo "  2. Run 'pytest tests/contract/' in backend to verify pacts"
echo "  3. Configure GitHub Actions secrets for Pact Broker (optional)"
echo ""
