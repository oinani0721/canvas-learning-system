#!/bin/bash
# Run Schemathesis contract tests against OpenAPI spec
# Usage: ./scripts/contract-test.sh [pytest args...]
# Example: ./scripts/contract-test.sh -v --hypothesis-seed=0

set -e
cd "$(dirname "$0")/.."

echo "=== Canvas Contract Test Runner (Schemathesis) ==="

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run contract tests with Schemathesis
echo "[Contract] Running OpenAPI contract tests..."
python -m pytest tests/contract/ \
    --override-ini="addopts=" \
    --no-cov \
    -v --tb=short \
    "$@"

echo "=== Contract tests complete ==="
