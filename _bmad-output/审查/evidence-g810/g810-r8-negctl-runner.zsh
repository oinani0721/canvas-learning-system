#!/bin/zsh
# CARD-G8-10 r8 负控运行器（r7-H1 / r5-M1 / r5-M2 / r6-M1 定向）
#   A-dup      : 重复显式 outcome key（先转义 pass 后 not_yet）——r7-H1 复核原形
#   B-merge    : merge 源内 `outcome: !!str pass`（显式 not_yet 覆盖 merge 结果）——r7-H1 merge hidden pass
#   C-alias    : 顶层 `seed_state: &p !!str pass` + merge 源内 `outcome: *p`——r7-H1 scalar alias
#   D-dotdot   : nodeid 路径 `backend/tests/../app/models/service_status.py::ServiceStatus`——r5-M1
#   E1-evdir   : evidence 目录引用改成不存在的同前缀路径——r5-M2（可解引用面）
#   E2-evdirmv : 物理移走 `_bmad-output/审查/evidence-g2-8/`（跑后原样搬回）——r5-M2（复核者原形）
#   F1-badsha  : 平文 SHA `6337e320` → 畸形值 `6337e32z8`——r5-M2（无效平文 SHA）
#   F2-substsha: 平文 SHA `6337e320` → 另一个**有效** commit `c53069d3`——r5-M2（digest 绑定组）
#   G-ownerpath: 检索链 owner cell 换成「文件名含 G4-3 的 path:line 引用」——r6-M1
# 用法: zsh g810-r8-negctl-runner.zsh <pre|post>
#   pre  = 用 v4.5（git show HEAD 提取）→ 期望 A–G 全穿透 neg_rc=0（F2 同 rc=0 但 digest 变）
#   post = 用树内 v4.6 → 期望 A–G 全红 neg_rc=1（F2 仍 rc=0 且 digest 变 = 绑定成立）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LEDGER=_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
EVDIR=_bmad-output/审查/evidence-g2-8
EVMOVED=_bmad-output/审查/evidence-g2-8.r8-moved
PHASE=${1:-post}
TS=$(date +%Y%m%dT%H%M%S)
TMP=$(mktemp -d /tmp/g810-r8.XXXXXX) || exit 1
OUT=$EV/negctl-r8-$PHASE-$TS.txt
DUMMY=00000000000000000000000000000000

if [[ $PHASE == pre ]]; then
  git show HEAD:"$EV/check_g810_refs.py" > "$TMP/check_g810_refs_v45.py" || exit 1
  CHECKER=$TMP/check_g810_refs_v45.py
else
  CHECKER=$EV/check_g810_refs.py
fi
CSHA=$(shasum -a 256 "$CHECKER" | awk '{print $1}')

restore() {
  git show HEAD:"$LEDGER" > "$LEDGER"
  if [[ -d "$EVMOVED" && ! -e "$EVDIR" ]]; then mv "$EVMOVED" "$EVDIR"; fi
}
trap 'restore' EXIT

digest_now() {
  python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$DUMMY" 2>&1 \
    | sed -n 's/.*source_digest=\([0-9a-f]\{32\}\).*/\1/p'
}

mutate() {  # $1 = case 名（文本级变异；E2 在 zsh 侧做物理移动）
  python3 - "$1" "$LEDGER" <<'PY'
import sys
name, path = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (name, "needle", s.count(old), old[:80])
    s = s.replace(old, new, n)
def insert_after_canon(line_text):
    global s
    lines = s.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip().startswith("- {dim: observability, c: 逐链归属表")]
    assert len(idx) == 1, idx
    lines.insert(idx[0] + 1, line_text)
    s = "\n".join(lines)
if name == "A-dup":
    insert_after_canon('  - {dim: observability-extra, outcome: "pa\\u0073s", outcome: not_yet, coverage: partial}')
elif name == "B-merge":
    insert_after_canon('  - {dim: observability-extra, outcome: not_yet, coverage: partial, <<: &extra {outcome: !!str pass}}')
elif name == "C-alias":
    lines = s.split("\n")
    ci = [i for i, l in enumerate(lines) if l == "criteria:"]
    assert len(ci) == 1, ci
    lines.insert(ci[0], "seed_state: &p !!str pass")
    s = "\n".join(lines)
    insert_after_canon('  - {dim: observability-extra, outcome: not_yet, coverage: partial, <<: {outcome: *p}}')
elif name == "D-dotdot":
    rep("`backend/tests/unit/test_service_status_contract.py::TestStatusedResultContract::test_unavailable_rejects_payload`",
        "`backend/tests/../app/models/service_status.py::ServiceStatus`")
elif name == "E1-evdir":
    rep("`_bmad-output/审查/evidence-g2-8/`", "`_bmad-output/审查/evidence-g2-8-nope-r8/`")
elif name == "F1-badsha":
    assert s.count("6337e320") == 3, s.count("6337e320")
    s = s.replace("6337e320", "6337e32z8", 2)
elif name == "F2-substsha":
    assert s.count("6337e320") == 3, s.count("6337e320")
    s = s.replace("6337e320", "c53069d3", 2)
elif name == "G-ownerpath":
    rep("`G4-3`（总账 v2", "`_bmad-output/审查/CARD-G4-3-验收单.md:1`（总账 v2")
else:
    raise SystemExit(f"unknown case {name}")
open(path, "w", encoding="utf-8").write(s)
PY
}

case_run() {  # $1=case $2=期望 neg_rc $3=说明
  local name=$1 want=$2 desc=$3
  local led_before d out rc ctrl_d ctrl_out ctrl_rc led_after same verdict extra=""
  led_before=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  if [[ $name == "E2-evdirmv" ]]; then
    [[ -d "$EVDIR" && ! -e "$EVMOVED" ]] || { echo "E2 setup FAIL"; return 1; }
    mv "$EVDIR" "$EVMOVED" || return 1
  else
    mutate "$name" || { echo "MUTATION FAILED $name"; return 1; }
  fi
  d=$(digest_now)
  out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$d" 2>&1); rc=$?
  if [[ $name == F2* ]]; then
    if [[ "$d" != "$CANON_DIGEST" ]]; then extra="digest_changed_vs_canonical=yes（$CANON_DIGEST → $d）"; else extra="digest_changed_vs_canonical=NO"; BIND_BAD=1; fi
  fi
  restore
  led_after=$(shasum -a 256 "$LEDGER" | awk '{print $1}')
  ctrl_d=$(digest_now)
  ctrl_out=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$ctrl_d" 2>&1); ctrl_rc=$?
  [[ "$led_after" == "$led_before" ]] && same=yes || same=NO
  [[ $rc == $want ]] && verdict=ok || verdict=MISMATCH
  {
    print -r -- "--- case: $name（相位 $PHASE）---"
    print -r -- "# mutation: $desc"
    print -r -- "# re-anchored_expect_digest(mutated)=$d"
    print -r -- "$out"
    print -r -- "neg_rc=$rc expected_rc=$want verdict=$verdict"
    [[ -n $extra ]] && print -r -- "# $extra"
    print -r -- "# --- control run（还原后同一树）---"
    print -r -- "$ctrl_out"
    print -r -- "control_rc=$ctrl_rc"
    print -r -- "ledger_sha_before=$led_before"
    print -r -- "ledger_sha_after=$led_after sha_equal=$same"
    print -r -- "# evidence_dir_restored=$(test -d "$EVDIR" && echo yes || echo NO) moved_leftover=$(test -e "$EVMOVED" && echo yes || echo no)"
  } >> "$OUT"
  echo "[$name/$PHASE] neg_rc=$rc want=$want $verdict sha_equal=$same file=$(basename $OUT)"
  [[ $verdict == ok && $same == yes && $ctrl_rc == 0 ]] || BAD=1
}

BAD=0
BIND_BAD=0
{
  echo "# CARD-G8-10 r8 负控运行器（相位 $PHASE）"
  echo "# checker=$CHECKER"
  echo "# checker_sha256=$CSHA"
  echo "# canonical_ledger_sha256=$(git show HEAD:"$LEDGER" | shasum -a 256 | awk '{print $1}')"
  echo "# 恢复方式：git show HEAD:<底账> > <底账>（不用 stash / 不用 checkout）；E2 另把目录 mv 回原位"
} > "$OUT"
CANON_DIGEST=$(digest_now)
echo "# canonical_digest=$CANON_DIGEST" >> "$OUT"

if [[ $PHASE == pre ]]; then WANT=0; else WANT=1; fi
case_run A-dup      $WANT 'criteria 追加 - {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}（重复显式 key；复核 r7-H1 原形）'
case_run B-merge    $WANT 'criteria 追加 - {…, outcome: not_yet, <<: &extra {outcome: !!str pass}}（merge 源内 pass 被显式 not_yet 覆盖 ⇒ constructed 面看不到）'
case_run C-alias    $WANT '顶层 seed_state: &p !!str pass + criteria 追加 - {…, outcome: not_yet, <<: {outcome: *p}}（scalar alias 经 merge 源）'
case_run D-dotdot   $WANT 'nodeid 改为 `backend/tests/../app/models/service_status.py::ServiceStatus`（.. 越界归一化）'
case_run E1-evdir   $WANT 'evidence 目录引用改 `_bmad-output/审查/evidence-g2-8-nope-r8/`（不存在 ⇒ 必须红）'
case_run E2-evdirmv $WANT '物理移走 `_bmad-output/审查/evidence-g2-8/`（复核者原形；跑后 mv 回）'
case_run F1-badsha  $WANT '平文 SHA `6337e320` → `6337e32z8`（畸形值，匹配不到 hex 正则）'
case_run F2-substsha 0 '平文 SHA `6337e320` → `c53069d3`（有效 commit）⇒ 期望仍 rc=0，但 digest 变化（绑定证明）'
case_run G-ownerpath  $WANT '检索链 owner cell `G4-3` → `_bmad-output/审查/CARD-G4-3-验收单.md:1`（ID 只在文件名里）'

{
  echo "# --- 收尾（还原后 canonical 复跑）---"
  GREEN_D=$(digest_now)
  GREEN_OUT=$(set +e; python3 "$CHECKER" --ledger "$LEDGER" --root . --expect-digest "$GREEN_D" 2>&1); GREEN_RC=$?
  print -r -- "expect_digest=$GREEN_D"
  print -r -- "$GREEN_OUT"
  print -r -- "rc=$GREEN_RC"
  print -r -- "phase=$PHASE verdict_bad=$BAD f2_binding_bad=$BIND_BAD"
} >> "$OUT"
trap - EXIT
restore
if [[ $BAD == 0 && $BIND_BAD == 0 ]]; then echo "R8_NEGCTL_DONE phase=$PHASE ok file=$OUT"; else echo "R8_NEGCTL_DONE phase=$PHASE BAD=$BAD bind_bad=$BIND_BAD file=$OUT"; fi
