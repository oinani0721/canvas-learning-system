#!/bin/zsh
# CARD-G8-10 r7 —— v4.5 YAML 门新增失败分支控制（证「0 块 / 解析失败 / import 失败必须红」+ 同类标量变体）
#   C1 no-yaml-block  : 摘掉 §3 两条围栏 → 期望 rc=1 含 yaml-blocks
#   C2 yaml-parse-error: 块内注入未闭合 flow mapping → 期望 rc=1 含 yaml-parse-error
#   C3 yaml-missing   : PYTHONPATH 放一个 raise ImportError 的 yaml.py → 期望 rc=1 含 yaml-missing
#   C4 blockscalar-pass: 块内追加 block scalar（> 折叠）pass → 期望 rc=1 含 pass-unsupported
#   C5 tag-pass       : 块内追加 `outcome: !!str pass` → 期望 rc=1 含 pass-unsupported
# 每条：只改一层 → 重锚 digest → 跑 → git show HEAD:<底账> 还原 → 对照 rc=0
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
CHECKER=$EV/check_g810_refs.py
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r7br.XXXXXX) || exit 1
OUT=$EV/yamlgate-branches-r7-v45-$TS.txt
DUMMY=00000000000000000000000000000000

restore() { git show HEAD:"$LEDGER" > "$LEDGER"; }
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

mutate() {  # $1 = 分支名
  python3 - "$1" "$LEDGER" <<'PY'
import sys
name, path = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().split("\n")
canon = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
assert len(canon) == 1, canon
if name == "C1-no-yaml-block":
    fences = [i for i, l in enumerate(lines) if l.strip() in ("```yaml", "```")]
    assert len(fences) >= 2, fences
    for i in sorted(fences[:2], reverse=True):
        del lines[i]
elif name == "C2-yaml-parse-error":
    lines.insert(canon[0] + 1, "  - {dim: broken-gate, outcome: not_yet")
elif name == "C4-blockscalar-pass":
    lines[canon[0] + 1 : canon[0] + 1] = ["  - dim: observability-extra-bs", "    outcome: >", "      pass", "    coverage: partial"]
elif name == "C5-tag-pass":
    lines.insert(canon[0] + 1, "  - {dim: observability-extra-tag, outcome: !!str pass, coverage: partial}")
else:
    raise SystemExit(f"unknown branch {name}")
open(path, "w", encoding="utf-8").write("\n".join(lines))
PY
}

{
  echo "# CARD-G8-10 r7 YAML 门分支控制（checker v4.5）  checker_sha256=$CSHA"
  echo "# 口径：每条控制只改一层；改后重锚 --expect-digest；跑完 git show HEAD:<底账> 还原（不留改动）"
  echo "# ledger_sha(canonical)=$(git show HEAD:"$LEDGER" | shasum -a 256 | awk '{print $1}')"
} > "$OUT"

FAILED=0
for c in C1-no-yaml-block C2-yaml-parse-error C4-blockscalar-pass C5-tag-pass; do
  led_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  mutate "$c" || { echo "MUTATE FAIL $c" >> "$OUT"; FAILED=1; continue; }
  d=$(digest_now)
  o=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
  restore
  led_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  [[ "$led_after" == "$led_before" ]] && same=yes || same=NO
  { print -r -- "--- branch: $c（mutated_digest=$d; sha_equal=$same）---"; print -r -- "$o"; print -r -- "rc=$rc"; } >> "$OUT"
  echo "[$c] rc=$rc :: $(print -r -- "$o" | head -1)"
  [[ $rc == 1 ]] || FAILED=1
  [[ $same == yes ]] || FAILED=1
done

# C3 yaml-missing：无底账改动；PYTHONPATH 前置一个 raise ImportError 的假 yaml.py
mkdir -p "$TMP/blockyaml"
printf 'raise ImportError("PyYAML blocked for branch control")\n' > "$TMP/blockyaml/yaml.py"
d=$(digest_now)
o=$(set +e; PYTHONPATH="$TMP/blockyaml" python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
{ print -r -- "--- branch: C3-yaml-missing（PYTHONPATH=$TMP/blockyaml，假 yaml.py=raise ImportError; mutated_digest=$d）---"; print -r -- "$o"; print -r -- "rc=$rc"; } >> "$OUT"
echo "[C3-yaml-missing] rc=$rc :: $(print -r -- "$o" | head -1)"
[[ $rc == 1 ]] || FAILED=1

ctrl=$(digest_now)
o=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl" 2>&1); rc=$?
{ print -r -- "--- control（canonical 还原后）---"; print -r -- "$o"; print -r -- "rc=$rc"; } >> "$OUT"
echo "[control] rc=$rc digest=$ctrl"
[[ $rc == 0 ]] || FAILED=1
trap - EXIT
restore
echo "BRANCHES_DONE failed=$FAILED file=$OUT"
