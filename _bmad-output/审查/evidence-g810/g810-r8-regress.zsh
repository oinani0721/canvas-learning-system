#!/bin/zsh
# CARD-G8-10 r8 回归负控（证「旧失败面未放宽」）：r6-A / r6-B / r7-A / r7-B / r7-H1 原形
#   用法: zsh g810-r8-regress.zsh <pre|post>   （pre = v4.5 从 HEAD 提取；post = 树内 v4.6）
#   期望：r6-A / r6-B / r7-A / r7-B 两相位都 rc=1（v4.5 已闭合，v4.6 不得放宽）；
#         r7-H1 原形 = v4.5 rc=0（穿透）→ v4.6 rc=1（本轮闭合）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
PHASE=${1:-post}
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r8rg.XXXXXX) || exit 1
OUT=$EV/regress-r8-$PHASE-$TS.txt
DUMMY=00000000000000000000000000000000

if [[ $PHASE == pre ]]; then
  git show HEAD:"$EV/check_g810_refs.py" > "$TMP/check_g810_refs_v45.py" || exit 1
  CHECKER=$TMP/check_g810_refs_v45.py
else
  CHECKER=$EV/check_g810_refs.py
fi
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

mutate() {
  python3 - "$1" "$LEDGER" <<'PY'
import sys
name, path = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (name, "needle", s.count(old), old[:80])
    s = s.replace(old, new, n)
def insert_after_canon(line_text):
    global s
    lines = s.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
    assert len(idx) == 1, idx
    lines.insert(idx[0] + 1, line_text)
    s = "\n".join(lines)
if name == "r6-A":
    insert_after_canon('  - {dim: observability-extra, outcome: "pass", coverage: partial}')
elif name == "r7-A":
    insert_after_canon('  - {dim: observability-extra, outcome: "pa\\u0073s", coverage: partial}')
elif name == "r7-B":
    insert_after_canon('  - {dim: observability-extra, outcome: &not_yet pass, coverage: partial}')
elif name == "r7-H1":
    insert_after_canon('  - {dim: observability-extra, outcome: "pa\\u0073s", outcome: not_yet, coverage: partial}')
elif name == "r6-B":
    rep("`G4-3`（总账 v2", "`张三` / `G4-3`（总账 v2")
else:
    raise SystemExit(f"unknown case {name}")
open(path, "w", encoding="utf-8").write(s)
PY
}

{
  echo "# CARD-G8-10 r8 回归负控（相位 $PHASE）"
  echo "# checker=$CHECKER"
  echo "# checker_sha256=$CSHA"
  echo "# canonical_ledger_sha256=$(git show HEAD:"$LEDGER" | shasum -a 256 | awk '{print $1}')"
} > "$OUT"

BAD=0
case_run() {  # $1=case $2=期望 rc $3=说明
  local name=$1 want=$2 desc=$3
  local led_before d out rc ctrl_d ctrl_out ctrl_rc led_after same verdict
  led_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  mutate "$name" || { echo "MUTATION FAILED $name"; return 1; }
  d=$(digest_now)
  out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
  restore
  led_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  ctrl_d=$(digest_now)
  ctrl_out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl_d" 2>&1); ctrl_rc=$?
  [[ "$led_after" == "$led_before" ]] && same=yes || same=NO
  [[ $rc == $want ]] && verdict=ok || verdict=MISMATCH
  {
    print -r -- "--- case: $name（相位 $PHASE）---"
    print -r -- "# mutation: $desc"
    print -r -- "# re-anchored_expect_digest(mutated)=$d"
    print -r -- "$out"
    print -r -- "neg_rc=$rc expected_rc=$want verdict=$verdict"
    print -r -- "# --- control run（还原后同一树）---"
    print -r -- "$ctrl_out"
    print -r -- "control_rc=$ctrl_rc"
    print -r -- "ledger_sha_before=$led_before ledger_sha_after=$led_after sha_equal=$same"
  } >> "$OUT"
  echo "[$name/$PHASE] neg_rc=$rc want=$want $verdict sha_equal=$same"
  [[ $verdict == ok && $same == yes && $ctrl_rc == 0 ]] || BAD=1
}

if [[ $PHASE == pre ]]; then WANT=1; WANT_H1=0; else WANT=1; WANT_H1=1; fi
case_run r6-A  $WANT    'criteria 追加 - {dim: observability-extra, outcome: "pass", coverage: partial}（r6-H1 引号字面标量）'
case_run r6-B  $WANT    '检索链 owner cell：`G4-3` → `张三` / `G4-3`（r6-H2 反引号内伪 owner）'
case_run r7-A  $WANT    'criteria 追加 - {dim: observability-extra, outcome: "pa\u0073s", coverage: partial}（r7 转义双引号标量）'
case_run r7-B  $WANT    'criteria 追加 - {dim: observability-extra, outcome: &not_yet pass, coverage: partial}（r7 anchor 标量）'
case_run r7-H1 $WANT_H1 'criteria 追加 - {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}（r7-H1 复核原形：重复 key）'

{
  echo "# --- 收尾（还原后 canonical 复跑）---"
  GREEN_D=$(digest_now)
  GREEN_OUT=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$GREEN_D" 2>&1); GREEN_RC=$?
  print -r -- "expect_digest=$GREEN_D"
  print -r -- "$GREEN_OUT"
  print -r -- "rc=$GREEN_RC"
  print -r -- "phase=$PHASE verdict_bad=$BAD"
} >> "$OUT"
trap - EXIT
restore
if [[ $BAD == 0 ]]; then echo "R8_REGRESS_DONE phase=$PHASE ok file=$OUT"; else echo "R8_REGRESS_DONE phase=$PHASE BAD=$BAD file=$OUT"; fi
