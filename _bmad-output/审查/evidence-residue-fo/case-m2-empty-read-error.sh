#!/bin/bash
# CASE m2 — 空清单 + read 报错: SEEN==EXPECTED==0 也能走到 OK(Codex round-1 MEDIUM)
# 自述: round-1 的「消费条数 == 清单里的 NUL 数」只说明**没少读**, 不说明**读到过**。
#       暂存面为空(或全在允许名单内)时清单是空的, 此时把记录流换成目录, read 照样报错,
#       但 SEEN=EXPECTED=0 ⇒ 比较通过, hits 也正常空 ⇒ round-1 版块打 OK 退 0。
#       round-2 往流末追了一条结束哨兵(绝不可能是真实路径), 主循环必须真的读到它 ⇒ 退 1。
# ⚠️ 这一条的「旧版」= round-1 的 commit cd31cffd(已带 SEEN/EXPECTED), 不是 B14_BASE ——
#    要证的是「计数相等仍不够」, 拿没有计数的 B14_BASE 当旧版会把两件事混在一起。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE m2: 空清单下的读取错误 ==="
BASE_SHA=cd31cffd
prepare_blocks || exit 1
echo "⚠️ 本条的旧版 = round-1 commit cd31cffd(已含 SEEN/EXPECTED 比较), 不是 B14_BASE"

inject_before_loop 'mv "$TMPD/names" "$TMPD/names.orig" && mkdir "$TMPD/names"   # 注入: 记录流换成目录'

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
echo "输入: **零暂存文件**(清单为空) + 与 8-2 同一注入点、同一注入文本"
echo -n "旁证: 空暂存面的枚举字节数 = "
( cd "$REPO" && "$REAL_GIT" --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AMT -z | wc -c | tr -d ' ' ); echo

run_both m2 "$REPO"
