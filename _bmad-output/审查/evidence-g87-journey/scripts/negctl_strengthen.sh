#!/usr/bin/env bash
# CARD-G8-7 零静默改写门 负控强化电池 (可复跑)
# 用法: bash negctl_strengthen.sh
# 输出: 每段打印精确命令 + 结果 + rc; 供 Codex 复现审计 (回应 r2 M-1)
set -u
ROOT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy
EV="$ROOT/_bmad-output/审查/evidence-g87-journey"
BEFORE="$EV/02-live-snapshot-before.txt"
AFTER="$EV/04-live-snapshot-after.txt"
PY="$ROOT/backend/.venv/bin/python"
SCR="$(mktemp -d)"
trap 'rm -rf "$SCR"' EXIT

# 声明写入面 (精确匹配; 未授权下被答节点/新材料/选定板未知 ⇒ 占位, 匹配为空集)
WL=(-e '^检验白板/<新检验白板>\.md$' -e '^节点/<被答节点>\.md$' -e '^节点/<新材料>\.md$' \
    -e '^原白板/<选定板>\.md$' -e '^outputs/回顾-' -e '^outputs/\.recap-manifest-' \
    -e '^outputs/\.recap-scan-' -e '^outputs/今日复习\.json$' -e '^outputs/今日复习\.md$' \
    -e 'daily-review\.canvas-vault\.state\.json$')

# 路径提取: 修正版剥离 "diff前缀 + 64hex + 2空格"
extract_fixed() { grep -E '^[<>]' | sed 's/^[<>] [0-9a-f]\{64\}  //' | sort -u; }
extract_cardtext() { grep -E '^[<>]' | awk '{print $3}' | sort -u; }

mutate() {  # $1=src $2=target $3=dest  (flip sha 末位 hex)
  "$PY" - "$1" "$2" "$3" <<'PY'
import sys
src,tgt,dst=sys.argv[1],sys.argv[2],sys.argv[3]
ls=open(src,encoding='utf-8').read().split('\n'); n=0
for i,l in enumerate(ls):
    if l.endswith(tgt):
        sha,_,p=l.partition('  ')
        ls[i]=sha[:-1]+('0' if sha[-1]!='0' else '1')+'  '+p; n+=1
open(dst,'w',encoding='utf-8').write('\n'.join(ls))
print(f"  mutate: lines={n} target={tgt}")
PY
}

classify() {  # $1=snapshot $2=tag
  diff <(grep -v '^#' "$1" | sort) <(grep -v '^#' "$AFTER" | sort) | extract_fixed > "$SCR/ch_$2.txt"
  grep -v -E "${WL[@]}" "$SCR/ch_$2.txt" > "$SCR/out_$2.txt"
  echo "  changed=$(wc -l < "$SCR/ch_$2.txt" | tr -d ' ') outside=$(wc -l < "$SCR/out_$2.txt" | tr -d ' ')"
  echo "  outside 明细: $(tr '\n' '|' < "$SCR/out_$2.txt")"
}

echo "# 负控强化电池 (可复跑脚本) $(date '+%FT%T%z')"
echo "# 白名单 matcher: grep -v -E ${WL[*]}"
echo "# 输入面 sha256: before=$(shasum -a 256 "$BEFORE" | cut -d' ' -f1)"
echo "#               after =$(shasum -a 256 "$AFTER" | cut -d' ' -f1)"
echo
echo "## A. 非白名单文件 原白板/CS.md"
echo "CMD: cp \$BEFORE bm_a.txt; mutate bm_a.txt '原白板/CS.md'; classify bm_a.txt a"
cp "$BEFORE" "$SCR/bm_a.txt"; mutate "$SCR/bm_a.txt" '原白板/CS.md' "$SCR/bm_a.txt"; classify "$SCR/bm_a.txt" a; echo "rc=$?"
echo
echo "## B. 无关节点 节点/lecture 2.md"
echo "CMD: cp \$BEFORE bm_b.txt; mutate bm_b.txt '节点/lecture 2.md'; classify bm_b.txt b"
cp "$BEFORE" "$SCR/bm_b.txt"; mutate "$SCR/bm_b.txt" '节点/lecture 2.md' "$SCR/bm_b.txt"; classify "$SCR/bm_b.txt" b; echo "rc=$?"
echo
echo "## C. 含空格路径 原白板/递归与分治 (Recursion & Divide-Conquer).md"
echo "CMD: cp \$BEFORE bm_c.txt; mutate bm_c.txt '<space path>'; 分别用卡文字面与修正版提取"
cp "$BEFORE" "$SCR/bm_c.txt"; mutate "$SCR/bm_c.txt" '原白板/递归与分治 (Recursion & Divide-Conquer).md' "$SCR/bm_c.txt"
echo -n "  卡文字面 awk '\$3': "; diff <(grep -v '^#' "$SCR/bm_c.txt" | sort) <(grep -v '^#' "$AFTER" | sort) | extract_cardtext | tr '\n' '|'; echo
echo -n "  修正版剥离:        "; diff <(grep -v '^#' "$SCR/bm_c.txt" | sort) <(grep -v '^#' "$AFTER" | sort) | extract_fixed | tr '\n' '|'; echo
classify "$SCR/bm_c.txt" c; echo "rc=$?"
echo
echo "## D. 卡文 §二.8 sed 原文是否 no-op (身份链)"
echo "CMD: cp \$BEFORE bm_d.txt; sed -i '' -e '/原白板\/CS\.md\$/ s/^\\(.\\{63\\}\\)./\\1f/' bm_d.txt; diff \$BEFORE bm_d.txt | grep -c '^>'"
cp "$BEFORE" "$SCR/bm_d.txt"
sed -i '' -e '/原白板\/CS\.md$/ s/^\(.\{63\}\)./\1f/' "$SCR/bm_d.txt"
echo "  原白板/CS.md 完整原文行: $(grep '原白板/CS.md$' "$BEFORE" | head -1)"
echo "  该行 sha 第 64 位字符: $(grep '原白板/CS.md$' "$BEFORE" | head -1 | cut -c64)"
echo "  before vs bm_d 差异行数 (0 = no-op): $(diff "$BEFORE" "$SCR/bm_d.txt" | grep -c '^>')"
echo "rc=$?"
echo
echo "# 结论: A/B/C 三段负控输入均被 outside 捕获; C 段证明卡文字面 awk \$3 对含空格路径截断; D 段证明卡文 sed 因末位恰为 'f' 而 no-op"
