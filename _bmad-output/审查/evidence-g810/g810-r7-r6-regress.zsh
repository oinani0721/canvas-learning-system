#!/bin/zsh
# CARD-G8-10 r7 —— r6 两段定向负控在 v4.5 下的回归复跑（证「旧失败面未放宽」）
#   r6-A = criteria 追加 `outcome: "pass"`（引号字面标量）→ 期望 rc=1 含 pass-unsupported
#   r6-B = 检索链 owner cell 反引号内伪 owner `张三` / `G4-3` → 期望 rc=1 含 owner-invalid … '张三'
# 用法: zsh g810-r7-r6-regress.zsh
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
CHECKER=$EV/check_g810_refs.py
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
TS=$(date +%Y%m%dT%H%M%S)
DUMMY=00000000000000000000000000000000

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

mutate_A() {   # r6-A：引号字面 pass 标量
  python3 - "$LEDGER" <<'PY'
import sys
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().split("\n")
idx = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
assert len(idx) == 1, idx
lines.insert(idx[0] + 1, '  - {dim: observability-extra, outcome: "pass", coverage: partial}')
open(p, "w", encoding="utf-8").write("\n".join(lines))
PY
}

mutate_B() {   # r6-B：反引号内伪 owner
  python3 - "$LEDGER" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
needle = "`G4-3`（总账 v2"
assert s.count(needle) == 1, s.count(needle)
open(p, "w", encoding="utf-8").write(s.replace(needle, "`张三` / `G4-3`（总账 v2", 1))
PY
}

case_run() {
  local name=$1 fn=$2 desc=$3
  local led_before out rc digest ctrl_digest ctrl_out ctrl_rc led_after same
  led_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  $fn || { echo "MUTATION FAILED $name"; return 1; }
  digest=$(digest_now)
  out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$digest" 2>&1); rc=$?
  restore
  led_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  ctrl_digest=$(digest_now)
  ctrl_out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl_digest" 2>&1); ctrl_rc=$?
  [[ "$led_after" == "$led_before" ]] && same=yes || same=NO
  {
    print -r -- "# CARD-G8-10 r7 回归负控 $name（checker v4.5）"
    print -r -- "# checker=$CHECKER"
    print -r -- "# checker_sha256=$CSHA"
    print -r -- "# ledger_sha_before=$led_before"
    print -r -- "# mutation: $desc"
    print -r -- "# re-anchored_expect_digest(mutated)=$digest"
    print -r -- "--- negctl run（变异底账 + 重锚 digest）---"
    print -r -- "$out"
    print -r -- "neg_rc=$rc"
    print -r -- "--- control run（git show HEAD: 还原后同一树）---"
    print -r -- "$ctrl_out"
    print -r -- "control_rc=$ctrl_rc"
    print -r -- "ledger_sha_after=$led_after"
    print -r -- "sha_equal=$same"
    print -r -- "restore_method=git show HEAD:<ledger> > <ledger>; trap on EXIT; no stash/no checkout"
  } > "$EV/negctl-r6$name-regress-v45-$TS.txt"
  echo "[r6$name] neg_rc=$rc control_rc=$ctrl_rc sha_equal=$same file=negctl-r6$name-regress-v45-$TS.txt"
}

case_run A mutate_A 'criteria 数组追加一行: - {dim: observability-extra, outcome: "pass", coverage: partial}（r6-H1 原形）'
case_run B mutate_B '检索链 owner cell: `G4-3`（总账 v2 …  →  `张三` / `G4-3`（总账 v2 …（r6-H2 原形）'
trap - EXIT
restore
echo "REGRESS_DONE ts=$TS"
