#!/bin/zsh
# 卡文 §二.7 多重集对照（协议 §2.3 判据）。态一: BASE_SHA=da690bf8（阶段 0 merge 前）
TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc
BASE_SHA=${1:-da690bf8}
VENV=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv
EV=$TREE/_bmad-output/审查/evidence-pyright-svc; mkdir -p "$EV"
B=$(mktemp -d)/baseline-$BASE_SHA; mkdir -p "$B"      # 不要 rm -rf（guard hook 拦 ` -f `）
git -C "$TREE" archive "$BASE_SHA" backend/app backend/lib pyrightconfig.json | tar -x -C "$B"
ln -s "$VENV" "$B/backend/.venv"
( cd "$B" && backend/.venv/bin/pyright backend/app --outputjson > "$EV/pyright-base-$BASE_SHA.json" 2>/dev/null ); echo "base rc=$?"
( cd "$TREE" && backend/.venv/bin/pyright backend/app --outputjson > "$EV/pyright-work-$(git -C $TREE rev-parse --short HEAD).json" 2>/dev/null ); echo "work rc=$?"
python3 - "$EV"/pyright-base-*.json "$EV"/pyright-work-*.json <<'PY'
import json,sys,collections
def load(p):
    d=json.load(open(p)); ms=collections.Counter()
    for x in d['generalDiagnostics']:
        if x['severity']!='error': continue
        f=x['file']; i=f.find('/backend/app/'); ms[(f[i+1:] if i>=0 else f, x.get('rule','-'), x['message'])]+=1
    return ms,d['summary']['errorCount']
base,bn=load(sys.argv[1]); work,wn=load(sys.argv[2]); new=work-base; gone=base-work
print(f"base={bn} work={wn} NEW={sum(new.values())} GONE={sum(gone.values())}")
for k,c in sorted(new.items()): print("NEW",c,k)
sys.exit(1 if new else 0)
PY
echo "rc=$?"
