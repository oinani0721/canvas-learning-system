#!/bin/bash
# Canvas Learning System - Ralph Loop Runner
# Orchestrates iterative /auto-epic sessions until all Epics complete.
# Works in both Docker and WSL2 environments.

set -uo pipefail

[ ! -f "PRD.md" ] && echo "ERROR: PRD.md required in $(pwd)" && exit 1
[ ! -f "PROGRESS.md" ] && echo "# Progress" > PROGRESS.md

# Agent Teams: ensure env var is set for this session
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-1}"

# Docker compose command: v2 plugin (docker compose) or v1 standalone (docker-compose)
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE=""
fi

MAX=${1:-30}
I=0

while [ $I -lt $MAX ]; do
    grep -q "ALL_EPICS_COMPLETE" PROGRESS.md && echo "All done!" && break
    echo "=== Ralph Loop Iteration $I ==="

    # Every 10 iterations, restart neo4j-test to prevent OOM
    if [ $((I % 10)) -eq 0 ] && [ $I -gt 0 ] && [ -n "$DOCKER_COMPOSE" ]; then
        echo "Restarting neo4j-test (OOM prevention)..."
        $DOCKER_COMPOSE restart neo4j-test 2>/dev/null || true
        sleep 15
    fi

    claude -p "/auto-epic" --allowedTools "Read,Write,Edit,Bash,Grep,Glob,Agent"
    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo "Session error (exit $EXIT_CODE). Retry in 5s..."
        sleep 5
    fi

    git add -A && git commit -m "ralph-loop: iteration $I" 2>/dev/null
    I=$((I+1))
done

echo "Ralph Loop finished after $I iterations."
