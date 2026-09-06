set -u
MARKER="MUT""ANT"
TMPD=$(mktemp -d "${TMPDIR:-/tmp}/lefthook-mutant-residue.XXXXXX") || {
  echo "[Mutant-Scan] FAILED: 无法创建临时目录 — 按 fail-closed 阻断。"; exit 1; }
trap 'rm -rf "$TMPD"' EXIT
FAILED=0
if ! git --no-pager diff --cached --no-color --no-renames \
       --name-only --diff-filter=AM -z > "$TMPD/names"; then
  echo "[Mutant-Scan] FAILED: 枚举暂存文件失败 — 按 fail-closed 阻断。"; exit 1
fi
# CARD-TOOL-residue-newline: 按 NUL 直接消费 -z, 不再经 tr 拆行 —— tr 把文件名里的
# \n 拆成两半, 两半各自当路径查 diff, git 对不存在的路径 rc=0 且无输出 => 静默放行。
# 下面先自证本 shell 真能逐字节取回 NUL 记录: 载荷同时带反斜线/换行/前导空格,
# 故 -r、IFS=、-d '' 任缺一个都判不过; dash 等纯 POSIX sh 无 read -d, 一次都不循环。
printf 'a\\\nb\000 c\000' > "$TMPD/probe"
PROBE_ACC=""
while IFS= read -r -d '' _p; do PROBE_ACC="$PROBE_ACC|$_p"; done < "$TMPD/probe"
if [ "$PROBE_ACC" != "$(printf '|a\\\nb| c')" ]; then
  echo "[Mutant-Scan] FAILED: 本 shell 的 'IFS= read -r -d' 取不回逐字节 NUL 记录 —"
  echo "[Mutant-Scan]   /bin/sh 若是 dash 等纯 POSIX sh 必然走到这里。按 fail-closed 阻断。"
  exit 1
fi
: > "$TMPD/hits"
while IFS= read -r -d '' f; do
  [ -n "$f" ] || continue
  case "$f" in
    backend/scripts/g32b_mutation_gates.py) continue ;;
    backend/scripts/g32cb_mutation_gates.py) continue ;;
    _bmad-output/*) continue ;;
  esac
  if ! git --no-pager --literal-pathspecs diff --cached --no-color \
         --no-renames -U0 --diff-filter=AM -- "$f" > "$TMPD/d"; then
    echo "[Mutant-Scan] FAILED: 取 diff 失败: $f"; FAILED=1; continue
  fi
  F="$f" awk -v M="$MARKER" '
    BEGIN          { F = ENVIRON["F"] }
    /^diff --git / { inhunk = 0; next }
    /^@@/          { split($3, a, ","); ln = a[1] + 0; inhunk = 1; next }
    !inhunk        { next }
    /^\+/          { if (index($0, M)) printf "  %s:%d: %s\n", F, ln, substr($0, 2); ln++; next }
    /^ /           { ln++; next }
    { next }
  ' "$TMPD/d" >> "$TMPD/hits" || { echo "[Mutant-Scan] FAILED: 解析失败: $f"; FAILED=1; }
done < "$TMPD/names"
if [ "$FAILED" -ne 0 ]; then
  echo "[Mutant-Scan] 扫描未完成(见上) — 这不是「没发现标记」, 按 fail-closed 阻断。"
  exit 1
fi
if [ -s "$TMPD/hits" ]; then
  echo ""
  echo "[Mutant-Scan] BLOCKED — 暂存的新增行里带变异残留标记:"
  cat "$TMPD/hits"
  echo ""
  echo "[Mutant-Scan] 变异 harness 没还原干净。先 restore 被改的生产文件,"
  echo "[Mutant-Scan] 再拿变异前的全文件 sha 基线逐个复核 —— 标记只是最弱那道网。"
  exit 1
fi
echo "[Mutant-Scan] OK (staged additions carry no mutation marker)."
