#!/bin/bash
# Canvas Learning System - PostToolUse Composite Oracle v2
# Tiers: smoke (2s) → impact-scoped unit (10-20s) → lint (1s) → dead code (1s)
# mutmut excluded (too slow for per-edit; run manually after bug fixes)
#
# fix-test-infra-paralysis Phase 0.2: every pytest invocation runs through
# scripts/run_cmd_capture.sh, which captures full output, propagates the
# original exit code, and prints `[TEST FAILURE]` + tmp file path + last N
# lines on failure. The previous `pytest ... | tail -N` pattern silently
# dropped non-zero exit codes (POSIX pipelines return only the rightmost
# command's exit status), so the redundant `[ $? -ne 0 ]` checks were
# operating on tail's exit code (always 0).

PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Resolve project root
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-/workspace}"
WRAPPER="$PROJECT_ROOT/scripts/run_cmd_capture.sh"

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

    # Tier 1: Smoke tests (2s) — app boots, health responds
    if [ -d "$PROJECT_ROOT/backend/tests/smoke" ]; then
        "$WRAPPER" --cwd "$PROJECT_ROOT/backend" --tail 80 -- \
            python -m pytest tests/smoke/ -x -q --no-cov --no-header --override-ini="addopts=" --tb=line || exit 1
    fi

    # Tier 2: Impact-scoped tests (10-20s) — only tests related to changed file
    cd "$PROJECT_ROOT/backend" || exit 1
    MODULE=$(echo "$FILE_PATH" | sed 's|.*/app/||;s|\.py$||;s|/|.|g')
    RELATED_TESTS=$(grep -rl "from app\.${MODULE}\|import.*$(basename "$FILE_PATH" .py)" tests/ 2>/dev/null | head -20 | tr '\n' ' ')
    if [ -n "$RELATED_TESTS" ]; then
        "$WRAPPER" --cwd "$PROJECT_ROOT/backend" --tail 120 -- \
            python -m pytest $RELATED_TESTS -m "not integration and not slow" -x -q --no-cov --no-header --override-ini="addopts=" --tb=short || exit 1
    fi

    # Tier 3: Dead code detection (1s) — vulture has no pipe so needs no wrapper
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

    "$WRAPPER" --cwd "$PROJECT_ROOT/backend" --tail 120 -- \
        python -m pytest "$FILE_PATH" -x -q --no-cov --no-header --override-ini="addopts=" --tb=short || exit 1

elif [[ "$FILE_PATH" == *"frontend/src/"* ]] && [[ "$FILE_PATH" != *".test."* ]]; then
    # stryker (frontend mutation testing) via wrapper for reliable exit-code propagation
    "$WRAPPER" --cwd "$PROJECT_ROOT/frontend" --tail 20 -- npx stryker run || exit 1
    # knip (frontend dead code/unused exports detection) — no pipe, safe to keep direct
    ( cd "$PROJECT_ROOT/frontend" && npx knip --production 2>&1 )
    [ $? -ne 0 ] && echo "UNUSED EXPORTS DETECTED" && exit 1
fi

exit 0
