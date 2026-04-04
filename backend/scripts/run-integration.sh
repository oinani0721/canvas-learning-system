#!/bin/bash
# Run real Neo4j integration tests against docker neo4j-test container (port 7692)
# Usage: ./scripts/run-integration.sh [pytest args...]
# Example: ./scripts/run-integration.sh -k "test_neo4j" -v

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(cd .. && pwd)"

echo "=== Canvas Integration Test Runner ==="

# 1. Check if neo4j-test container is running
if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "canvas-learning-system-neo4j-test"; then
    echo "[Setup] Starting neo4j-test container..."
    cd "$PROJECT_ROOT" && docker compose --profile test up -d neo4j-test
    cd "$PROJECT_ROOT/backend"

    echo "[Setup] Waiting for Neo4j to be healthy..."
    for i in $(seq 1 30); do
        if docker exec canvas-learning-system-neo4j-test wget -q --spider http://localhost:7474 2>/dev/null; then
            echo "[Setup] Neo4j is ready."
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "[Setup] ERROR: Neo4j failed to start within 60s"
            exit 1
        fi
        sleep 2
    done
else
    echo "[Setup] neo4j-test container already running."
fi

# 2. Set environment for real Neo4j connection
export NEO4J_TEST_URI="bolt://localhost:7692"
export NEO4J_TEST_USER="neo4j"
export NEO4J_TEST_PASSWORD="testpassword"

# 3. Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 4. Run integration tests
echo "[Test] Running integration tests..."
python -m pytest tests/ \
    -m "integration" \
    --override-ini="addopts=" \
    -v --tb=short \
    "$@"

echo "=== Integration tests complete ==="
