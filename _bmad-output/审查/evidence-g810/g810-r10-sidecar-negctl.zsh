#!/bin/zsh
# CARD-G8-10 r10 —— sidecar 生成器的路径校验负控（r9-M4 定向）
#   三个反例（应 rc=1 且 path_decoded=false）：
#     N1 绝对路径 "/tmp/x.py" / N2 相对越界 "../x.py" / N3 非 UTF-8 字节（git 八进制转义 \377）
#   一个正控（应 rc=0 且 path_decoded=true）：r9 真实 JEV 产物
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r10sc.XXXXXX) || exit 1
OUT=$EV/sidecar-negctl-r10-$TS.txt
GEN=$EV/g810-r8-sidecar.py
GEN_SHA=$(shasum -a 256 "$GEN" | awk '{print $1}')

mk_fixture() {  # $1=名 $2=code_files 的 JSON 片段（已含引号转义）
  local name=$1 frag=$2
  cat > "$TMP/$name.json" <<JSON
{
  "commit": "synthetic-fixture ($name)",
  "ref": "deadbeef",
  "sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
  "model": "jev-1.13.0",
  "code_files": [$frag],
  "files": [{"file": "synthetic", "added": 1, "removed": 0, "runtime": 0.1, "risk": "logic", "risk_conf": 0.5, "urgency": 1.0, "urgency_conf": 0.5, "review": 0.5, "test": 0.5, "truncated": false, "flag": true}],
  "usage": {"input_tokens": 1, "output_tokens": 1},
  "latency_ms": {"min": 1, "median": 1, "max": 1}
}
JSON
  printf 'Model: jev-1.13.0 | calls: 1 | input_tokens: 1 | output_tokens: 1\nsynthetic 1/1  0.1  1.00  0.50  0.50  logic  REVIEW\n标记人工审查: 1/1\n' > "$TMP/$name.stdout"
}

mk_fixture N1-abs '"/tmp/x.py"'
mk_fixture N2-dotdot '"../x.py"'
mk_fixture N3-badutf8 '"\"a/\\377x.py\""'

{
  echo "# CARD-G8-10 r10 sidecar 生成器路径校验负控（r9-M4）"
  echo "# generator=$GEN"
  echo "# generator_sha256=$GEN_SHA"
  echo "# 口径：生成器 rc!=0 且 sidecar.path_decoded==false 且 path_validation_failures 非空 = 负控生效"
} > "$OUT"

BAD=0
for n in N1-abs N2-dotdot N3-badutf8; do
  o=$(set +e; python3 "$GEN" --json "$TMP/$n.json" --stdout "$TMP/$n.stdout" --out "$TMP/$n.sidecar.json" 2>&1); rc=$?
  dec=$(python3 - "$TMP/$n.sidecar.json" <<'PY' 2>/dev/null || echo "PARSE_FAIL"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"path_decoded={d['path_decoded']} failures={d['path_validation_failures']}")
PY
)
  {
    echo "--- $n（期望 rc=1 / path_decoded=false）---"
    echo "$o"
    echo "rc=$rc"
    echo "$dec"
  } >> "$OUT"
  echo "[$n] rc=$rc $dec"
  [[ $rc == 1 ]] || BAD=1
  echo "$o" | grep -q "path_decoded=False" || BAD=1
done

# 正控：真实 r9 产物
o=$(set +e; python3 "$GEN" --json "$EV/jev-triage-9a22c33b.json" --stdout "$(ls $EV/jev-triage-9a22c33b-run-*.txt | head -1)" --out "$TMP/P-sidecar.json" --round r9 2>&1); rc=$?
{
  echo "--- P-positive（真实 r9 JEV 产物；期望 rc=0 / path_decoded=True）---"
  echo "$o"
  echo "rc=$rc"
} >> "$OUT"
echo "[P-positive] rc=$rc"
[[ $rc == 0 ]] || BAD=1
echo "$o" | grep -q "path_decoded=True" || BAD=1
echo "verdict_bad=$BAD" >> "$OUT"
if [[ $BAD == 0 ]]; then echo "R10_SIDECAR_NEGCTL ok file=$OUT"; else echo "R10_SIDECAR_NEGCTL BAD=$BAD file=$OUT"; fi
