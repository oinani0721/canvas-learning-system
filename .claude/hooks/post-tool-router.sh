#!/bin/bash
# Canvas Learning System - PostToolUse Composite Oracle v2
# Tiers: smoke (2s) → impact-scoped unit (10-20s) → lint (1s) → dead code (1s)
# mutmut excluded (too slow for per-edit; run manually after bug fixes)

PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Resolve project root
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-/workspace}"

if [[ "$FILE_PATH" == *"backend/app/"* ]] || [[ "$FILE_PATH" == *"backend/lib/"* ]]; then
    # Activate backend venv (has ruff, vulture, pytest, fastapi)
    if [ -f "$PROJECT_ROOT/backend/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/backend/.venv/bin/activate"
    elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    # Auto-format
    ruff format "$FILE_PATH" 2>/dev/null || true
    ruff check --fix "$FILE_PATH" 2>/dev/null || true

    echo "=== Composite Oracle: smoke → unit → vulture ==="
    cd "$PROJECT_ROOT/backend"

    # Tier 1: Smoke tests (2s) — app boots, health responds
    if [ -d "tests/smoke" ]; then
        python -m pytest tests/smoke/ -x -q --no-cov --no-header --override-ini="addopts=" --tb=line 2>&1 | tail -5
        [ $? -ne 0 ] && echo "SMOKE FAILED" && exit 1
    fi

    # Tier 2: Impact-scoped tests (10-20s) — only tests related to changed file
    MODULE=$(echo "$FILE_PATH" | sed 's|.*/app/||;s|\.py$||;s|/|.|g')
    RELATED_TESTS=$(grep -rl "from app\.${MODULE}\|import.*$(basename "$FILE_PATH" .py)" tests/ 2>/dev/null | head -20 | tr '\n' ' ')
    if [ -n "$RELATED_TESTS" ]; then
        python -m pytest $RELATED_TESTS -m "not integration and not slow" -x -q --no-cov --no-header --override-ini="addopts=" --tb=short 2>&1 | tail -20
        [ $? -ne 0 ] && echo "TEST FAILURES" && exit 1
    fi

    # Tier 3: Dead code detection (1s)
    vulture app/ --min-confidence 100 2>&1
    [ $? -ne 0 ] && echo "DEAD CODE DETECTED" && exit 1

    cd "$PROJECT_ROOT"

elif [[ "$FILE_PATH" == *"backend/tests/"* ]]; then
    # Test file edited — just run that test file
    if [ -f "$PROJECT_ROOT/backend/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/backend/.venv/bin/activate"
    elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    cd "$PROJECT_ROOT/backend"
    python -m pytest "$FILE_PATH" -x -q --no-cov --no-header --override-ini="addopts=" --tb=short 2>&1 | tail -20
    [ $? -ne 0 ] && exit 1
    cd "$PROJECT_ROOT"

elif [[ "$FILE_PATH" == *"frontend/src/"* ]] && [[ "$FILE_PATH" != *".test."* ]]; then
    cd "$PROJECT_ROOT/frontend"
    # stryker (frontend mutation testing)
    npx stryker run 2>&1 | tail -20
    [ $? -ne 0 ] && exit 1
    # knip (frontend dead code/unused exports detection)
    npx knip --production 2>&1
    [ $? -ne 0 ] && echo "UNUSED EXPORTS DETECTED" && exit 1
    cd "$PROJECT_ROOT"
fi

exit 0
