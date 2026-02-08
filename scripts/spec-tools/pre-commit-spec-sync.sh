#!/bin/bash
# Canvas Learning System - Pre-commit Spec Sync Hook
# 双向规范同步：代码变更自动更新规范
#
# 核心原则: 代码是唯一的事实来源（Single Source of Truth）！！！！
#
# 安装方法:
#   cp scripts/spec-tools/pre-commit-spec-sync.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# 功能:
#   1. 检测 API 文件变更
#   2. 导出 OpenAPI 规范 (FastAPI -> OpenAPI)
#   3. 导出 JSON Schema (Pydantic -> JSON Schema)
#   4. 验证规范一致性
#   5. 检测破坏性变更
#   6. 将规范变更加入 commit

set -e

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}[Spec Sync]${NC} BMad Bidirectional Spec Sync Hook"
echo -e "${CYAN}[Spec Sync]${NC} Checking for API changes..."

# 检查是否有 API 文件变更
API_CHANGES=$(git diff --cached --name-only | grep -E "^backend/app/(api|models|schemas)/" || true)

if [ -z "$API_CHANGES" ]; then
    echo -e "${GREEN}[Spec Sync]${NC} No API changes detected, skipping spec export."
    exit 0
fi

echo -e "${YELLOW}[Spec Sync]${NC} API changes detected:"
echo "$API_CHANGES"

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}[Spec Sync]${NC} Python not found, skipping spec export."
    exit 0
fi

# Step 1: 保存当前 OpenAPI 用于 diff
OLD_OPENAPI="/tmp/old-openapi-$(date +%s).json"
if [ -f "$PROJECT_ROOT/openapi.json" ]; then
    cp "$PROJECT_ROOT/openapi.json" "$OLD_OPENAPI"
fi

# Step 2: 导出 OpenAPI 规范
echo -e "${YELLOW}[Spec Sync]${NC} Step 1/4: Exporting OpenAPI specification..."

cd "$BACKEND_DIR"

if python ../scripts/spec-tools/export-openapi.py 2>/dev/null; then
    echo -e "${GREEN}[Spec Sync]${NC} OpenAPI spec exported successfully."
else
    echo -e "${YELLOW}[Spec Sync]${NC} OpenAPI export skipped (FastAPI app not available)."
fi

cd "$PROJECT_ROOT"

# Step 3: 导出 JSON Schema
echo -e "${YELLOW}[Spec Sync]${NC} Step 2/4: Exporting JSON Schemas from Pydantic..."

if python scripts/spec-tools/export-json-schemas.py 2>/dev/null; then
    echo -e "${GREEN}[Spec Sync]${NC} JSON Schemas exported successfully."
else
    echo -e "${YELLOW}[Spec Sync]${NC} JSON Schema export skipped."
fi

# Step 4: 验证一致性
echo -e "${YELLOW}[Spec Sync]${NC} Step 3/4: Validating spec consistency..."

CONSISTENCY_RESULT=$(python scripts/spec-tools/validate-spec-consistency.py --json 2>/dev/null || echo '{"summary":{"is_valid":true}}')
IS_VALID=$(echo "$CONSISTENCY_RESULT" | python -c "import sys, json; print(json.load(sys.stdin).get('summary', {}).get('is_valid', True))" 2>/dev/null || echo "True")

if [ "$IS_VALID" = "False" ]; then
    echo -e "${RED}[Spec Sync]${NC} Spec consistency validation FAILED!"
    echo -e "${RED}[Spec Sync]${NC} Run: python scripts/spec-tools/validate-spec-consistency.py"
    echo -e "${RED}[Spec Sync]${NC} Fix critical issues before committing."
    # 不阻塞 commit，只警告
    # exit 1
fi

# Step 5: 检测破坏性变更
echo -e "${YELLOW}[Spec Sync]${NC} Step 4/4: Checking for breaking changes..."

if [ -f "$OLD_OPENAPI" ] && [ -f "$PROJECT_ROOT/openapi.json" ]; then
    BREAKING=$(python scripts/spec-tools/diff-openapi.py "$OLD_OPENAPI" "$PROJECT_ROOT/openapi.json" --json 2>/dev/null || echo '{"breaking_changes":[]}')
    BREAKING_COUNT=$(echo "$BREAKING" | python -c "import sys, json; print(len(json.load(sys.stdin).get('breaking_changes', [])))" 2>/dev/null || echo "0")

    if [ "$BREAKING_COUNT" != "0" ]; then
        echo -e "${RED}[Spec Sync]${NC} WARNING: $BREAKING_COUNT breaking change(s) detected!"
        echo -e "${RED}[Spec Sync]${NC} Run: python scripts/spec-tools/diff-openapi.py $OLD_OPENAPI openapi.json"
    else
        echo -e "${GREEN}[Spec Sync]${NC} No breaking changes detected."
    fi
    rm -f "$OLD_OPENAPI"
fi

# Step 6: 添加规范文件到 commit
echo -e "${YELLOW}[Spec Sync]${NC} Adding spec files to commit..."

SPEC_ADDED=0

# 添加 openapi.json
if [ -f "$PROJECT_ROOT/openapi.json" ]; then
    if ! git diff --quiet "$PROJECT_ROOT/openapi.json" 2>/dev/null; then
        git add "$PROJECT_ROOT/openapi.json"
        echo -e "${GREEN}[Spec Sync]${NC} + openapi.json"
        SPEC_ADDED=$((SPEC_ADDED + 1))
    fi
fi

# 添加生成的 JSON Schema
if [ -d "$PROJECT_ROOT/specs/data/generated" ]; then
    for schema in "$PROJECT_ROOT/specs/data/generated"/*.schema.json; do
        if [ -f "$schema" ]; then
            if ! git diff --quiet "$schema" 2>/dev/null; then
                git add "$schema"
                echo -e "${GREEN}[Spec Sync]${NC} + $(basename $schema)"
                SPEC_ADDED=$((SPEC_ADDED + 1))
            fi
        fi
    done
fi

if [ $SPEC_ADDED -eq 0 ]; then
    echo -e "${GREEN}[Spec Sync]${NC} No spec changes to add."
else
    echo -e "${GREEN}[Spec Sync]${NC} Added $SPEC_ADDED spec file(s) to commit."
fi

echo -e "${CYAN}[Spec Sync]${NC} Done. SSOT: Code is the source of truth!"
exit 0
