#!/bin/zsh
# CARD-G8-10 r13 —— 审计 v2.4 控制组（r12-M2 / r12-L1 定向）
#   C1 marker-missing      : REF=dce85102（其 UAT 在位但无 §九 `29. **r8 开工自证` 边界标记）⇒ 期望 rc=1 + marker-missing
#   C2 excl-dead           : UAT 覆盖文本追加一条「名字面内 0 命中」的排除项 ⇒ 期望 rc=1 + excl-dead
#   C3 excl-empty-reason   : UAT 覆盖文本追加一条空理由的排除项 ⇒ 期望 rc=1 + excl-empty-reason
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
UAT=_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r13ctl.XXXXXX) || exit 1
OUT=$EV/audit-ctl-r13-$TS.txt
AUDIT=$EV/g810-r12-artifact-audit.zsh

python3 - "$UAT" "$TMP" <<'PY'
import pathlib, sys
uat, tmp = sys.argv[1], sys.argv[2]
base = pathlib.Path(uat).read_text(encoding="utf-8")
marker = "- `negctl-r11-post-20260920T141449.txt`"
assert base.count(marker) >= 1
pathlib.Path(tmp + "/uat-dead.txt").write_text(base.replace(marker, "- `ghost-never-mentioned-r13.txt` — 死项测试\n" + marker, 1), encoding="utf-8")
pathlib.Path(tmp + "/uat-empty.txt").write_text(base.replace(marker, "- `sidecar-g810-r9-9a22c33b.json` —\n" + marker, 1), encoding="utf-8")
PY

{
  echo "# CARD-G8-10 r13 审计 v2.4 控制组（$AUDIT）"
  echo "# C1 marker-missing / C2 excl-dead / C3 excl-empty-reason；各只改一层；期望全 rc=1"
} > "$OUT"

BAD=0
o=$(set +e; zsh "$AUDIT" dce85102 "$TMP" 2>&1); rc=$?
{ echo "--- C1 marker-missing（REF=dce85102）---"; echo "$o"; echo "rc=$rc"; } >> "$OUT"
echo "[C1] rc=$rc :: $(print -r -- "$o" | head -1)"; [[ $rc == 1 ]] || BAD=1

o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-dead.txt" 2>&1); rc=$?
{ echo "--- C2 excl-dead（UAT 覆盖：追加死排除项）---"; echo "$o"; echo "rc=$rc"; } >> "$OUT"
echo "[C2] rc=$rc :: $(print -r -- "$o" | grep -m1 excl-dead || print -r -- "$o" | tail -1)"; [[ $rc == 1 ]] || BAD=1

o=$(set +e; zsh "$AUDIT" HEAD "$TMP" "$TMP/uat-empty.txt" 2>&1); rc=$?
{ echo "--- C3 excl-empty-reason（UAT 覆盖：空理由）---"; echo "$o"; echo "rc=$rc"; } >> "$OUT"
echo "[C3] rc=$rc :: $(print -r -- "$o" | grep -m1 excl-empty-reason || print -r -- "$o" | tail -1)"; [[ $rc == 1 ]] || BAD=1

echo "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R13_AUDIT_CTL ok file=$OUT" || echo "R13_AUDIT_CTL BAD=$BAD file=$OUT"
