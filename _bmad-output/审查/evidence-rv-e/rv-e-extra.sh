#!/bin/bash
# CARD-RV-E 追加探针：六处之外，新门(870e52b3)还有哪些「门未覆盖的路径」。
# 全部在隔离 scratch 仓，只跑逐字提取的门脚本。
set -u
SP="$1"
STAMP=$(date +%Y%m%dT%H%M%S)
NEW="$SP/gate-new.sh"
M='ZZPROBEMARKZZ'

mkrepo() { mkdir -p "$1"; cd "$1" || exit 1; git init -q .; git config user.email p@probe.local; git config user.name probe; }

echo "########## CARD-RV-E 追加探针 $STAMP （只跑 NEW 门）##########"

# ---------- E1: 二进制文件里的标记 ----------
E1="$SP/e1-$STAMP"; mkrepo "$E1"
echo seed > seed.txt; git add seed.txt; git commit -qm base
printf 'head\000%s\000tail\n' "$M" > blob.bin      # 含 NUL -> git 判 binary
printf 'plain = "%s"\n' "$M" > control.py           # 验伪锚: 必须被抓到
git add -A .
echo; echo "=== E1 索引 ==="; git diff --cached --name-status
echo "=== E1 git 对 blob.bin 的 diff 输出形态 ==="
git --no-pager diff --cached --no-color -U0 --diff-filter=AM -- blob.bin | head -5
echo "=== E1 NEW 门 ==="; bash "$NEW"; echo "E1 rc=$?"

# ---------- E2: 类型改变 (regular file -> symlink) ----------
E2="$SP/e2-$STAMP"; mkrepo "$E2"
printf 'old content\n' > t.txt
printf 'plain = "%s"\n' "$M" > control.py
git add -A .; git commit -qm base
rm t.txt 2>/dev/null
ln -s "target_with_${M}_inside" t.txt              # symlink 目标串带标记
printf 'x = 1\n' >> control.py                      # 让 control.py 也变(M) 作验伪锚
git add -A .
echo; echo "=== E2 索引(注意 t.txt 的状态字母) ==="; git diff --cached --name-status
echo "=== E2 t.txt 在 --diff-filter=AM 下是否出现在枚举里 ==="
git --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AM -z | tr '\000' '\n'
echo "=== E2 t.txt 不加 filter 时的 diff ==="
git --no-pager diff --cached --no-color -U0 -- t.txt | head -8
echo "=== E2 NEW 门 ==="; bash "$NEW"; echo "E2 rc=$?"

# ---------- E3: `done < file` 重定向失败时的 shell 行为 ----------
echo; echo "=== E3 sh 里 `while ... done < 不存在的文件` 之后是否继续执行 ==="
sh -c 'set -u; FAILED=0
while IFS= read -r f; do echo "  body: $f"; done < /nonexistent/list 2>/dev/null
echo "  after-loop reached, FAILED=$FAILED, loop-rc-was=$?"
if [ "$FAILED" -ne 0 ]; then echo "  -> would block"; else echo "  -> would print OK (fail-open)"; fi'
echo "E3 outer rc=$?"

# ---------- E4: 删除行携带标记 (设计上应放行, 作反向对照) ----------
E4="$SP/e4-$STAMP"; mkrepo "$E4"
printf 'a = "%s"\nb = 2\n' "$M" > d.py; git add d.py; git commit -qm base
printf 'b = 2\n' > d.py                             # 删掉带标记那行
git add -A .
echo; echo "=== E4 索引 ==="; git diff --cached --name-status
echo "=== E4 NEW 门(预期 OK: 标记只在删除行) ==="; bash "$NEW"; echo "E4 rc=$?"

echo; echo "########## 追加探针结束 $STAMP ##########"
