#!/bin/bash
# CARD-SEB-WRITER-SUBSTRING-TMP (k) 负控：各只拆一层，红必须落在指定断言上。
#
# ⛔ 还原基准 = **变异前的字节快照**，不是 `git show HEAD:<path>`。
#    卡文 (k) 写的是后者，但本卡跑负控时 HEAD 仍是 B15_BASE `9c4e7e82`（修复未提交）——
#    照抄会把整个修复一起还原掉，而且还原后 shasum 与 HEAD 自洽，是个静默的假绿。
#    （工程坑：还原基准是变异前的 sha 不是 HEAD。）
#
# 用法: bash negctl.sh <worktree-root> <段号 1|2|3> <snapshot-dir>
set -u
ROOT="$1"; SEG="$2"; SNAPDIR="$3"
cd "$ROOT" || exit 2
SEB=canvas-vault/.claude/skills/start-exam-board/SKILL.md
CAS=backend/tests/regression/test_g3_3_cas.py
PYTEST="$ROOT/backend/.venv/bin/pytest"

case "$SEG" in
  1|2) TARGET="$SEB" ;;
  3)   TARGET="$CAS" ;;
  *)   echo "未知段号 $SEG"; exit 2 ;;
esac
SNAP="$SNAPDIR/negctl-seg$SEG-snapshot.bak"
cp "$TARGET" "$SNAP"
trap 'cp "$SNAP" "$TARGET"' EXIT

echo "=== 负控段 $SEG · target=$TARGET · $(date -Iseconds) ==="
echo "--- shasum 行 1/4 快照 ---";   shasum -a 256 "$SNAP"
echo "--- shasum 行 2/4 变异前 ---"; shasum -a 256 "$TARGET"

python3 - "$SEG" "$TARGET" <<'PY'
import sys
from pathlib import Path

seg, target = sys.argv[1], Path(sys.argv[2])
text = target.read_text(encoding="utf-8")

if seg == "1":
    # 只拆「parsed-field 等值」这一层，换回子串判定。
    # 严格解码那一层不动 —— 坏行在上面的 try 里就 continue 了，走不到这一行，
    # 所以本段测的确实只是「等值 vs 子串」。
    old = '            if isinstance(_rec, dict) and _rec.get("event_id") == evid:'
    new = '            if json.dumps(evid, ensure_ascii=False) in _bl.decode("utf-8", "replace"):'
elif seg == "2":
    # 只拆「逐行严格解码」这一层，换回有损解码。查重方式不动。
    old = '                _rec = json.loads(_bl.decode("utf-8"))'
    new = '                _rec = json.loads(_bl.decode("utf-8", "replace"))'
else:
    # 只把 cas 侧的模块级过滤字面量改回旧值（钉点不同批改 = 什么后果）。
    old = 'if \'P = "/tmp/cls-exam/exam-created-event.json"\' in b'
    new = 'if \'P = "/tmp/exam-created-event.json"\' in b'

assert text.count(old) == 1, f"预置失败: 变异锚不唯一, count={text.count(old)}\n{old!r}"
target.write_text(text.replace(old, new, 1), encoding="utf-8")
print(f"已变异 1 处:\n  - {old.strip()}\n  + {new.strip()}")
PY
rc_mut=$?
if [ "$rc_mut" -ne 0 ]; then echo "变异失败 rc=$rc_mut"; exit "$rc_mut"; fi

echo "--- shasum 行 3/4 变异后（必须与行 2 不同）---"; shasum -a 256 "$TARGET"

echo "--- 被测判据 ---"
if [ "$SEG" = "3" ]; then
  ( cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" -q -p no:cacheprovider tests/regression/test_g3_3_cas.py -rfE )
  echo "pytest_rc=$?"
else
  ( cd backend && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" -q -p no:cacheprovider tests/skills/test_seb_writer_exact_match.py -rfE )
  echo "pytest_rc=$?"
fi

cp "$SNAP" "$TARGET"
echo "--- shasum 行 4/4 还原后（必须与行 2 逐字同）---"; shasum -a 256 "$TARGET"
