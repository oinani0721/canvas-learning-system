#!/bin/zsh
# CARD-G8-10 r10 正常底账基线 + digest 重锚链 + tracked/untracked dirty 拆分自证
#   用法: zsh g810-r10-green.zsh [PREV_REF]   （PREV_REF 默认 ca597bbf = r8 收尾 commit，其上为 v4.6；
#   收尾/复跑时可显式传旧 ref，避免 HEAD 已换版时把旧 checker 也从 HEAD 取（同源 ⇒ 两值相等、标签失真）；
#   r10 修 r9-L1：标题与末行不再写死 "树内 v4.6 / v46@"，改用 here@$HERE）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r8gr.XXXXXX) || exit 1
OUT=$EV/g810-green-r10-$TS.txt
DUMMY=00000000000000000000000000000000
CHECKER=$EV/check_g810_refs.py
V46SHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
PREV=${1:-9a22c33b}
PREVS=$(git rev-parse --short=8 "$PREV") || exit 1
HERE=$(git rev-parse --short=8 HEAD)
git show "$PREV:$EV/check_g810_refs.py" > "$TMP/check_g810_refs_prev.py" || exit 1
VPREVSHA=$(shasum -a 256 "$TMP/check_g810_refs_prev.py" | awk '{print $1}')

d45=$(python3 "$TMP/check_g810_refs_prev.py" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p')
d46=$(python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p')
out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d46" 2>&1); rc=$?
out45=$(set +e; python3 "$TMP/check_g810_refs_prev.py" --ledger "$LEDGER" --root . --expect-digest "$d45" 2>&1); rc45=$?
{
  echo "# CARD-G8-10 r10 正常底账基线（canonical 底账；树内 checker 见 checker_here_sha256）"
  echo "# checker=$CHECKER"
  echo "# checker_here_sha256=$V46SHA"
  echo "# checker_prev_sha256(from $PREVS)=$VPREVSHA"
  echo "# ledger_sha=$(shasum -a 256 "$LEDGER" | awk '{print $1}')"
  echo "# ledger_sha_vs_HEAD=$(git show HEAD:"$LEDGER" | shasum -a 256 | awk '{print $1}')"
  echo "# --- digest 重锚链 ---"
  echo "# prev@$PREVS=$d45（改前，旧口径）"
  echo "# here@$HERE=$d46（树内 checker 新口径：+evidence 目录内容 +commit tree OID）"
  echo "# --- 旧 checker 对 canonical 底账复跑 ---"
  echo "$out45"
  echo "rc_prev=$rc45"
  echo "# --- 树内 checker 口径复跑（canonical 底账 + 重锚 digest）---"
  echo "expect_digest=$d46"
  echo "$out"
  echo "rc=$rc"
} > "$OUT"
echo "GREEN_R10 prev@$PREVS=$d45 here@$HERE=$d46 rc=$rc rc_prev=$rc45 file=$OUT"
