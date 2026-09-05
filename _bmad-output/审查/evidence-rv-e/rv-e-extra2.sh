#!/bin/bash
# CARD-RV-E 追加探针 v2：补严 E2 的验伪锚 + 修正 E3 的引号。
set -u
SP="$1"
STAMP=$(date +%Y%m%dT%H%M%S)
NEW="$SP/gate-new.sh"
M='ZZPROBEMARKZZ'
mkrepo() { mkdir -p "$1"; cd "$1" || exit 1; git init -q .; git config user.email p@probe.local; git config user.name probe; }

echo "########## CARD-RV-E 追加探针 v2  $STAMP ##########"

# ---------- E2b: 类型改变(T) 漏检 —— 同批带一个必被抓到的验伪锚 ----------
E="$SP/e2b-$STAMP"; mkrepo "$E"
printf 'old content\n' > t.txt
printf 'base = 0\n'    > control.py
git add -A .; git commit -qm base
ln -sfn "target_with_${M}_inside" t.txt      # regular file -> symlink, 目标串带标记
printf 'ctl = "%s"\n' "$M" >> control.py     # 验伪锚: 本轮新增行带标记, 必须被抓到
git add -A .
echo; echo "=== E2b 索引 ==="; git diff --cached --name-status
echo "=== E2b --diff-filter=AM 枚举面(t.txt 在不在里面) ==="
git --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AM -z | tr '\000' '\n'
echo "=== E2b symlink 目标串确实带标记 ==="; ls -l t.txt | sed 's/.*-> //'
echo "=== E2b 不加 --diff-filter 时 t.txt 的新增行 ==="
git --no-pager diff --cached --no-color -U0 -- t.txt | grep '^+' | cat -v
echo "=== E2b NEW 门 ==="; bash "$NEW"; echo "E2b rc=$?"
echo ">>> 判读: 验伪锚 control.py 被抓到 = 门在跑; t.txt 未出现在 hits = T 状态漏检"

# ---------- E3b: `done < 不存在文件` 的 sh 行为(修正引号) ----------
echo
echo '=== E3b: sh 中 "while ... done < 不存在的文件" 之后是否继续执行 ==='
sh -c 'set -u
FAILED=0
while IFS= read -r f; do echo "  body: $f"; done < /nonexistent/list
rc=$?
echo "  loop rc=$rc ; FAILED=$FAILED ; 循环体未执行"
if [ "$FAILED" -ne 0 ]; then echo "  -> 会阻断"; else echo "  -> 会打印 OK (fail-open)"; fi' 2>&1
echo "E3b outer rc=$?"
echo ">>> 对照: 真实门里 \$TMPD/list 由 :298 的 tr 刚创建, :298 失败会 exit 1;"
echo ">>> 故该窗口窄(需 TMPD 在 :298 与 :320 之间消失), 但确属 FAILED 位未覆盖的失败点。"

echo; echo "########## 追加探针 v2 结束 $STAMP ##########"
