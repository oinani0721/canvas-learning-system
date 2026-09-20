#!/bin/zsh
# CARD-G8-10 r14 —— sidecar 生成器负控 v2（带**目标标签断言**；r13-M4/M5/L4 整改）
#   反例（各断言 rc=1 且输出含指定标签）：
#     N1 abs / N2 .. / N3 非 UTF-8         → 期望标签 path_decoded=False
#     N4 files=[] calls=5 / N5 code_files 非空 → partial-inconsistent
#     N6 stdout 前部散文 `calls: 0` + Model 行 `calls: 5`（解析锚定测试）→ partial-inconsistent
#     N7 Model 行 calls: 0 但 `标记人工审查: 1/1` → partial-inconsistent
#   正控：P1 真实 r13（calls=1）rc=0；P2 真实 r12b（0 文件 0/0）rc=0 且 partial=true
set -u
RUNNER_ABS=${0:A}
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r14sc.XXXXXX) || exit 1
OUT=$EV/sidecar-negctl-r14-$TS-$$.txt
GEN=$EV/g810-r8-sidecar.py
GEN_SHA=$(shasum -a 256 "$GEN" | awk '{print $1}')

mk() {  # $1=名 $2=code_files 片段 $3=files JSON $4=stdout 文本
  cat > "$TMP/$1.json" <<JSON
{"commit": "synthetic-fixture ($1)", "ref": "deadbeef", "sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
 "model": "jev-1.13.0", "code_files": [$2], "files": $3,
 "usage": {"input_tokens": 1, "output_tokens": 1}, "latency_ms": {"min": 1, "median": 1, "max": 1}}
JSON
  print -r -- "$4" > "$TMP/$1.stdout"
}
JF='[{"file": "synthetic", "added": 1, "removed": 0, "runtime": 0.1, "risk": "logic", "risk_conf": 0.5, "urgency": 1.0, "urgency_conf": 0.5, "review": 0.5, "test": 0.5, "truncated": false, "flag": true}]'
S1='Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1
synthetic 1/1  0.1  1.00  0.50  0.50  logic  REVIEW
标记人工审查: 1/1'
S5='Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
S6='Commit: old | calls: 0
Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
S7='Model: jev-1.13.0 | calls: 0 | input_tokens: 0 | output_tokens: 0
标记人工审查: 1/1'
mk N1-abs '"/tmp/x.py"' "$JF" "$S1"
mk N2-dotdot '"../x.py"' "$JF" "$S1"
mk N3-badutf8 '"\"a/\\377x.py\""' "$JF" "$S1"
mk N4-calls5 '""' '[]' "$S5"
mk N5-codefiles '""' '[]' "$S1"
mk N6-spoof '""' '[]' "$S6"
mk N7-flag11 '""' '[]' "$S7"

{
  echo "# CARD-G8-10 r14 sidecar 生成器负控 v2（tag 断言）"; echo "# generator=$GEN"; echo "# generator_sha256=$GEN_SHA"
} > "$OUT"
BAD=0
run() {  # $1=名 $2=期望标签
  local n=$1 label=$2 o rc ok=yes
  o=$(set +e; python3 "$GEN" --json "$TMP/$n.json" --stdout "$TMP/$n.stdout" --out "$TMP/$n.sidecar.json" --allow-empty 2>&1); rc=$?
  [[ $rc == 1 ]] || ok=NO
  print -r -- "$o" | grep -q -- "$label" || ok=NO
  { echo "--- $n（期望 rc=1 且含 '$label'）---"; print -r -- "$o"; echo "rc=$rc assert=$ok"; } >> "$OUT"
  echo "[$n] rc=$rc assert=$ok"; [[ $ok == yes ]] || BAD=1
}
run N1-abs "path_decoded=False"
run N2-dotdot "path_decoded=False"
run N3-badutf8 "path_decoded=False"
run N4-calls5 "partial-inconsistent"
run N5-codefiles "partial-inconsistent"
run N6-spoof "partial-inconsistent"
run N7-flag11 "partial-inconsistent"
o1=$(set +e; python3 "$GEN" --json "$EV/jev-triage-c84a0cc4.json" --stdout "$(ls $EV/jev-triage-c84a0cc4-run-*.txt | head -1)" --out "$TMP/P1.json" --round r13 2>&1); r1=$?
o2=$(set +e; python3 "$GEN" --json "$EV/jev-triage-4c5777d0.json" --stdout "$(ls $EV/jev-triage-4c5777d0-run-*.txt | head -1)" --out "$TMP/P2.json" --round r12b --allow-empty 2>&1); r2=$?
ok2=yes
[[ $r1 == 0 && $r2 == 0 ]] || ok2=NO
grep -q '"partial": true' "$TMP/P2.json" || ok2=NO
{ echo "--- P1（真实 r13，期望 rc=0）---"; print -r -- "$o1"; echo "rc=$r1";
  echo "--- P2（真实 r12b 0 文件，期望 rc=0 + partial=true）---"; print -r -- "$o2"; echo "rc=$r2 assert=$ok2"; } >> "$OUT"
echo "[P1] rc=$r1"; echo "[P2] rc=$r2 assert=$ok2"; [[ $ok2 == yes ]] || BAD=1
print -r -- "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R14_SIDECAR_NEGCTL ok file=$OUT" || echo "R14_SIDECAR_NEGCTL BAD=$BAD file=$OUT"
