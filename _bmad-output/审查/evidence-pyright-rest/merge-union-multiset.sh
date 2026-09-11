#!/bin/zsh
# merge commit 专用多重集判据：合并结果的错误集必须 ⊆ 两个父提交错误集的并集。
# 键 = (相对路径, rule, message)，不含行号（盲区如实登记）。
# 用法: merge-union-multiset.sh <P1_SHA> <P2_SHA> <TAG>
set -u
TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest
P1=$1; P2=$2; TAG=$3
VENV=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv
EV=$TREE/_bmad-output/审查/evidence-pyright-rest; mkdir -p "$EV"
for S in $P1 $P2; do
  D=$(mktemp -d)/t-$S; mkdir -p "$D"
  git -C "$TREE" archive "$S" backend/app backend/lib pyrightconfig.json | tar -x -C "$D"
  ln -s "$VENV" "$D/backend/.venv"
  echo "tree($S) = $D"
  ( cd "$D" && backend/.venv/bin/pyright backend/app --outputjson > "$EV/pyright-parent-$S.json" 2>/dev/null ); echo "  rc=$?"
done
( cd "$TREE" && backend/.venv/bin/pyright backend/app --outputjson > "$EV/pyright-merged-$TAG.json" 2>/dev/null ); echo "merged rc=$?"
python3 - "$EV/pyright-parent-$P1.json" "$EV/pyright-parent-$P2.json" "$EV/pyright-merged-$TAG.json" <<'PY'
import json,sys,collections
def load(p):
    d=json.load(open(p)); ms=collections.Counter()
    for x in d['generalDiagnostics']:
        if x['severity']!='error': continue
        f=x['file']; i=f.find('/backend/app/')
        ms[(f[i+1:] if i>=0 else f, x.get('rule','-'), x['message'])]+=1
    return ms,d['summary']['errorCount']
p1,n1=load(sys.argv[1]); p2,n2=load(sys.argv[2]); mg,nm=load(sys.argv[3])
assert n1>0 and n2>0, "SUSPECT-EMPTY: 两个父提交都零错在本树不可能，先查 JSON 读取"
union=p1|p2                      # Counter 并集取逐键最大计数
new=mg-union
print(f"parent1={n1} parent2={n2} merged={nm} |union|={sum(union.values())} NEW_vs_UNION={sum(new.values())}")
for k,c in sorted(new.items()): print("NEW",c,k)
sys.exit(1 if new else 0)
PY
echo "judge-rc=$?"
