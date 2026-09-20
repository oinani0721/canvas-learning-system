#!/bin/zsh
# CARD-G8-10 r13 —— sidecar 生成器：路径校验（r9-M4）+ **PARTIAL 三方一致**（r12-M3）负控
#   反例：N1 绝对 / N2 `..` / N3 非 UTF-8 / **N4 files=[] 但 calls=5** / **N5 files=[] 但 code_files 非空**
#   正控：P1 真实 r12 JEV（calls=1）+ P2 真实 r12b（0 文件，--allow-empty）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r13sc.XXXXXX) || exit 1
OUT=$EV/sidecar-negctl-r13-$TS.txt
GEN=$EV/g810-r8-sidecar.py
GEN_SHA=$(shasum -a 256 "$GEN" | awk '{print $1}')

mk() {  # $1=名 $2=code_files JSON 片段 $3=files JSON $4=stdout
  local name=$1 cf=$2 files=$3 sout=$4
  cat > "$TMP/$name.json" <<JSON
{
  "commit": "synthetic-fixture ($name)", "ref": "deadbeef",
  "sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "model": "jev-1.13.0",
  "code_files": [$cf], "files": $files,
  "usage": {"input_tokens": 1, "output_tokens": 1},
  "latency_ms": {"min": 1, "median": 1, "max": 1}
}
JSON
  print -r -- "$sout" > "$TMP/$name.stdout"
}

JFILE='[{"file": "synthetic", "added": 1, "removed": 0, "runtime": 0.1, "risk": "logic", "risk_conf": 0.5, "urgency": 1.0, "urgency_conf": 0.5, "review": 0.5, "test": 0.5, "truncated": false, "flag": true}]'
STD1='Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1
synthetic 1/1  0.1  1.00  0.50  0.50  logic  REVIEW
标记人工审查: 1/1'
STD5='Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
mk N1-abs '"/tmp/x.py"' "$JFILE" "$STD1"
mk N2-dotdot '"../x.py"' "$JFILE" "$STD1"
mk N3-badutf8 '"\"a/\\377x.py\""' "$JFILE" "$STD1"
mk N4-calls5 '""' '[]' "$STD5"
mk N5-codefiles '""' '[]' "$STD1"

{
  echo "# CARD-G8-10 r13 sidecar 生成器负控（r9-M4 路径 + r12-M3 PARTIAL 三方一致）"
  echo "# generator=$GEN"; echo "# generator_sha256=$GEN_SHA"
  echo "# 口径：负例 = rc=1 且（path_decoded=false 或 partial-inconsistent 记录）；正控 = rc=0"
} > "$OUT"

BAD=0
for n in N1-abs N2-dotdot N3-badutf8 N4-calls5 N5-codefiles; do
  o=$(set +e; python3 "$GEN" --json "$TMP/$n.json" --stdout "$TMP/$n.stdout" --out "$TMP/$n.sidecar.json" --allow-empty 2>&1); rc=$?
  { echo "--- $n（期望 rc=1）---"; echo "$o"; echo "rc=$rc"; } >> "$OUT"
  echo "[$n] rc=$rc"; [[ $rc == 1 ]] || BAD=1
done
# 正控 P1/P2
o1=$(set +e; python3 "$GEN" --json "$EV/jev-triage-2e52f551.json" --stdout "$(ls $EV/jev-triage-2e52f551-run-*.txt | head -1)" --out "$TMP/P1.json" --round r12 2>&1); r1=$?
o2=$(set +e; python3 "$GEN" --json "$EV/jev-triage-4c5777d0.json" --stdout "$(ls $EV/jev-triage-4c5777d0-run-*.txt | head -1)" --out "$TMP/P2.json" --round r12b --allow-empty 2>&1); r2=$?
{ echo "--- P1（真实 r12，期望 rc=0）---"; echo "$o1"; echo "rc=$r1";
  echo "--- P2（真实 r12b 0 文件 + --allow-empty，期望 rc=0 且 partial）---"; echo "$o2"; echo "rc=$r2"; } >> "$OUT"
echo "[P1] rc=$r1"; echo "[P2] rc=$r2"
[[ $r1 == 0 && $r2 == 0 ]] || BAD=1
grep -q '"partial": true' "$TMP/P2.json" && echo "[P2] partial=true ✓" || { echo "[P2] partial 缺失"; BAD=1; }
echo "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R13_SIDECAR_NEGCTL ok file=$OUT" || echo "R13_SIDECAR_NEGCTL BAD=$BAD file=$OUT"
