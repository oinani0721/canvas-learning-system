#!/bin/bash
# CASE 6-2 — 单文件 diff 缺 --no-textconv
# 自述: 独立临时仓里给 *.py 挂一个 diff 驱动, 并用 GIT_CONFIG_* 注入该驱动的 textconv
#       程序(把标记改写成别的字样)。旧版块拿到的是**转换后**的文本 ⇒ 零命中、打 OK 退 0。
#       新版块加了 --no-textconv, 拿回原始内容 ⇒ BLOCKED 退 1。
# 注: .gitattributes 类对照只在 $TMPDIR 下的独立临时仓里做, 跑完随 WORK 一起删(卡文 (i))。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-2: 单文件 diff 缺 --no-textconv ==="
prepare_blocks || exit 1

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf '#!/bin/sh\nsed "s/%s/REDACTED-BY-TEXTCONV/g" "$1"\n' "$MARK" > "$WORK/conv.sh"
chmod +x "$WORK/conv.sh"
printf '*.py diff=strip\n' > "$REPO/.gitattributes"
( cd "$REPO" && "$REAL_GIT" add .gitattributes && "$REAL_GIT" commit -q -m attrs ) >/dev/null 2>&1
printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )

export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=diff.strip.textconv GIT_CONFIG_VALUE_0="$WORK/conv.sh"
echo "输入: 临时仓 .gitattributes = '*.py diff=strip'; diff.strip.textconv 把标记换成 REDACTED-BY-TEXTCONV"
echo "旁证: 旧标志集下 git 看到的新增行 ="
( cd "$REPO" && "$REAL_GIT" --no-pager --literal-pathspecs diff --cached --no-color \
    --no-renames -U0 --diff-filter=AM -- p.py | /usr/bin/grep '^+x' )

run_both 6-2 "$REPO"
