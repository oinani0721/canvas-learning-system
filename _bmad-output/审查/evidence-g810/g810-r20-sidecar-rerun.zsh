#!/bin/zsh
# CARD-G8-10 r20 —— 用**当前生成器版本**对两轮真实 JEV 输入做干净复跑（r19-L1 补证）
#   目的：把 UAT「真实行 = rc=0」绑定到确切生成器 SHA（此前 r17/r18 sidecar 只记泛化名）
#   用法: zsh g810-r20-sidecar-rerun.zsh  → 产出 sidecar-rerun-<round>-<sha8>-<TAG>.json + 合并件（TAG 随生成器版本）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
GEN=$EV/g810-r8-sidecar.py
GEN_SHA=$(shasum -a 256 "$GEN" | awk '{print $1}')
TS=$(date +%Y%m%dT%H%M%S)
TAG=v49202                                   # 与生成器版本一致（v4.9-r20.2）
OUT=$EV/sidecar-rerun-r20.2-$TS-$$.txt
BAD=0
{
  echo "# CARD-G8-10 r20 sidecar 干净复跑（两轮真实 JEV 输入 × 当前生成器）"
  echo "# generator=$GEN"; echo "# generator_sha256=$GEN_SHA"
} > "$OUT"
for pair in "r17:4569aef4" "r18:5b581b0c"; do
  round=${pair%%:*}; sha=${pair##*:}
  json=$EV/jev-triage-$sha.json
  runlog=$(ls $EV/jev-triage-$sha-run-*.txt | head -1)
  outj=$EV/sidecar-rerun-$round-$sha-$TAG.json
  o=$(set +e; python3 "$GEN" --json "$json" --stdout "$runlog" --out "$outj" --round "$round" 2>&1); rc=$?
  { echo "--- $round（$sha）---"; print -r -- "$o"; echo "rc=$rc"; } >> "$OUT"
  echo "[$round/$sha] rc=$rc"
  [[ $rc == 0 ]] || BAD=1
done
echo "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R20_SIDECAR_RERUN ok file=$OUT" || echo "R20_SIDECAR_RERUN BAD=$BAD file=$OUT"
