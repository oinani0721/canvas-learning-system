#!/bin/bash
# Run mutation testing on a specific module
# Usage: ./scripts/mutmut-targeted.sh app/services/review_service.py
#
# mutmut 3.x reads paths_to_mutate from pyproject.toml.
# This script temporarily overrides it for targeted runs.

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(cd .. && pwd)"

MODULE="${1:?Usage: $0 <module_path> (e.g., app/services/review_service.py)}"

if [ ! -f "$MODULE" ]; then
    echo "ERROR: File not found: $MODULE"
    exit 1
fi

# Activate venv
source .venv/bin/activate 2>/dev/null || true

echo "=== Mutation Testing: $MODULE ==="
echo "This may take several minutes (each mutant runs full pytest cycle)."
echo ""

# Backup pyproject.toml, set targeted path
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
cp "$PYPROJECT" "$PYPROJECT.bak"

# Use sed to replace paths_to_mutate
sed -i.tmp "s|paths_to_mutate = \[\"app/\"\]|paths_to_mutate = [\"$MODULE\"]|" "$PYPROJECT"

# Run mutmut
cd "$PROJECT_ROOT/backend"
mutmut run 2>&1 || true

echo ""
echo "=== Results ==="
mutmut results 2>&1 || true

# Restore pyproject.toml
mv "$PYPROJECT.bak" "$PYPROJECT"
rm -f "$PYPROJECT.tmp"

echo ""
echo "=== Done ==="
