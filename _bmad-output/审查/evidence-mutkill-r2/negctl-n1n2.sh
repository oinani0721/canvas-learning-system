#!/usr/bin/env bash
# (e) 两条承重负控的入口（裁判 6）。⛔ 只读工作树；门文件落 mkdtemp，跑完删。
set -u
TREE="$(cd "$(dirname "$0")/../../.." && pwd)"
exec "$TREE/backend/.venv/bin/python" "$TREE/_bmad-output/审查/evidence-mutkill-r2/negctl_n1n2.py" "$@"
