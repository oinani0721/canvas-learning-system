#!/bin/zsh
# CARD-G8-10 r15 → r17 —— 审计 v2.6.3 控制组（标签断言 + invocation 绑定件；C1–C9）
#   C1 section-anchor / C2 marker-count / C3 marker-context / C4 excl-dead / C5 excl-empty-reason
#   C6 excl-duplicate / C7 excl-malformed / C8 28/29 间隙注入名 / C9 伪 `28.` 编号（r16-L1：编号须唯一且 …27,28）
set -u
RUNNER_ABS=${0:A}
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
UAT=_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r15ctl.XXXXXX) || exit 1
OUT=$EV/audit-ctl-r15-$TS-$$.txt
AUDIT=$EV/g810-r12-artifact-audit.zsh

python3 - "$UAT" "$TMP" <<'PY'
import pathlib, re, sys
uat, tmp = sys.argv[1], sys.argv[2]
base = pathlib.Path(uat).read_text(encoding="utf-8")
sec9 = re.search(r"^## 九 ", base, re.M)
assert sec9, "§九 标题缺失"
head = base.index("## 十三 审计排除名单")
first_dash = base.index("- `", head)
# C1：删掉 §九 标题行
c1 = base[:sec9.start()] + base[sec9.end():]
# C3：把标记行移到 §九 末尾（§十 之前）
mm = re.search(r"^29\. \*\*r8 开工自证.*$", base, re.M)
nxt = re.search(r"^## 十 ", base, re.M)
c3 = base[:mm.start()] + base[mm.end():]
nxt = re.search(r"^## 十 ", c3, re.M)
c3 = c3[:nxt.start()] + mm.group(0) + "\n" + c3[nxt.start():]
# C4 dead / C5 empty-reason / C6 duplicate / C7 malformed
c4 = base[:first_dash] + "- `ghost-never-mentioned-r15.txt` — 死项测试\n" + base[first_dash:]
c5 = base[:first_dash] + "- `scripts/jev_review_triage.py` —\n" + base[first_dash:]
c6 = base[:first_dash] + "- `scripts/jev_review_triage.py` — 重复项测试\n" + base[first_dash:]
c7 = base[:first_dash] + "- `scripts/jev_review_triage.py`（缺破折号理由）\n" + base[first_dash:]
# C8：在 28 项行与 29 项行之间插入一个未解引用名（r15-L1 的原始攻击）
m28 = list(re.finditer(r"^28\. ", base, re.M))[-1]
m29 = re.search(r"^29\. \*\*r8 开工自证", base, re.M)
c8 = base[:m29.start()] + "- `ghost-gap-r16.txt`（28/29 间隙注入）\n" + base[m29.start():]
# C9：在真实 28 项与 29 项之间插入伪 `28.` 行（并放一个名字，检验伪 28 是否被拦）
c9 = base[:m29.start()] + "28. filler（伪编号注入）\n- `ghost-dup28-r17.txt`\n" + base[m29.start():]
for name, txt in (("c1", c1), ("c3", c3), ("c4", c4), ("c5", c5), ("c6", c6), ("c7", c7), ("c8", c8), ("c9", c9)):
    pathlib.Path(f"{tmp}/uat-{name}.txt").write_text(txt, encoding="utf-8")
print("fixtures ok")
PY

{
  echo "# CARD-G8-10 r15 → r18 审计 v2.6.3 控制组 C1–C9（逐条断言 rc=1 + 目标标签；输出件按本次 invocation 的 file= 解析）"
} > "$OUT"

BAD=0
check() {  # $1=名 $2=期望标签 $3=运行输出 $4=rc
  local name=$1 label=$2 o=$3 rc=$4 ok=yes f
  [[ $rc == 1 ]] || ok=NO
  f=$(print -r -- "$o" | sed -n 's/.*file=\([^ ]*\)$/\1/p' | tail -1)
  f="$TMP/${f:-none}"                     # audit 的 stdout 只给 basename（`file=$(basename ...)`）⇒ 回到本次 OUTDIR
  if [[ -z ${f} || ! -f "$f" ]]; then ok=NO; fi
  grep -q -- "$label" "${f:-/dev/null}" || ok=NO
  { echo "--- $name（期望 rc=1 且输出件含 '$label'）---"; print -r -- "$o"; echo "# file=${f:-none}"; echo "rc=$rc assert=$ok"; } >> "$OUT"
  echo "[$name] rc=$rc assert=$ok"
  [[ $ok == yes ]] || BAD=1
}
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c1.txt" 2>&1); rc=$?; check C1-section-anchor section-anchor "$o" $rc
o=$(set +e; zsh "$AUDIT" dce85102 "$TMP" 2>&1); rc=$?; check C2-marker-count marker-count "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c3.txt" 2>&1); rc=$?; check C3-marker-context marker-context "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c4.txt" 2>&1); rc=$?; check C4-excl-dead excl-dead "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c5.txt" 2>&1); rc=$?; check C5-excl-empty-reason excl-empty-reason "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c6.txt" 2>&1); rc=$?; check C6-excl-duplicate excl-duplicate "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c7.txt" 2>&1); rc=$?; check C7-excl-malformed excl-malformed "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c8.txt" 2>&1); rc=$?; check C8-gap-name-in-face ghost-gap-r16.txt "$o" $rc
o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-c9.txt" 2>&1); rc=$?; check C9-dup28 marker-context "$o" $rc
print -r -- "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R15_AUDIT_CTL ok file=$OUT" || echo "R15_AUDIT_CTL BAD=$BAD file=$OUT"
