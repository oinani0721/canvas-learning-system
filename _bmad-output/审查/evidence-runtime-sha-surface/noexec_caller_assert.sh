#!/usr/bin/env bash
# 调用方自证断言 —— shell 版（验收单原文之一）。
#
# ⛔ 诚实边界：本文件**自己也是 bash**，所以在 `SHELLOPTS=noexec` 的环境里它同样
#    只解析不执行 —— 它挡不住那个形态。它的用处是给「调用方环境是干净的、但门
#    可能因别的原因没跑完」的场合一个不只看 rc 的判据。**真正免疫 noexec 的断言
#    必须落在非 bash 进程**（Python / make / pytest），见 noexec_contract.py。
#
# 用法: bash noexec_caller_assert.sh <门绝对路径> [-- <被包裹命令...>]
set -uo pipefail
GATE="$1"; shift || true
if [ "${1:-}" = "--" ]; then shift; fi
if [ "$#" -eq 0 ]; then set -- /usr/bin/true; fi

out="$(bash "$GATE" -- "$@" 2>&1)"; rc=$?
if ! printf '%s\n' "$out" | grep -qE '^RUNTIME-FILES: (unchanged|CHANGED)$'; then
  printf 'GATE-DID-NOT-RUN — 门没有自报结论行；rc=%s 不足以判定通过（SHELLOPTS=noexec？解释器被换掉？）\n' \
    "$rc" >&2
  exit 1
fi
printf 'GATE-RAN rc=%s\n' "$rc"
exit "$rc"
