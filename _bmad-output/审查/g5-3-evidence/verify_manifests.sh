#!/bin/bash
# G5-3 — 证据自洽校验（Codex round-1 HIGH-3 / round-2 HIGH-3 的常驻判据）
#
# 「证据包绑定的是当前交付字节」这件事，一次性核对过没用 —— 文档一改就失效。
# 本脚本把它变成可随时复跑的一条命令：两份 manifest 全绿 + 绿证条数与实跑一致。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
fail=0

echo "== manifest 校验 =="
( cd "$REPO" && shasum -a 256 -c "$HERE/engine-and-products.sha256" ) || fail=1
( cd "$REPO" && shasum -a 256 -c "$HERE/judge-and-contract.sha256" ) || fail=1

echo
echo "== 绿证与实跑一致性 =="
claimed=$(grep -oE '[0-9]+ passed' "$HERE/pytest-green.txt" | head -1)
actual=$(cd "$REPO/backend" && ./.venv/bin/pytest tests/skills/ -q --no-header -p no:randomly -p no:cacheprovider 2>&1 | grep -oE '[0-9]+ passed' | head -1)
echo "pytest-green.txt 声称: ${claimed:-<无>} / 实跑: ${actual:-<无>}"
[ -n "$claimed" ] && [ "$claimed" = "$actual" ] || { echo "⛔ 绿证与实跑不一致"; fail=1; }

echo
[ "$fail" = 0 ] && echo "✅ 证据包自洽" || echo "⛔ 证据包不自洽"
exit $fail
