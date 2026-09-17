#!/bin/bash
# CARD-TOOL-residue-fail-open — 真 hook 三控(完整绑定存档)
# 对应 Codex round-4 的证据意见: 只记 0/1/1 不够, 要能把这次执行绑回具体字节。
# 因此每一控都落: 本次 lefthook.yml 的 sha256 与 HEAD、探针的路径与 blob OID 与字节 od、
# 本次 lefthook 的版本与绝对路径、完整原始输出、lefthook 的 rc。
#
# ⛔ 撤暂存一律 git reset HEAD -- <path> + 删文件; 禁 git checkout -- / git stash。
# ⛔ 本文件不含变异标记字面量: MARK 现拼。
set -u
cd "$(dirname "$0")/../../.." || exit 1        # -> 车道树根
ROOT=$PWD
LH=/opt/homebrew/bin/lefthook
MARK=$(printf 'MUT%s' 'ANT')
D=_bmad-output/审查/evidence-residue-fo

echo "=== 真 hook 三控 @ $(date -Iseconds) ==="
echo "车道树      : $ROOT"
echo "HEAD        : $(git rev-parse HEAD)"
echo "lefthook.yml: sha256=$(shasum -a 256 < lefthook.yml | cut -d' ' -f1)"
echo "工作树相对 HEAD 的 lefthook.yml 差异: $(git --no-pager diff --stat --no-color HEAD -- lefthook.yml | tail -1 | sed 's/^ *//')"
echo "lefthook    : $LH -> $(readlink "$LH")"
echo -n "lefthook 版本(裸调用): "; "$LH" version; echo "  version_rc=$?"
echo

one() {   # $1 = 名称, $2 = 探针路径, $3 = payload 形态(plain|nulfirst), $4 = 期望(OK|BLOCKED)
  local nm=$1 pp=$2 form=$3 want=$4 rc
  echo "######## $nm ########"
  case "$form" in
    nulfirst) printf 'x = 1 \000 # %s\n' "$MARK" > "$pp" ;;
    *)        printf 'x = 1  # %s\n' "$MARK" > "$pp" ;;
  esac
  echo "探针路径    : $pp   (期望 $want)"
  echo "探针字节(od): $(LC_ALL=C od -An -c < "$pp" | tr -s ' ' | tr -d '\n' | sed 's/^ //')"
  git add "$pp"
  echo "探针 blob OID: $(git rev-parse ":$pp")"
  echo "本次暂存清单 :"; git --no-pager diff --cached --no-color --name-only | sed 's/^/  /'
  # ⚠️ 原始输出里可能带**真 NUL 字节**(负控 B 的探针含 NUL, ruff 报语法错误时会把那个字节
  # 原样回显)。含 NUL 的文档会被 git 判成二进制、diff 里看不到内容, 所以这里把 NUL 等长换成
  # `?` 再落盘 —— 除该字节外逐字节原样, 不是摘录。
  echo "--- lefthook run pre-commit 输出(NUL 已等长换成 ?, 其余逐字节原样) ---"
  "$LH" run pre-commit 2>&1 | LC_ALL=C tr '\000' '?'; rc=${PIPESTATUS[0]}
  echo "--- lefthook_rc=$rc ---"
  git reset -q HEAD -- "$pp"; /bin/rm -f "$ROOT/$pp"
  echo "撤销后 _t8a_probe/_probe 残留计数: $(git status --porcelain | /usr/bin/grep -cE '_t8a_probe|_probe\.txt')"
  echo
}

one "正控 — 允许名单内的路径 + 真标记(期望该块放行)" "$D/_probe.txt"            plain    OK
one "负控 A — 名单外的路径 + 普通标记(期望阻断)"      backend/scripts/_t8a_probe.py plain    BLOCKED
one "负控 B — 名单外 + 同一行内 NUL 在标记之前(期望阻断)" backend/scripts/_t8a_probe.py nulfirst BLOCKED

echo "=== 收尾: 工作树状态 ==="
git status --porcelain | sed 's/^/  /'
