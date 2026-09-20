#!/bin/zsh
# CARD-G8-10 r14 —— 审计 v2.5 控制组（带**目标标签断言**；r13-M5 整改）
#   C1 marker-missing / C1b marker-count / C2 excl-dead / C3 excl-empty-reason / C4 excl-duplicate
#   每条：构造 fixture ⇒ 跑 ⇒ 断言 rc=1 **且** 输出含指定标签；缺任一 ⇒ verdict_bad=1
set -u
RUNNER_ABS=${0:A}
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
UAT=_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r14ctl.XXXXXX) || exit 1
OUT=$EV/audit-ctl-r14-$TS-$$.txt
AUDIT=$EV/g810-r12-artifact-audit.zsh

python3 - "$UAT" "$TMP" <<'PY'
import pathlib, sys
uat, tmp = sys.argv[1], sys.argv[2]
base = pathlib.Path(uat).read_text(encoding="utf-8")
head = "## 十三 审计排除名单"
assert head in base, "§十三 标题缺失，fixture 无法构造"
# C2：在 §十三 段首注入死项；C3：注入空理由项；C4：注入与现有条目同名但空理由的重复项
first_dash = base.index("- `", base.index(head))
dead = base[:first_dash] + "- `ghost-never-mentioned-r14.txt` — 死项测试\n" + base[first_dash:]
empty = base[:first_dash] + "- `sidecar-g810-r9-9a22c33b.json` —\n" + base[first_dash:]
dup = base[:first_dash] + "- `scripts/jev_review_triage.py` — 重复项测试\n" + base[first_dash:]
# C1b：复制一份 marker（计数 2）
import re as _re
mm = _re.search(r"^29\. \*\*r8 开工自证", base, _re.M)
assert mm is not None, "marker missing"
assert len(_re.findall(r"^29\. \*\*r8 开工自证", base, _re.M)) == 1
marker2 = base[:mm.start()] + "29. **r8 开工自证（重复 fixture）\n" + base[mm.start():]
for name, txt in (("dead", dead), ("empty", empty), ("dup", dup), ("marker2", marker2)):
    pathlib.Path(f"{tmp}/uat-{name}.txt").write_text(txt, encoding="utf-8")
print("fixtures ok")
PY

{
  echo "# CARD-G8-10 r14 审计 v2.5 控制组（含目标标签断言；runner=$AUDIT）"
  echo "# C1 marker-missing（REF=dce85102） / C1b marker-count（fixture 双标记） / C2 excl-dead / C3 excl-empty-reason / C4 excl-duplicate"
} > "$OUT"

BAD=0
check() {  # $1=名 $2=期望标签 $3=实际输出 $4=rc
  local name=$1 label=$2 o=$3 rc=$4 ok=yes f
  [[ $rc == 1 ]] || ok=NO
  f=$(ls -t "$TMP"/artifact-audit-r12-*.txt 2>/dev/null | head -1)
  if [[ -z $f || ! -f $f ]]; then ok=NO; fi
  grep -q -- "$label" "${f:-/dev/null}" || ok=NO
  { echo "--- $name（期望 rc=1 且输出件含 '$label'）---"; print -r -- "$o"; echo "# 输出件=$(basename ${f:-none})"; echo "rc=$rc assert=$ok"; } >> "$OUT"
  echo "[$name] rc=$rc assert=$ok"
  [[ $ok == yes ]] || BAD=1
}
o=$(set +e; zsh "$AUDIT" dce85102 "$TMP" 2>&1); rc=$?; check C1 marker-count "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-marker2.txt" 2>&1); rc=$?; check C1b marker-count "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-dead.txt" 2>&1); rc=$?; check C2 excl-dead "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-empty.txt" 2>&1); rc=$?; check C3 excl-empty-reason "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-dup.txt" 2>&1); rc=$?; check C4 excl-duplicate "$o" $rc
print -r -- "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R14_AUDIT_CTL ok file=$OUT" || echo "R14_AUDIT_CTL BAD=$BAD file=$OUT"
