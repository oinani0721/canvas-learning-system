#!/bin/bash
# 安装 git hooks 到 .git/hooks/
# 用法: bash scripts/hooks/install.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

for hook in pre-commit post-commit pre-push; do
    if [ -f "$SCRIPT_DIR/$hook" ]; then
        cp "$SCRIPT_DIR/$hook" "$HOOKS_DIR/$hook"
        chmod +x "$HOOKS_DIR/$hook"
        echo "✅ Installed: $hook"
    fi
done

echo "Done. All hooks installed."
