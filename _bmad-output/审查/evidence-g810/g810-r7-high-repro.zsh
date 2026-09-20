#!/bin/zsh
# CARD-G8-10 r7 —— 复核 HIGH 的独立复现（PyYAML 重复 key last-write-wins 折叠）
# 输入 = 复核者给出的：criteria 追加 `- {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}`
# 期望（复核声称）：v4.5 rc=0（穿透）；对照（还原后）rc=0；底账 shasum 前后逐字同
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
CHECKER=$EV/check_g810_refs.py
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
TS=$(date +%Y%m%dT%H%M%S)
DUMMY=00000000000000000000000000000000
OUT=$EV/review-high-duplicate-key-repro-$TS.txt

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

led_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
python3 - "$LEDGER" <<'PY'
import sys
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().split("\n")
idx = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
assert len(idx) == 1, idx
lines.insert(idx[0] + 1, '  - {dim: observability-extra, outcome: "pa\\u0073s", outcome: not_yet, coverage: partial}')
open(p, "w", encoding="utf-8").write("\n".join(lines))
PY
d=$(digest_now)
o=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
# 同址解析证明（PyYAML 对重复 key 的 last-write-wins）
py=$(python3 - <<'PY'
import yaml
doc = yaml.safe_load('criteria:\n  - {dim: x, outcome: "pa\\u0073s", outcome: not_yet, coverage: partial}\n')
print("safe_load(criteria[0]) =", doc["criteria"][0])
PY
)
restore
led_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
[[ "$led_after" == "$led_before" ]] && same=yes || same=NO
cd=$(digest_now)
co=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$cd" 2>&1); crc=$?
{
  print -r -- "# CARD-G8-10 r7 复核 HIGH 独立复现（PyYAML 重复 outcome key 折叠）"
  print -r -- "# checker=$CHECKER"
  print -r -- "# checker_sha256=$CSHA"
  print -r -- "# ledger_sha_before=$led_before"
  print -r -- "# mutation: criteria 数组追加一行 - {dim: observability-extra, outcome: \"pa\\u0073s\", outcome: not_yet, coverage: partial}（同一 mapping 两个 outcome key）"
  print -r -- "# pyyaml 解析：$py"
  print -r -- "# re-anchored_expect_digest(mutated)=$d"
  print -r -- "--- negctl run（变异底账 + 重锚 digest）---"
  print -r -- "$o"
  print -r -- "neg_rc=$rc"
  print -r -- "--- control run（git show HEAD: 还原后同一树）---"
  print -r -- "$co"
  print -r -- "control_rc=$crc"
  print -r -- "ledger_sha_after=$led_after"
  print -r -- "sha_equal=$same"
  print -r -- "restore_method=git show HEAD:<ledger> > <ledger>; trap on EXIT; no stash/no checkout"
  print -r -- "verdict=复现成立：v4.5 对该输入 rc=$rc（无 pass-unsupported）——与 glm-5.3 r7 复核 HIGH-1 一致"
} > "$OUT"
echo "[high-repro] neg_rc=$rc control_rc=$crc sha_equal=$same"; echo "file=$OUT"
trap - EXIT
restore
