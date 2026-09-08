#!/usr/bin/env bash
# (h) 信号负控入口（裁判 7）。⛔ 只对本脚本自造的临时文件发信号。
set -u
TREE="$(cd "$(dirname "$0")/../../.." && pwd)"
exec "$TREE/backend/.venv/bin/python" "$TREE/_bmad-output/审查/evidence-mutkill-r2/negctl_signal.py" "$@"
