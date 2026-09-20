#!/bin/zsh
# CARD-G8-10 r6 负控运行器（两段：A=引号 pass 标量 / B=反引号内伪 owner）
# 用法: zsh g810-r6-negctl-runner.zsh <pre|post>
#   pre  = 用 v4.3（git show HEAD 提取）→ 复现两条 HIGH（负控不被拦下, 期望 rc=0）
#   post = 用树内修后 checker → 负控必红（A 含 pass-unsupported / B 含 owner-invalid）
# 每段：改一层 → 重锚 --expect-digest → 跑 → EXIT trap 用 git show HEAD:<底账> 还原 → 对照复跑 + shasum 逐字对
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
PHASE=${1:-post}
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r6.XXXXXX) || exit 1

if [[ $PHASE == pre ]]; then
  git show HEAD:"$EV/check_g810_refs.py" > "$TMP/check_g810_refs_v43.py" || exit 1
  CHECKER=$TMP/check_g810_refs_v43.py
else
  CHECKER=$EV/check_g810_refs.py
fi
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
DUMMY=00000000000000000000000000000000

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

mutate_A() {
  python3 - "$LEDGER" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
lines = s.split("\n")
idx = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
assert len(idx) == 1, idx
lines.insert(idx[0] + 1, '  - {dim: observability-extra, outcome: "pass", coverage: partial}')
open(p, "w", encoding="utf-8").write("\n".join(lines))
PY
}

mutate_B() {
  python3 - "$LEDGER" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
needle = "`G4-3`（总账 v2"
assert s.count(needle) == 1, s.count(needle)
s = s.replace(needle, "`张三` / `G4-3`（总账 v2", 1)
open(p, "w", encoding="utf-8").write(s)
PY
}

case_run() {  # $1=名字(A/B) $2=变异函数名 $3=变异描述
  local name=$1 fn=$2 desc=$3
  local led_sha_before out rc digest ctrl_digest ctrl_out ctrl_rc led_sha_after same
  led_sha_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  $fn || { echo "MUTATION FAILED $name"; return 1; }
  digest=$(digest_now)
  out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$digest" 2>&1); rc=$?
  restore
  led_sha_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  ctrl_digest=$(digest_now)
  ctrl_out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl_digest" 2>&1); ctrl_rc=$?
  if [[ "$led_sha_after" == "$led_sha_before" ]]; then same=yes; else same=NO; fi
  {
    echo "# CARD-G8-10 r6 负控 $name（相位 $PHASE）"
    echo "# checker=$CHECKER"
    echo "# checker_sha256=$CSHA"
    echo "# ledger_sha_before=$led_sha_before"
    echo "# mutation: $desc"
    echo "# re-anchored_expect_digest(mutated)=$digest"
    echo "--- negctl run（变异底账 + 重锚 digest）---"
    echo "$out"
    echo "neg_rc=$rc"
    echo "--- control run（git show HEAD: 还原后同一树）---"
    echo "$ctrl_out"
    echo "control_rc=$ctrl_rc"
    echo "ledger_sha_after=$led_sha_after"
    echo "sha_equal=$same"
    echo "restore_method=git show HEAD:<ledger> > <ledger>; trap on EXIT; no stash/no checkout"
  } > "$EV/negctl-$name-r6-$PHASE-$TS.txt"
  echo "[$name/$PHASE] neg_rc=$rc control_rc=$ctrl_rc sha_equal=$same file=negctl-$name-r6-$PHASE-$TS.txt"
}

case_run A mutate_A 'criteria 数组追加一行: - {dim: observability-extra, outcome: "pass", coverage: partial}'
case_run B mutate_B '检索链 owner cell: `G4-3`（总账 v2 …  →  `张三` / `G4-3`（总账 v2 …'

GREEN_DIGEST=$(digest_now)
GREEN_OUT=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$GREEN_DIGEST" 2>&1); GREEN_RC=$?
{
  echo "# CARD-G8-10 r6 正常底账基线（相位 $PHASE，还原后）"
  echo "# checker=$CHECKER"
  echo "# checker_sha256=$CSHA"
  echo "# ledger_status=$(git status --porcelain -- "$LEDGER" | wc -l | tr -d " ") 行脏"
  echo "# ledger_sha=$(shasum -a 256 "$LEDGER" | awk '{print $1}')"
  echo "expect_digest=$GREEN_DIGEST"
  echo "$GREEN_OUT"
  echo "rc=$GREEN_RC"
} > "$EV/g810-green-r6-$PHASE-$TS.txt"
echo "[green/$PHASE] rc=$GREEN_RC digest=$GREEN_DIGEST file=g810-green-r6-$PHASE-$TS.txt"
trap - EXIT
restore
echo "DONE phase=$PHASE ts=$TS"
