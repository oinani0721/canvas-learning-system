#!/bin/bash
# 负控 round-2：补 Codex round-1 #6 指出的证据缺口
#   缺口①：没有 _probe 创建记录 / 变异源码 / 创建断言 → 判据①「变异生效」不能独立核实
#   缺口②：红轮没保存实际 rc
#   缺口③：绿轮没有 nodeid、还原 diff/hash、rc → 不能绑定「同一用例还原后变绿」
# 本轮把这些全部落盘。不改任何生产代码。
set -uo pipefail

TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
E="$TREE/_bmad-output/审查/evidence-hygiene"
PROBE="$TREE/backend/tests/unit/test_zz_hygiene_negctl.py"
LOG="$E/negctl-round2-full.txt"

cleanup() {
  rm -f "$PROBE" 2>/dev/null
  "$TREE/backend/.venv/bin/python" - <<'PY' 2>/dev/null
import shutil, pathlib
p = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/raw")
if p.exists(): shutil.rmtree(p)
PY
}
trap cleanup EXIT

exec > >(tee "$LOG") 2>&1
cd "$TREE/backend" || exit 90

echo "════ 负控 round-2（补证）════"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "生产代码 sha（跑前，须与跑后相同）:"
shasum -a 256 tests/unit/conftest.py app/api/v1/system.py tests/unit/test_startup_health_check.py

# ───────── 红轮 ─────────
cat > "$PROBE" <<'PY'
"""临时负控用例（CARD-TEST-hygiene-vaultinit (c)）—— 不入 commit。"""

from pathlib import Path


def test_negctl_writes_into_repo():
    target = Path("raw/_probe")
    target.mkdir(parents=True, exist_ok=True)
    # 断言①：变异确实生效（这条 assert 本身就是「_probe 被创建」的记录）
    assert target.is_dir(), "变异未生效：raw/_probe 未创建"
    print(f"NEGCTL-MUTATION-EFFECTIVE abs={target.resolve()}")
PY

echo ""
echo "════ 红轮：变异源码（逐字）════"
cat "$PROBE"
echo "变异文件 sha: $(shasum -a 256 "$PROBE" | awk '{print $1}')"

RED_CMD=(./.venv/bin/python -m pytest tests/unit/test_zz_hygiene_negctl.py -q -p no:cacheprovider -p no:randomly --override-ini=addopts=)
echo ""
echo "════ 红轮命令 ════"
echo "PYTHONDONTWRITEBYTECODE=1 ${RED_CMD[*]}"
PYTHONDONTWRITEBYTECODE=1 "${RED_CMD[@]}" > "$E/negctl-r2-red.txt" 2>&1
RED_RC=$?
echo "红轮 rc=$RED_RC"
echo ""
echo "════ 红轮判据（逐条，带出处）════"
echo "① 变异生效 —— 用例内 print 的绝对路径:"
grep -o 'NEGCTL-MUTATION-EFFECTIVE abs=.*' "$E/negctl-r2-red.txt" || echo "  ⛔ 未找到"
echo "  文件系统实证: $(test -d "$TREE/backend/raw/_probe" && echo "backend/raw/_probe 存在 ✅" || echo "⛔ 不存在")"
echo "② 拒因身份（必须是本卡的门）:"
grep -o 'CARD-TEST-hygiene-vaultinit 不变量门' "$E/negctl-r2-red.txt" | head -1 || echo "  ⛔ 未找到"
echo "③ 指名 backend/raw:"
grep -o '新出现 vault 骨架: .*raw' "$E/negctl-r2-red.txt" | head -1 || echo "  ⛔ 未找到"
echo "④ 被测用例本身 passed（红只来自门）:"
grep -E '^\s*1 passed.*error|passed.*1 error' "$E/negctl-r2-red.txt" | head -1
echo "⑤ 红轮 ERROR 的 nodeid:"
grep -E '^ERROR tests/' "$E/negctl-r2-red.txt"
echo "⑥ 红轮 rc = $RED_RC （非 0 才算门起作用）"

# ───────── 清污染 + 绿轮 ─────────
"$TREE/backend/.venv/bin/python" - <<'PY'
import shutil, pathlib
p = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/raw")
if p.exists(): shutil.rmtree(p); print("已清红轮污染 backend/raw")
PY

cat > "$PROBE" <<'PY'
"""临时负控用例 —— 绿轮：同一用例，同一断言，只把写入目标换成 tmp_path。"""

from pathlib import Path


def test_negctl_writes_into_repo(tmp_path: Path):
    target = tmp_path / "raw/_probe"
    target.mkdir(parents=True, exist_ok=True)
    assert target.is_dir(), "变异未生效：raw/_probe 未创建"
    print(f"NEGCTL-MUTATION-EFFECTIVE abs={target.resolve()}")
PY

echo ""
echo "════ 绿轮：还原后源码（逐字，nodeid 与红轮相同）════"
cat "$PROBE"
echo "还原文件 sha: $(shasum -a 256 "$PROBE" | awk '{print $1}')"

PYTHONDONTWRITEBYTECODE=1 "${RED_CMD[@]}" > "$E/negctl-r2-green.txt" 2>&1
GREEN_RC=$?
echo ""
echo "════ 绿轮判据 ════"
echo "① 同一 nodeid 通过:"
grep -E '^tests/unit/test_zz_hygiene_negctl|1 passed' "$E/negctl-r2-green.txt" | head -2
echo "② 写入目标（应在 tmp_path 内，不在仓库）:"
grep -o 'NEGCTL-MUTATION-EFFECTIVE abs=.*' "$E/negctl-r2-green.txt" || echo "  (未捕获 print，-q 模式下 passed 用例不打印)"
echo "③ 门未误报: $(grep -c 'CARD-TEST-hygiene-vaultinit 不变量门' "$E/negctl-r2-green.txt") 次（应 0）"
echo "④ backend/raw 不存在: $(test -e "$TREE/backend/raw" && echo '⛔ 仍存在' || echo '✅')"
echo "⑤ 绿轮 rc = $GREEN_RC （应为 0）"

echo ""
echo "════ 生产代码 sha（跑后，须与跑前逐字相同）════"
shasum -a 256 tests/unit/conftest.py app/api/v1/system.py tests/unit/test_startup_health_check.py
echo ""
echo "════ 结论 ════"
echo "红轮 rc=$RED_RC / 绿轮 rc=$GREEN_RC  → $([ "$RED_RC" -ne 0 ] && [ "$GREEN_RC" -eq 0 ] && echo '门承重成立 ✅' || echo '⛔ 不成立')"
