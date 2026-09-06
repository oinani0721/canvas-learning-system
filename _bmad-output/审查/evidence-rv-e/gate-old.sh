MARKER="ZZPROBE""MARKZZ"
TMP="${TMPDIR:-/tmp}/lefthook-mutant-residue.$$"
: > "$TMP"
git -c core.quotepath=false diff --cached --name-only --diff-filter=AM \
  | while IFS= read -r f; do
      case "$f" in
        backend/scripts/g32b_mutation_gates.py) continue ;;
        backend/scripts/g32cb_mutation_gates.py) continue ;;
        _bmad-output/*) continue ;;
      esac
      git diff --cached -U0 --diff-filter=AM -- "$f" \
        | awk -v F="$f" -v M="$MARKER" '
            /^@@/    { split($3, a, ","); ln = a[1] + 0; next }
            /^\+\+\+/ { next }
            /^\+/    { if (index($0, M)) printf "  %s:%d: %s\n", F, ln, substr($0, 2); ln++ }
          ' >> "$TMP"
    done
if [ -s "$TMP" ]; then
  echo ""
  echo "[Mutant-Scan] BLOCKED — 暂存的新增行里带变异残留标记:"
  cat "$TMP"
  echo ""
  echo "[Mutant-Scan] 变异 harness 没还原干净。先 restore 被改的生产文件,"
  echo "[Mutant-Scan] 再拿变异前的全文件 sha 基线逐个复核 —— 标记只是最弱那道网。"
  rm -f "$TMP"
  exit 1
fi
rm -f "$TMP"
echo "[Mutant-Scan] OK (staged additions carry no mutation marker)."
