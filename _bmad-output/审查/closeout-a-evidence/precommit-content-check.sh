#!/bin/bash
# 提交前逐文件内容核对 —— 跨 session 并发写入碰撞的可执行防线
#
# 起因：CARD-收口A 期间，另一 session 并发写入同一路径，两个进程各持一个 fd 按各自
# offset 落盘，产生拼接损坏文件；该文件被 `git add -A` 一并提交，而提交信息描述的是
# 本车道的内容 —— 提交信息与提交内容不符，且 `git status` 只列文件名，完全看不出来。
#
# 自审 MEDIUM-5 指出：当时只把「提交前逐文件核对」写成了建议，没有可执行的门。
# 本脚本就是那道门。
#
# 判据（对每个暂存的文本文件）：
#   1. UTF-8 必须可解码 —— 拼接损坏几乎必然在拼接点解码失败，这条最灵；
#   2. 打印 字节数 / 行数 / 首行，供人眼一秒识别「这是不是我写的那份」；
#   3. 首行若与同名文件的预期不符，由人判断（脚本不猜）。
#
# 用法：  bash _bmad-output/审查/closeout-a-evidence/precommit-content-check.sh
# 退出码：0 = 全部可解码；1 = 有文件解码失败（极可能是并发写入碰撞）
#
# ── 本门自己的验证证据（门也要先红后绿）──────────────────────────────────
# 正样本（必须被抓到）：当年那个真实的拼接损坏文件
#     git show 9e24ef40:'_bmad-output/审查/codex-review-CARD-G5-9.md' > /tmp/damaged.md
#     → 实测检出 UTF-8 解码失败 @ byte 9890（文件共 16075 字节）✅
# 负样本（必须放行）：本卡 8 个正常交付物 → 全部可解码 ✅
#
# ⚠️ 一次真实的「首行列」使用记录，说明这道门该怎么用：
#   本卡跑它时，`codex-self-review-transcript.txt` 的首行显示
#   `Reading additional input from stdin...`，一眼看去像是混进了噪声。
#   **去核实**后确认：那是 codex 自身的启动输出，与源 stderr `cmp` 逐字节相同，并非污染。
#   ⇒ 首行列的作用是**触发核实**，不是直接下结论。看到异常先 cmp，别急着判定。

set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

# ⚠️ 不用 mapfile：macOS 自带 bash 3.2 没有它（实测 `mapfile: command not found`）。
#    改用 NUL 分隔 + while read，同时正确处理含空格/中文的路径。
FILES=""
while IFS= read -r -d '' f; do
    FILES="${FILES}${f}"$'\n'
done < <(git diff --cached --name-only -z --diff-filter=ACM)

COUNT=$(printf '%s' "$FILES" | grep -c . || true)
if [ "${COUNT:-0}" -eq 0 ]; then
    echo "暂存区为空，无需核对。"
    exit 0
fi

echo "=== 提交前逐文件内容核对（${COUNT} 个暂存文件）==="
printf '%-62s %10s %7s  %s\n' "文件" "字节" "行" "首行 / 状态"
echo "--------------------------------------------------------------------------------"

BADF=$(mktemp)
trap 'rm -f "$BADF"' EXIT
BAD=0
printf '%s' "$FILES" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    [ -f "$f" ] || continue
    # 二进制文件跳过（git 自己的判定）
    if git diff --cached --numstat -- "$f" | grep -q '^-	-	'; then
        printf '%-62s %10s %7s  %s\n' "$(basename "$f")" "-" "-" "(binary, 跳过)"
        continue
    fi
    OUT=$(python3 - "$f" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
b = p.read_bytes()
try:
    t = b.decode("utf-8")
    first = (t.splitlines() or [""])[0][:44]
    print(f"OK\t{len(b)}\t{t.count(chr(10))}\t{first}")
except UnicodeDecodeError as e:
    print(f"BAD\t{len(b)}\t-\t⛔ UTF-8 解码失败 @ byte {e.start} — 疑似并发写入拼接损坏")
PY
)
    STATUS=$(printf '%s' "$OUT" | cut -f1)
    BYTES=$(printf '%s' "$OUT" | cut -f2)
    LINES=$(printf '%s' "$OUT" | cut -f3)
    NOTE=$(printf '%s' "$OUT" | cut -f4-)
    printf '%-62s %10s %7s  %s\n' "$(basename "$f")" "$BYTES" "$LINES" "$NOTE"
    [ "$STATUS" = "BAD" ] && echo x >> "$BADF"
done

echo "--------------------------------------------------------------------------------"
BAD=$(wc -l < "$BADF" | tr -d " ")
if [ "${BAD:-0}" -gt 0 ]; then
    echo "❌ $BAD 个文件 UTF-8 解码失败 —— 极可能是并发 session 写入碰撞，请勿提交。"
    echo "   排查：其他 session 是否正在写同一路径？该文件的首行是不是你写的那份？"
    exit 1
fi
echo "✅ 全部可解码。请人眼扫一遍上表的「首行」列，确认每个文件确实是你写的那份。"
echo "   ⚠️ 本脚本能抓拼接损坏，但抓不到「被完整覆盖成另一份合法内容」——那只能靠首行比对。"
exit 0
