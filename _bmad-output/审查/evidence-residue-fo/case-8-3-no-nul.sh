#!/bin/bash
# CASE 8-3 — 记录流末条没有 NUL 终止, 那一条被 read 直接丢弃
# 自述: 用一个 git 垫片把**枚举那一次调用**(带 --name-only 的那次)的输出换成
#       `a_clean.py\0b_dirty.py`(末条故意不带 NUL), 其余 git 调用原样透传。
#       `read -r -d ''` 读到末条时拿不到终止符, 返回非零 ⇒ 循环体不执行, 带标记的
#       b_dirty.py 从未被扫 ⇒ 旧版块打 OK 退 0。
#       新版块在枚举之后校验「非空清单必须以 NUL 结尾」⇒ 退 1。
# 说明: 这一条**不是** SEEN/EXPECTED 计数能抓的 —— 清单里只有 1 个 NUL, 循环也只跑
#       1 次, 两个数相等; 所以末字节校验是独立必需的一道。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 8-3: 记录流末条无 NUL 终止 ==="
prepare_blocks || exit 1

SHIM="$WORK/bin"; mkdir -p "$SHIM"
cat > "$SHIM/git" <<SHIMEOF
#!/bin/sh
for a in "\$@"; do
  if [ "\$a" = "--name-only" ]; then
    printf 'a_clean.py\000b_dirty.py'
    exit 0
  fi
done
exec "$REAL_GIT" "\$@"
SHIMEOF
chmod +x "$SHIM/git"

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'y = 2  # nothing here\n' > "$REPO/a_clean.py"
printf 'x = 1  # %s\n' "$MARK" > "$REPO/b_dirty.py"
( cd "$REPO" && "$REAL_GIT" add a_clean.py b_dirty.py )

echo "输入: 暂存 a_clean.py(无标记) + b_dirty.py(带标记)"
echo "注入: git 垫片让枚举输出 'a_clean.py<NUL>b_dirty.py' —— 末条缺 NUL; 其余 git 调用透传"
echo -n "旁证: 该流的末字节(十进制, NUL 应为 0) = "
printf 'a_clean.py\000b_dirty.py' | tail -c 1 | od -An -tu1 | tr -d ' \n'; echo

run_both 8-3 "$REPO" "$SHIM"
