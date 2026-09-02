#!/usr/bin/env bash
# 运行时文件门 —— 证明「跑测试没动生产运行时数据」。
#
# [BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]
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
# ## 为什么整段前言这么长（第八批 Codex HIGH 的直接整改）
#
# 上一版只做了「固定 PATH + unset -f shasum awk grep」。2026-09-03 实测三条绕过
# 全部成立、且三条都让门输出 `RUNTIME-FILES: unchanged` 且 rc=0：
#
#   1. `dirname() { printf '///data/nonexistent'; }; export -f dirname`
#      → 脚本监视 `//data/bug_log.jsonl` 等根本不存在的路径，三项 absent，假绿；
#   2. `printf() { builtin printf '%s' "000…0"; }; export -f printf`
#      → 所有摘要输出恒为同一串零，前后必然相等，假绿；
#   3. `BASH_ENV=<注入文件> bash 本脚本`
#      → 注入文件在脚本第 1 行之前被 source，可定义任意函数（含上面两个）。
#
# 本版的收口是「先把地基清干净，再让门证明自己算得对」：
#
#   * 清 `BASH_ENV`/`ENV`/`CDPATH`（它们只影响后续，已被 source 的内容靠下一条清）；
#   * `compgen -A function` 枚举并 `unset -f` **全部**函数（不只是三个名字）——
#     BASH_ENV 已经注入的函数在这一步被连根拔掉；
#   * `enable` 恢复可能被 `enable -n` 关掉的 builtin（printf/echo/test/[）；
#   * 外部命令一律**绝对路径**且逐个校验可执行；`dirname` 直接不用了，
#     改用 bash 参数展开 `${BASH_SOURCE[0]%/*}`；`awk`/`grep` 也不用了，
#     改用 builtin 的 `read` + `[[ =~ ]]`；
#   * **门自证**：先对一个常量串算 sha256 与钉死的期望值比对（见 SELFTEST_*）。
#     任何形式的哈希管道劫持（假 shasum / 假 printf / 假 read）都会让这一步失配。
#     这道自证是本门自己的验伪锚：门算错了要能说出来，而不是安静地判 unchanged。
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
# * 被包裹命令在**调用者的 PATH** 下执行（门只给自己锁 PATH）。门不为被包裹
#   命令的环境卫生背书。
#
# 退出码:
#   1  = 文件被改，或门自证失败（门的裁定）
#   2  = 用法错误
#   其它 = 被包裹命令自己的退出码（测试红了照样透出来，不被门吞掉）

set -uo pipefail

# ── 地基清理：顺序不能换 ────────────────────────────────────────────────
# BASH_ENV 指定的文件在本行之前就已经被 source 了；清掉它只防后续 bash 子进程，
# 真正拔掉其副作用靠下面的「unset 全部函数」。
unset BASH_ENV ENV CDPATH
# 枚举并清掉**全部** shell 函数（含 BASH_FUNC_* 导出进来的）。compgen 是 builtin。
for __fn in $(builtin compgen -A function 2>/dev/null); do
  builtin unset -f "$__fn" 2>/dev/null || true
done
unset __fn
# 恢复可能被 `enable -n` 关掉的 builtin —— 否则 printf/echo 会落到 PATH 上。
builtin enable printf echo test [ read 2>/dev/null || true
# 门自身的工具解析锁死在系统目录；被包裹命令另行恢复调用者 PATH（见下）。
CALLER_PATH="${PATH:-}"
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH

# ── 外部命令：绝对路径 + 存在性校验（不用 dirname/awk/grep）──────────────
SHA_CANDIDATES=(/usr/bin/shasum /usr/bin/sha256sum /bin/sha256sum)
SHA_BIN=""
SHA_ARGS=()
for __c in "${SHA_CANDIDATES[@]}"; do
  if [ -x "$__c" ]; then
    SHA_BIN="$__c"
    case "$__c" in
      */shasum) SHA_ARGS=(-a 256) ;;
      *) SHA_ARGS=() ;;
    esac
    break
  fi
done
unset __c
if [ -z "$SHA_BIN" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 找不到可执行的 sha256 工具 (%s)\n' "${SHA_CANDIDATES[*]}" >&2
  exit 1
fi
DATE_BIN=/bin/date
DIFF_BIN=/usr/bin/diff

# ── 门自证：常量串的 sha256 必须等于钉死值 ──────────────────────────────
# 这一步同时验证 SHA_BIN、builtin printf、builtin read 三者都没被掉包。
SELFTEST_INPUT='w4-runtime-sha-gate-selftest-v1'
SELFTEST_EXPECTED='82e87819dac824b894684638a188059759c99d793641765853e5c5cae20baa1c'

hash_stdin() {
  # 从 stdin 读内容，回显 64 位十六进制摘要；失败回显空串。
  local out digest rest
  out="$("$SHA_BIN" "${SHA_ARGS[@]}")" || return 1
  builtin read -r digest rest <<<"$out"
  builtin printf '%s' "$digest"
}

SELFTEST_ACTUAL="$(builtin printf '%s' "$SELFTEST_INPUT" | hash_stdin)"
if [ "$SELFTEST_ACTUAL" != "$SELFTEST_EXPECTED" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 门自证失败：sha256(%s) 期望 %s，实得 %s。\n' \
    "$SELFTEST_INPUT" "$SELFTEST_EXPECTED" "${SELFTEST_ACTUAL:-<空>}" >&2
  builtin printf '  哈希管道被劫持（假 shasum / 假 printf / 假 read / PATH 注入），本门的结论不可信。\n' >&2
  exit 1
fi

# ── 路径解析：不用 dirname（它可被导出函数劫持），用参数展开 ─────────────
__src="${BASH_SOURCE[0]}"
case "$__src" in
  */*) SCRIPT_DIR_RAW="${__src%/*}" ;;
  *) SCRIPT_DIR_RAW="." ;;
esac
SCRIPT_DIR="$(builtin cd "$SCRIPT_DIR_RAW" && builtin pwd -P)" || {
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 无法解析脚本目录 %s\n' "$SCRIPT_DIR_RAW" >&2
  exit 1
}
BACKEND_DIR="$(builtin cd "${SCRIPT_DIR}/.." && builtin pwd -P)" || {
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 无法解析 BACKEND_DIR\n' >&2
  exit 1
}
unset __src SCRIPT_DIR_RAW
# BACKEND_DIR 必须是一个**真的**后端目录，否则说明路径解析被人做了手脚
# （第八批的 dirname 劫持正是把它变成 `//`，三项 absent 假绿）。
if [ ! -f "${BACKEND_DIR}/app/main.py" ] || [ ! -d "${BACKEND_DIR}/tests" ]; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — BACKEND_DIR=%s 不像后端目录（缺 app/main.py 或 tests/）\n' \
    "$BACKEND_DIR" >&2
  exit 1
fi

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
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — 监视清单有 %s 项, 期望 %s 项\n' \
    "${#WATCHED[@]}" "${EXPECTED_WATCH_COUNT}" >&2
  exit 1
fi

if [ "${1:-}" != "--" ]; then
  builtin printf '用法: bash %s -- <command...>\n' "$0" >&2
  builtin printf "  ('--' 之后的一切原样作为命令执行)\n" >&2
  exit 2
fi
shift
if [ "$#" -eq 0 ]; then
  builtin printf "RUNTIME-FILES: GATE-BROKEN — '--' 之后没有命令; 拒绝空跑（空跑必然 unchanged, 是假绿）\n" >&2
  exit 2
fi

snapshot() {
  # 逐行输出 "<sha256|absent>  <path>"；顺序与 WATCHED 一致。
  # hash 管道任何一环失败（shasum 出错 / 结果非 64 位十六进制）都判门损坏，
  # 不允许「空 digest 前后相等 = unchanged」的假绿。
  local f digest
  for f in "${WATCHED[@]}"; do
    if [ -f "$f" ]; then
      digest="$(hash_stdin <"$f")" || {
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — sha256 失败: %s\n' "$f" >&2
        exit 1
      }
      if [[ ! "$digest" =~ ^[0-9a-f]{64}$ ]]; then
        builtin printf "RUNTIME-FILES: GATE-BROKEN — sha256 结果非 64-hex: '%s' (%s)\n" "$digest" "$f" >&2
        exit 1
      fi
      builtin printf '%s  %s\n' "$digest" "$f"
    else
      builtin printf 'absent  %s\n' "$f"
    fi
  done
}

# snapshot 失败必须**先于** wrapped command 拦截 —— 此时还没有 set -e，
# $( ) 内的 exit 1 不会中止脚本，必须显式查赋值返回码。
if ! BEFORE="$(snapshot)"; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — before snapshot 失败，拒绝执行被包裹命令\n' >&2
  exit 1
fi
builtin printf '=== RUNTIME-FILES before (%s) ===\n' "$("$DATE_BIN" '+%Y-%m-%d %H:%M:%S %z')"
builtin printf '%s\n' "${BEFORE}"
builtin printf '=== 执行被包裹命令 ===\n'
builtin printf '$ %s\n' "$*"

set +e
# 子壳执行：builtin（`exit 0`）/ eval / 函数定义都死在子壳里，无法篡改本壳的
# snapshot 函数、BEFORE 变量或跳过 after 快照。PATH 只在子壳里恢复成调用者的
# ——门自己的工具解析始终锁在系统目录（卡文 (h)：仅给 wrapped command 恢复 PATH）。
(
  PATH="${CALLER_PATH}"
  export PATH
  "$@"
)
CMD_RC=$?
set -e

if ! AFTER="$(snapshot)"; then
  builtin printf 'RUNTIME-FILES: GATE-BROKEN — after snapshot 失败\n' >&2
  exit 1
fi
builtin printf '=== RUNTIME-FILES after (%s) ===\n' "$("$DATE_BIN" '+%Y-%m-%d %H:%M:%S %z')"
builtin printf '%s\n' "${AFTER}"
builtin printf 'WRAPPED-COMMAND-EXIT: %s\n' "${CMD_RC}"

if [ "${BEFORE}" != "${AFTER}" ]; then
  builtin printf 'RUNTIME-FILES: CHANGED\n'
  builtin printf -- '--- diff (before vs after) ---\n'
  if [ -x "$DIFF_BIN" ]; then
    "$DIFF_BIN" <(builtin printf '%s\n' "${BEFORE}") <(builtin printf '%s\n' "${AFTER}") || true
  fi
  exit 1
fi

builtin printf 'RUNTIME-FILES: unchanged\n'
exit "${CMD_RC}"
