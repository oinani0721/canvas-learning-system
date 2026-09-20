#!/bin/zsh
# CARD-G8-10 r11 —— UAT 引用产物 ↔ git 树的「名实一致」审计（r10-M2 定向）
#   口径：把 UAT（§九 r8/r9/r10/r11 段）里引用的 evidence-g810 产物名逐条对 `git cat-file -e <REF>:<path>`；
#        任一名在 REF 树中不存在 ⇒ 该条 FAIL，整体 rc=1。（REF 默认 HEAD）
#   用法: zsh g810-r11-artifact-audit.zsh [REF]
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
UAT=_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md
REF=${1:-HEAD}
TS=$(date +%Y%m%dT%H%M%S)
OUT=$EV/artifact-audit-r11-$TS.txt
REFSHA=$(git rev-parse "$REF")

python3 - "$UAT" "$EV" "$REF" "$OUT" <<'PY'
import re, subprocess, sys, pathlib
uat, ev, ref, out = sys.argv[1:5]
text = pathlib.Path(uat).read_text(encoding="utf-8")
i = text.find("29. **r8 开工自证")
seg = text[i:] if i > 0 else text
names = sorted({n for n in re.findall(r"`([A-Za-z0-9_.\u4e00-\u9fff\-]+\.(?:txt|json|zsh|py|md))`", seg)
                if n.startswith(("g810-", "negctl-", "sidecar-", "jev-triage-", "anchor-battery-", "yamlgate-",
                                 "regress-", "r8-startup-", "ghost-ref-", "review-high-", "artifact-audit-"))})
lines = [f"# CARD-G8-10 r11 UAT 产物审计（REF={ref} @ {subprocess.run(['git','rev-parse','--short=8',ref],capture_output=True,text=True).stdout.strip()}）",
         f"# 口径：UAT r8/r9/r10/r11 段引用的 evidence-g810 产物名 = {len(names)} 条；逐条 `git cat-file -e {ref}:{ev}/<name>`",
         "# 状态 名称"]
missing = []
for n in names:
    r = subprocess.run(["git", "cat-file", "-e", f"{ref}:{ev}/{n}"], capture_output=True)
    ok = r.returncode == 0
    if not ok:
        missing.append(n)
    lines.append(("OK   " if ok else "MISS ") + n)
lines.append(f"# tracked={len(names)-len(missing)} missing={len(missing)}")
if missing:
    lines.append("# missing_list=" + ",".join(missing))
pathlib.Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[-6:]))
sys.exit(1 if missing else 0)
PY
rc=$?
echo "rc=$rc" >> "$OUT"
echo "artifact_audit ref=$REFSHA rc=$rc file=$(basename $OUT)"
exit $rc
