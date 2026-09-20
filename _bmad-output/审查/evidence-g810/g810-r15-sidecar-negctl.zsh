#!/bin/zsh
# CARD-G8-10 r15 → r20.1 —— sidecar 生成器负控 v3（靶向化 + 标签断言；N1–N14 + 小写 verdict 正控 P3 + 孪生 T + 正控 P1=r16）
#   N1 abs / N2 .. / N3 非 UTF-8            → path_decoded=False
#   N4 files=[] calls=5（其余干净）          → partial-inconsistent
#   N5 code_files=["x.py"]（其余干净）        → partial-inconsistent
#   N6 双 Model 行（前 stale calls:0，后 calls:5）→ partial-inconsistent
#   N7 calls=0 但 标记人工审查 1/1            → partial-inconsistent
#   N8 JSON 缺 files/code_files 字段（calls=0, 0/0）→ partial-inconsistent
#   N9 缩进的第二条 Model 行（r15-M2）→ model-line-count
#   N10 仅表头、无数据行（r15-M3）→ verdict-missing
#   N11 与 JSON 不符的伪数据行（r16-M2）→ row-churn（行与 files 互核）
#   N12 克隆真实数值但改文件名（r17-M1）→ row-file
#   N13 加 evil- 前缀（r18-M1）→ row-file（路径边界后缀）
#   T  干净孪生（0 文件 + calls 0 + 0/0）      → rc=0 且 partial=true（证明 N4–N8 的红来自目标缺陷）
#   N13 加 evil- 前缀的同 basename（r18-M1）→ row-file（路径边界后缀，子串不算）
#   N14 basename 后加 -junk 尾串（r19-M1）→ row-file（必须**真后缀**）
#   P1 真实 r16（calls=1）→ rc=0
set -u
RUNNER_ABS=${0:A}
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r15sc.XXXXXX) || exit 1
OUT=$EV/sidecar-negctl-r15-$TS-$$.txt
GEN=$EV/g810-r8-sidecar.py
GEN_SHA=$(shasum -a 256 "$GEN" | awk '{print $1}')

mk() {  # $1=名 $2=完整 JSON 体 $3=stdout
  print -r -- "$2" > "$TMP/$1.json"
  print -r -- "$3" > "$TMP/$1.stdout"
}
JF='[{"file": "synthetic", "added": 1, "removed": 0, "runtime": 0.1, "risk": "logic", "risk_conf": 0.5, "urgency": 1.0, "urgency_conf": 0.5, "review": 0.5, "test": 0.5, "truncated": false, "flag": true}]'
BODY() {  # $1=name $2=code_files $3=files
  cat <<JSON
{"commit": "fixture", "ref": "deadbeef", "sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "model": "jev-1.13.0",
 "code_files": $2, "files": $3, "usage": {"input_tokens": 1, "output_tokens": 1}, "latency_ms": {"min": 1, "median": 1, "max": 1}}
JSON
}
S1='Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1
synthetic 1/1  0.1  1.00  0.50  0.50  logic  REVIEW
标记人工审查: 1/1'
S5='Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
S6='Model: jev-1.13.0 | calls: 0 | input_tokens: 0 | output_tokens: 0
Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
S7='Model: jev-1.13.0 | calls: 0 | input_tokens: 0 | output_tokens: 0
标记人工审查: 1/1'
S0='Model: jev-1.13.0 | calls: 0 | input_tokens: 0 | output_tokens: 0
标记人工审查: 0/0'
mk N1-abs "$(BODY N1 '["/tmp/x.py"]' "$JF")" "$S1"
mk N2-dotdot "$(BODY N2 '["../x.py"]' "$JF")" "$S1"
mk N3-badutf8 "$(BODY N3 '["\"a/\\377x.py\""]' "$JF")" "$S1"
mk N4-calls5 "$(BODY N4 '[]' '[]')" "$S5"
mk N5-codefiles "$(BODY N5 '["x.py"]' '[]')" "$S0"
mk N6-model2 "$(BODY N6 '[]' '[]')" "$S6"
mk N7-flag11 "$(BODY N7 '[]' '[]')" "$S7"
mk N8-nofields '{"commit": "fixture", "ref": "deadbeef", "sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "model": "jev-1.13.0", "usage": {}, "latency_ms": {}}' "$S0"
S9='Model: jev-1.13.0 | calls: 0 | input_tokens: 0 | output_tokens: 0
  Model: jev-1.13.0 | calls: 5 | input_tokens: 1 | output_tokens: 1
标记人工审查: 0/0'
S10='Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1
FILE                                                             CHURN    URG  REVIEW   TEST  RISK             VERDICT
标记人工审查: 1/1'
mk N9-indentmodel "$(BODY N9 '[]' '[]')" "$S9"
mk N10-headeronly "$(BODY N10 '["x.py"]' "$JF")" "$S10"
S11='Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1
fake-row +0/-0 0.1 0.2 0.3 0 PASS
标记人工审查: 1/1'
mk N11-fakerow "$(BODY N11 '["x.py"]' "$JF")" "$S11"
# N12：克隆真实 JEV 数值但把文件名换掉（r17-M1：行首列必须含 files[0] basename）
python3 - "$EV/jev-triage-4569aef4.json" "$(ls $EV/jev-triage-4569aef4-run-*.txt | head -1)" "$TMP/N12-rename.json" "$TMP/N12-rename.stdout" <<'PYX'
import pathlib, sys
jp, run, outj, outs = sys.argv[1:5]
pathlib.Path(outj).write_text(pathlib.Path(jp).read_text(encoding="utf-8"), encoding="utf-8")
t = pathlib.Path(run).read_text(encoding="utf-8")
pathlib.Path(outs).write_text(t.replace("g810-r8-sidecar.py", "ghost_file.py"), encoding="utf-8")
_pl = pathlib
_pl.Path(outs.replace("N12-rename", "N13-evilprefix")).write_text(
    t.replace("g810-r8-sidecar.py", "evil-g810-r8-sidecar.py"), encoding="utf-8")
_pl.Path(outj.replace("N12-rename", "N13-evilprefix")).write_text(
    _pl.Path(jp).read_text(encoding="utf-8"), encoding="utf-8")
_pl.Path(outs.replace("N12-rename", "N14-tailsuffix")).write_text(
    t.replace("g810-r8-sidecar.py", "g810-r8-sidecar.py-junk"), encoding="utf-8")
_pl.Path(outj.replace("N12-rename", "N14-tailsuffix")).write_text(
    _pl.Path(jp).read_text(encoding="utf-8"), encoding="utf-8")
PYX
mk T-twin "$(BODY T '[]' '[]')" "$S0"

{
  echo "# CARD-G8-10 r15 sidecar 生成器负控 v3（靶向 + 孪生正控）"; echo "# generator=$GEN"; echo "# generator_sha256=$GEN_SHA"
} > "$OUT"
BAD=0
run() {  # $1=名 $2=期望 rc $3=期望标签（'none' = 不检查）
  local n=$1 want=$2 label=$3 o rc ok=yes
  o=$(set +e; python3 "$GEN" --json "$TMP/$n.json" --stdout "$TMP/$n.stdout" --out "$TMP/$n.sidecar.json" --allow-empty 2>&1); rc=$?
  [[ $rc == $want ]] || ok=NO
  if [[ $label != none ]]; then print -r -- "$o" | grep -q -- "$label" || ok=NO; fi
  { echo "--- $n（期望 rc=$want${label:+ 且含 '$label'}）---"; print -r -- "$o"; echo "rc=$rc assert=$ok"; } >> "$OUT"
  echo "[$n] rc=$rc assert=$ok"; [[ $ok == yes ]] || BAD=1
}
run N1-abs 1 "path_decoded=False"
run N2-dotdot 1 "path_decoded=False"
run N3-badutf8 1 "path_decoded=False"
run N4-calls5 1 "partial-inconsistent"
run N5-codefiles 1 "partial-inconsistent"
run N6-model2 1 "model-line-count"
run N7-flag11 1 "partial-inconsistent"
run N8-nofields 1 "partial-inconsistent"
run N9-indentmodel 1 "model-line-count"
run N10-headeronly 1 "verdict-missing"
run N11-fakerow 1 "row-churn"
run N12-rename 1 "row-file"
run N13-evilprefix 1 "row-file"
run N14-tailsuffix 1 "row-file"
run T-twin 0 "none"
# P3：小写 `pass` verdict 行（r20.1：白名单大小写不敏感；转录原样）——用真实 r20 JEV 输入
o3=$(set +e; python3 "$GEN" --json "$EV/jev-triage-74746264.json" --stdout "$(ls $EV/jev-triage-74746264-run-*.txt | head -1)" --out "$TMP/P3.json" --round r20 2>&1); r3=$?
grep -q '"verdict": "pass"' "$TMP/P3.json" && ok3=yes || ok3=NO
{ echo "--- P3（真实 r20，小写 verdict，期望 rc=0 且 verdict=\"pass\"）---"; print -r -- "$o3"; echo "rc=$r3 assert=$ok3"; } >> "$OUT"
echo "[P3] rc=$r3 assert=$ok3"; [[ $r3 == 0 && $ok3 == yes ]] || BAD=1
grep -q '"partial": true' "$TMP/T-twin.sidecar.json" && echo "[T-twin] partial=true ✓" || { echo "[T-twin] partial 缺失"; BAD=1; }
o1=$(set +e; python3 "$GEN" --json "$EV/jev-triage-884af91a.json" --stdout "$(ls $EV/jev-triage-884af91a-run-*.txt | head -1)" --out "$TMP/P1.json" --round r16 2>&1); r1=$?
{ echo "--- P1（真实 r16，期望 rc=0）---"; print -r -- "$o1"; echo "rc=$r1"; } >> "$OUT"
echo "[P1] rc=$r1"; [[ $r1 == 0 ]] || BAD=1
print -r -- "verdict_bad=$BAD" >> "$OUT"
[[ $BAD == 0 ]] && echo "R15_SIDECAR_NEGCTL ok file=$OUT" || echo "R15_SIDECAR_NEGCTL BAD=$BAD file=$OUT"
