#!/bin/bash
# CARD-RV-E 取证驱动：在隔离 scratch 仓上，把 b20fe550 旧门 / 870e52b3 新门
# 放到同一批对抗性索引上对撞，逐条给出「旧门放行 / 新门拦下」的翻转证据。
# 全程不触碰 card-z7-tool 工作树、live vault、任何真实 index。
set -u
SP="$1"
STAMP=$(date +%Y%m%dT%H%M%S)
OLD="$SP/gate-old.sh"
NEW="$SP/gate-new.sh"
M='ZZPROBEMARKZZ'

mkrepo() {  # $1 = dir
  mkdir -p "$1"; cd "$1" || exit 1
  git init -q .; git config user.email p@probe.local; git config user.name probe
}

echo "########################################################"
echo "# CARD-RV-E 门对撞取证  $STAMP"
echo "# OLD = b20fe550:lefthook.yml 的 mutant-residue-scan run 块(逐字, 仅 MARKER 换中性串)"
echo "# NEW = 870e52b3:lefthook.yml 的同一块(= 主干 HEAD, blob 17dacb73)"
echo "# MARKER 探针串 = $M"
echo "########################################################"

# ============ 场景 1：特殊字符文件名 + 重命名 + ++ 正文 ============
A="$SP/c1-$STAMP"; mkrepo "$A"
{ for i in $(seq 1 30); do echo "line_$i = $i"; done; } > orig.py
git add orig.py; git commit -qm base
printf 'x = 1\ny = "%s"\n' "$M" > plain.py                       # 验伪锚: 两版都必须抓到
printf 'q = "%s"\n' "$M" > 'dq"uote.py'                          # ① 双引号
printf 'b = "%s"\n' "$M" > 'back\slash.py'                       # ① 反斜杠
printf 't = "%s"\n' "$M" > "$(printf 'tab\tname.py')"            # ① TAB
printf 'n = "%s"\n' "$M" > "$(printf 'new\nline.py')"            # ① 换行  <= 残孔
printf 's = "%s"\n' "$M" > 'star*glob.py'
printf 'u = "%s"\n' "$M" > '中文名.py'
printf '+++ not a diff header\ng = "%s"\n' "$M" > plusplus.py    # ⑤ 行号
git mv orig.py renamed.py; printf 'r = "%s"\n' "$M" >> renamed.py # ④ 重命名
git add -A .
echo; echo "=== 场景1 索引 ==="; git diff --cached --name-status | cat -v
echo; echo "--- 场景1 OLD ---"; bash "$OLD"; echo "OLD rc=$?"
echo; echo "--- 场景1 NEW ---"; bash "$NEW"; echo "NEW rc=$?"

# ============ 场景 2：pathspec magic / +++ 行上的标记 ============
B="$SP/c2-$STAMP"; mkrepo "$B"
echo seed > seed.txt; git add seed.txt; git commit -qm base
printf 'c = "%s"\n' "$M" > ':magic.py'                            # ② pathspec 魔法前缀
printf 'w = "%s"\n' "$M" > 'x?.py'
printf 'z = 0\n' > 'xy.py'
printf '+++ %s marker on a plus-plus-plus line\nok = 1\n' "$M" > sharp.py  # ⑤ 整条漏检
git add -A .
echo; echo "=== 场景2 索引 ==="; git diff --cached --name-status | cat -v
echo; echo "--- 场景2 OLD ---"; bash "$OLD"; echo "OLD rc=$?"
echo; echo "--- 场景2 NEW ---"; bash "$NEW"; echo "NEW rc=$?"

# ============ 场景 3：color.ui/color.diff = always ============
C="$SP/c3-$STAMP"; mkrepo "$C"
echo seed > seed.txt; git add seed.txt; git commit -qm base
printf 'x = 1\ny = "%s"\n' "$M" > plain.py
git add -A .
git config color.ui always; git config color.diff always
echo; echo "=== 场景3 原语: '^+' 命中数 ==="
echo -n "  裸 diff(无 --no-color)          : "; git --no-pager diff --cached -U0 --diff-filter=AM -- plain.py | grep -c '^+' || true
echo -n "  -c color.ui=never (注释称无效)  : "; git --no-pager -c color.ui=never diff --cached -U0 --diff-filter=AM -- plain.py | grep -c '^+' || true
echo -n "  --no-color 标志   (注释称有效)  : "; git --no-pager diff --cached --no-color -U0 --diff-filter=AM -- plain.py | grep -c '^+' || true
echo; echo "--- 场景3 OLD ---"; bash "$OLD"; echo "OLD rc=$?"
echo; echo "--- 场景3 NEW ---"; bash "$NEW"; echo "NEW rc=$?"

# ============ 场景 4：枚举失败(非 git 目录) → FAILED 位 ============
D="$SP/c4-$STAMP"; mkdir -p "$D"; cd "$D" || exit 1
echo; echo "=== 场景4 cwd 非 git 仓 ==="; git rev-parse --is-inside-work-tree 2>&1 | head -1
echo; echo "--- 场景4 OLD ---"; bash "$OLD" 2>/dev/null; echo "OLD rc=$?"
echo; echo "--- 场景4 NEW ---"; bash "$NEW" 2>/dev/null; echo "NEW rc=$?"

# ============ 场景 5：换行残孔链条四环 ============
cd "$A" || exit 1
echo; echo "=== 场景5 环1: :294-295 的 -z 输出里换行是原始字节 ==="
git --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AM -z | od -c | sed -n '1,3p'
echo "=== 场景5 环1-对照: 旧门枚举(无 -z) C 引号化成一行 ==="
git -c core.quotepath=false diff --cached --name-only --diff-filter=AM | grep -n 'new' | cat -v
echo "=== 场景5 环2: 经 :298 的 tr 后裂成两行 ==="
git --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AM -z | tr '\000' '\n' | grep -n -E '^(new|line\.py)$' | cat -v
echo "=== 场景5 环3: 两段各自作 pathspec -> 无输出 rc=0 ==="
git --no-pager --literal-pathspecs diff --cached --no-color --no-renames -U0 --diff-filter=AM -- "new"; echo "  seg1 rc=$?"
git --no-pager --literal-pathspecs diff --cached --no-color --no-renames -U0 --diff-filter=AM -- "line.py"; echo "  seg2 rc=$?"
echo "=== 场景5 环3-验伪锚: 同形命令对真实存在的路径能出输出 ==="
git --no-pager --literal-pathspecs diff --cached --no-color --no-renames -U0 --diff-filter=AM --stat -- "plain.py"; echo "  anchor rc=$?"

# ============ 场景 6：awk -v 转义处理(显示层) ============
echo; echo "=== 场景6 awk -v 对文件名做转义处理(F 仅用于显示) ==="
echo in | awk -v F='back\slash.py' '{print "  -v  F=[" F "]"}'
echo in | awk -v F='a\nb.py'       '{print "  -v  F=[" F "]"}'
awk 'BEGIN{ print "  ARGV F=[" ARGV[1] "]" }' 'back\slash.py'
awk --version 2>&1 | head -1
echo; echo "########## 取证结束 $STAMP ##########"
