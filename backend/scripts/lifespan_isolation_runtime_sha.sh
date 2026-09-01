#!/usr/bin/env bash
# 运行时文件门 —— 证明「跑测试没动生产运行时数据」。
#
# [BATCH-2026-09-01-第八批 / CARD-TEST-isolate-lifespan]
#
# 用法:
#   bash backend/scripts/lifespan_isolation_runtime_sha.sh -- <要跑的命令...>
#
# 例:
#   bash scripts/lifespan_isolation_runtime_sha.sh -- .venv/bin/pytest tests/api -q
#
# 判据: 三个受监视文件在命令前后 **逐字节相同**（sha256 相等，或前后都不存在）。
#       任一不同 → 打印 `RUNTIME-FILES: CHANGED` 并 exit 1。
#
# ## 这道门不比什么（诚实边界）
#
# * 只看这三个**具名**文件。lifespan 若写了别的路径（新增的日志/缓存/临时文件），
#   本门看不到 —— 它证明的是「这三个已知受害者没被动」，不是「全盘零写入」。
# * 只比首尾两个时刻。命令中途写进去、结束前又改回原内容，本门判 unchanged。
# * 不看 live vault、不看 Neo4j。数据库里被 DDL 改了 schema，本门照样绿
#   —— 那是 socket 门（backend/tests/support/live_port_guard.py）的职责。
# * `absent → absent` 与 `present 且 sha 不变` 同样算 unchanged；两者语义不同，
#   脚本会逐条打印实际状态，不要只看最后一行结论。
#
# 退出码:
#   1  = 文件被改（门的裁定）
#   其它 = 被包裹命令自己的退出码（测试红了照样透出来，不被门吞掉）

set -uo pipefail

# Codex round-2 HIGH：调用者可导出同名函数/PATH 劫持 shasum/awk（返回全零
# digest → 前后相等 → 假 unchanged）。锁死工具解析：固定 PATH + 清掉同名
# 导出函数，门自身的工具调用不接受外部注入。
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH
unset -f shasum awk grep shasum 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 受监视文件 —— 均 git-ignored 的运行时产物，均由 app/main.py 的 lifespan 链写。
#   bug_log.jsonl            <- app/services/bug_tracker.py
#   vault_index_pending.jsonl<- app/services/vault_index_orchestrator.py
#   outbox/events.jsonl      <- app/services/event_bus.py
WATCHED=(
  "${BACKEND_DIR}/data/bug_log.jsonl"
  "${BACKEND_DIR}/app/data/vault_index_pending.jsonl"
  "${BACKEND_DIR}/data/outbox/events.jsonl"
)
EXPECTED_WATCH_COUNT=3

# 自检: 监视清单不能悄悄变空/变短 —— 空清单会让本门「零比较、恒绿」。
if [ "${#WATCHED[@]}" -ne "${EXPECTED_WATCH_COUNT}" ]; then
  echo "RUNTIME-FILES: GATE-BROKEN — 监视清单有 ${#WATCHED[@]} 项, 期望 ${EXPECTED_WATCH_COUNT} 项" >&2
  exit 1
fi

if [ "${1:-}" != "--" ]; then
  echo "用法: bash $0 -- <command...>" >&2
  echo "  ('--' 之后的一切原样作为命令执行)" >&2
  exit 2
fi
shift
if [ "$#" -eq 0 ]; then
  echo "RUNTIME-FILES: GATE-BROKEN — '--' 之后没有命令; 拒绝空跑（空跑必然 unchanged, 是假绿）" >&2
  exit 2
fi

snapshot() {
  # 逐行输出 "<sha256|absent>  <path>"；顺序与 WATCHED 一致。
  # hash 管道任何一环失败（shasum 出错 / 结果非 64 位十六进制）都判门损坏，
  # 不允许「空 digest 前后相等 = unchanged」的假绿（Codex round-1 HIGH）。
  local f digest
  for f in "${WATCHED[@]}"; do
    if [ -f "$f" ]; then
      digest="$(shasum -a 256 "$f")" || {
        echo "RUNTIME-FILES: GATE-BROKEN — shasum 失败: $f" >&2
        exit 1
      }
      digest="$(printf '%s' "$digest" | awk '{print $1}')"
      if ! printf '%s' "$digest" | grep -qE '^[0-9a-f]{64}$'; then
        echo "RUNTIME-FILES: GATE-BROKEN — sha256 结果非 64-hex: '$digest' ($f)" >&2
        exit 1
      fi
      printf '%s  %s\n' "$digest" "$f"
    else
      printf 'absent  %s\n' "$f"
    fi
  done
}

# Codex round-2 MEDIUM：snapshot 失败必须**先于** wrapped command 拦截 ——
# 此时还没有 set -e，$( ) 内的 exit 1 不会中止脚本，必须显式查赋值返回码。
if ! BEFORE="$(snapshot)"; then
  echo "RUNTIME-FILES: GATE-BROKEN — before snapshot 失败，拒绝执行被包裹命令" >&2
  exit 1
fi
echo "=== RUNTIME-FILES before ($(date '+%Y-%m-%d %H:%M:%S %z')) ==="
echo "${BEFORE}"
echo "=== 执行被包裹命令 ==="
echo "\$ $*"

set +e
# 子 shell 执行：builtin（`exit 0`）/ eval / 函数定义都死在子壳里，
# 无法篡改本壳的 snapshot 函数、BEFORE 变量或跳过 after 快照（Codex round-1 HIGH）。
( "$@" )
CMD_RC=$?
set -e

if ! AFTER="$(snapshot)"; then
  echo "RUNTIME-FILES: GATE-BROKEN — after snapshot 失败" >&2
  exit 1
fi
echo "=== RUNTIME-FILES after ($(date '+%Y-%m-%d %H:%M:%S %z')) ==="
echo "${AFTER}"
echo "WRAPPED-COMMAND-EXIT: ${CMD_RC}"

if [ "${BEFORE}" != "${AFTER}" ]; then
  echo "RUNTIME-FILES: CHANGED"
  echo "--- diff (before vs after) ---"
  diff <(echo "${BEFORE}") <(echo "${AFTER}") || true
  exit 1
fi

echo "RUNTIME-FILES: unchanged"
exit "${CMD_RC}"
