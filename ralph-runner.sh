#!/bin/bash
# Canvas Learning System - Ralph Loop Runner
# Orchestrates iterative /auto-epic sessions until all Epics complete

[ ! -f "PRD.md" ] && echo "ERROR: PRD.md required" && exit 1
[ ! -f "PROGRESS.md" ] && echo "# Progress" > PROGRESS.md

MAX=${1:-30}
I=0

while [ $I -lt $MAX ]; do
    grep -q "ALL_EPICS_COMPLETE" PROGRESS.md && echo "All done!" && break
    echo "=== Ralph Loop Iteration $I ==="

    # Every 10 iterations, restart neo4j-test to prevent OOM
    if [ $((I % 10)) -eq 0 ] && [ $I -gt 0 ]; then
        echo "Restarting neo4j-test (OOM prevention)..."
        docker-compose restart neo4j-test
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
