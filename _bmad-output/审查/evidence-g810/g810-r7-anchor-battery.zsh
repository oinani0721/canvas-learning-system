#!/bin/zsh
# CARD-G8-10 r7 锚群复跑（v4.5；证「未放宽旧失败面」）：8 条旧锚形态逐条只改一层 → 重锚 digest → 跑 → git show 还原
# 用法: zsh g810-r7-anchor-battery.zsh
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
CHECKER=$EV/check_g810_refs.py
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
TS=$(date +%Y%m%dT%H%M%S)
DUMMY=00000000000000000000000000000000
OUT=$EV/anchor-battery-r7-v45-$TS.txt

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

mutate() {
  python3 - "$1" "$LEDGER" <<'PY'
import re, sys
name, path = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
def rep(old, new):
    global s
    assert s.count(old) >= 1, f"needle missing: {old!r}"
    s = s.replace(old, new, 1)
if name == "B-g99-plain":
    rep("`G4-3`（总账 v2", "G99（总账 v2")
elif name == "D-plain-name":
    rep("`G4-3`（总账 v2", "张三（总账 v2")
elif name == "G-mixed-owner":
    rep("`G4-3`（总账 v2", "张三 / `G4-3`（总账 v2")
elif name == "ref-missing":
    rep("`backend/app/models/service_status.py:39-45`", "`backend/app/models/no_such_file_g810r6.py:39-45`")
elif name == "quote-short":
    lines = s.split("\n")
    i = next(i for i, l in enumerate(lines) if l.startswith("| 复习链 |"))
    cells = lines[i].split("|")          # ["", 链, owner, 露出面, 文句, ...]
    before = cells[4]
    cells[4] = re.sub(r"「[^」]+」", "「四态一律」", cells[4], count=1)
    assert cells[4] != before, "quote cell unchanged"
    lines[i] = "|".join(cells)
    s = "\n".join(lines)
elif name == "nodeid-empty":
    rep("`backend/tests/unit/test_vault_lint.py::test_freshness_stale_and_corrupt_are_caught`",
        "`backend/tests/unit/test_vault_lint.py::`")
elif name == "dotdot-escape":
    rep("`backend/app/models/service_status.py:39-45`", "`../service_status_r6.py:39-45`")
elif name == "abs-path":
    rep("`backend/app/models/service_status.py:39-45`", "`/tmp/service_status_r6.py:39-45`")
else:
    raise SystemExit(f"unknown anchor {name}")
open(path, "w", encoding="utf-8").write(s)
PY
}

{
  echo "# CARD-G8-10 r7 锚群复跑（checker v4.5）  checker_sha256=$CSHA"
  echo "# 口径：每条锚只改一层；改后重锚 --expect-digest；跑完 git show HEAD:<底账> 还原（不留改动）"
  echo "# ledger_sha(canonical)=$(git show HEAD:"$LEDGER" | shasum -a 256 | awk '{print $1}')"
} > "$OUT"

FAILED=0
for a in B-g99-plain D-plain-name G-mixed-owner ref-missing quote-short nodeid-empty dotdot-escape abs-path; do
  mutate "$a" || { echo "MUTATE FAIL $a" >> "$OUT"; FAILED=1; continue; }
  d=$(python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p')
  o=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
  {
    echo "--- anchor: $a（mutated_digest=$d）---"
    echo "$o"
    echo "rc=$rc"
  } >> "$OUT"
  restore
  echo "[$a] rc=$rc :: $(print -r -- "$o" | head -1)"
  [[ $rc == 1 ]] || FAILED=1
done
ctrl=$(python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p')
o=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl" 2>&1); rc=$?
{ echo "--- control（canonical 还原后）---"; echo "$o"; echo "rc=$rc"; } >> "$OUT"
echo "[control] rc=$rc digest=$ctrl"
[[ $rc == 0 ]] || FAILED=1
trap - EXIT
restore
echo "BATTERY_DONE failed=$FAILED file=$OUT"
