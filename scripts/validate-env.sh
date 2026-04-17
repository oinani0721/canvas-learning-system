#!/usr/bin/env bash
set -euo pipefail

# Canvas Learning System — 环境变量验证脚本
# 检查 .env 是否存在、必需变量是否已设置、docker-compose 是否合法

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

errors=0
warnings=0

echo "═══════════════════════════════════════════════════════════════"
echo " Canvas Learning System — 环境变量验证"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# --- 1. Check .env exists ---
ENV_FILE="$PROJECT_ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}✗${NC} .env 文件不存在"
    echo "  → 运行: cp .env.example .env"
    echo "  → 然后编辑 .env 填入你的路径和密码"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env 文件存在"

# --- 2. Load .env and check required variables ---
# shellcheck source=/dev/null
source "$ENV_FILE"

REQUIRED_VARS=(
    "NEO4J_PASSWORD:Neo4j 数据库密码（至少 8 位）"
    "CANVAS_BASE_PATH:Obsidian vault 目录路径"
)

OPTIONAL_VARS=(
    "NEO4J_USER:Neo4j 用户名（默认 neo4j）"
    "NEO4J_HTTP_PORT:Neo4j HTTP 端口（默认 7478）"
    "NEO4J_BOLT_PORT:Neo4j Bolt 端口（默认 7691）"
    "OLLAMA_HOST:Ollama API 地址"
    "API_PORT:后端 API 端口（默认 8001）"
    "CORS_ORIGINS:CORS 允许的来源"
    "VAULT_MOUNT_MODE:Vault 挂载模式 rw/ro（默认 rw）"
)

echo ""
echo "── 必需变量 ──"
for entry in "${REQUIRED_VARS[@]}"; do
    var_name="${entry%%:*}"
    var_desc="${entry#*:}"
    value="${!var_name:-}"
    if [[ -z "$value" ]]; then
        echo -e "${RED}✗${NC} $var_name 未设置  — $var_desc"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✓${NC} $var_name 已设置"
    fi
done

echo ""
echo "── 可选变量 ──"
for entry in "${OPTIONAL_VARS[@]}"; do
    var_name="${entry%%:*}"
    var_desc="${entry#*:}"
    value="${!var_name:-}"
    if [[ -z "$value" ]]; then
        echo -e "${YELLOW}○${NC} $var_name 未设置（将使用默认值）— $var_desc"
        warnings=$((warnings + 1))
    else
        echo -e "${GREEN}✓${NC} $var_name = $value"
    fi
done

# --- 3. Validate CANVAS_BASE_PATH exists on disk ---
if [[ -n "${CANVAS_BASE_PATH:-}" ]]; then
    echo ""
    if [[ -d "$CANVAS_BASE_PATH" ]]; then
        echo -e "${GREEN}✓${NC} CANVAS_BASE_PATH 目录存在: $CANVAS_BASE_PATH"
        md_count=$(find "$CANVAS_BASE_PATH" -name "*.md" -maxdepth 3 2>/dev/null | wc -l | tr -d ' ')
        echo "  → 发现 $md_count 个 .md 文件"
    else
        echo -e "${RED}✗${NC} CANVAS_BASE_PATH 目录不存在: $CANVAS_BASE_PATH"
        errors=$((errors + 1))
    fi
fi

# --- 4. Validate docker-compose config ---
echo ""
echo "── Docker Compose 验证 ──"
if command -v docker-compose &>/dev/null || command -v docker &>/dev/null; then
    if (cd "$PROJECT_ROOT" && docker compose config --quiet 2>/dev/null || docker-compose config --quiet 2>/dev/null); then
        echo -e "${GREEN}✓${NC} docker-compose.yml 配置合法（所有变量已替换）"
    else
        echo -e "${RED}✗${NC} docker-compose.yml 配置无效"
        errors=$((errors + 1))
    fi
else
    echo -e "${YELLOW}○${NC} Docker 未安装，跳过 Compose 验证"
fi

# --- Summary ---
echo ""
echo "═══════════════════════════════════════════════════════════════"
if [[ $errors -gt 0 ]]; then
    echo -e "${RED}✗ 发现 $errors 个错误${NC}，$warnings 个警告"
    echo "  请修复上述必需变量后重新运行此脚本"
    exit 1
else
    echo -e "${GREEN}✓ 验证通过${NC}，$warnings 个警告"
    echo "  可以运行: docker-compose up -d"
    exit 0
fi
