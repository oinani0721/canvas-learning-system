#!/bin/bash
# Canvas Learning System - PostToolUse Composite Oracle
# Runs: pytest + mutmut + vulture (backend) or stryker + knip (frontend)
# Works in both Docker (/workspace) and WSL2/native ($CLAUDE_PROJECT_DIR) environments

PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Resolve project root: prefer $CLAUDE_PROJECT_DIR, fallback to /workspace (Docker)
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-/workspace}"

if [[ "$FILE_PATH" == *"backend/app/"* ]]; then
    echo "=== Composite Oracle: pytest + mutmut + vulture ==="
    cd "$PROJECT_ROOT/backend"

    # 1. pytest (unit tests only, skip integration/slow)
    python -m pytest tests/ -m "not integration and not slow" -q --tb=short 2>&1 | tail -20
    [ $? -ne 0 ] && echo "TEST FAILURES" && exit 1

    # 2. mutmut (only mutate the changed file, not full scan)
    RELATIVE=$(echo "$FILE_PATH" | sed 's|.*/backend/||')
    mutmut run --paths-to-mutate="$RELATIVE" 2>&1 | tail -20
    SURVIVING=$(mutmut results 2>/dev/null | grep -c "Survived" || echo "0")
    if [ "$SURVIVING" -gt 0 ]; then
        echo "FACADE DETECTED! $SURVIVING mutants survived."
        mutmut results 2>/dev/null | grep "Survived" | head -10
        exit 1
    fi

    # 3. vulture (dead code detection — catches broken pipelines)
    vulture app/ --min-confidence 100 2>&1
    [ $? -ne 0 ] && echo "DEAD CODE DETECTED" && exit 1

    cd "$PROJECT_ROOT"

elif [[ "$FILE_PATH" == *"backend/tests/"* ]]; then
    cd "$PROJECT_ROOT/backend"
    python -m pytest tests/ -m "not integration and not slow" -q --tb=short 2>&1 | tail -20
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
