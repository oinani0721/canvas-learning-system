#!/bin/bash
# (c) 负控：证明不变量 fixture 真的承重。
#   红轮 = 临时用例往 backend/raw 写 → fixture 必须 fail 且【消息里指名 backend/raw】
#   绿轮 = 同一用例不写 → fixture 必须放行
# 判据绑定失败身份，不用「rc != 0」这种粗判据。
set -uo pipefail

TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
E="$TREE/_bmad-output/审查/evidence-hygiene"
PROBE="$TREE/backend/tests/unit/test_zz_hygiene_negctl.py"

cleanup() {
  rm -f "$PROBE" 2>/dev/null
  "$TREE/backend/.venv/bin/python" - <<'PY' 2>/dev/null
import shutil, pathlib
p = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/raw")
if p.exists():
    shutil.rmtree(p)
    print("cleanup: removed backend/raw")
PY
  echo "--- cleanup 后 git status backend ---"
  git -C "$TREE" -c core.quotepath=false status --porcelain backend
}
trap cleanup EXIT

cd "$TREE/backend" || exit 90

# ════════════════ 红轮 ════════════════
cat > "$PROBE" <<'PY'
"""临时负控用例（CARD-TEST-hygiene-vaultinit (c)）—— 不入 commit。

模拟「测试往代码目录里写东西」。用相对路径, 与真实缺陷同形态:
pytest 从 backend/ 起跑, 所以 Path("raw/_probe") 就是 backend/raw/_probe。
"""

from pathlib import Path


def test_negctl_writes_into_repo():
    Path("raw/_probe").mkdir(parents=True, exist_ok=True)
    assert Path("raw/_probe").is_dir()
PY

RED="$E/negctl-red.txt"
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest tests/unit/test_zz_hygiene_negctl.py \
  -q -p no:cacheprovider -p no:randomly --override-ini='addopts=' > "$RED" 2>&1
RED_RC=$?
echo "=== 红轮 rc=$RED_RC ==="
tail -20 "$RED"

echo ""
echo "=== 红轮判据（三条都要成立）==="
# ① 变异确实生效：backend/raw 真被造出来了（否则绿轮的绿是自证）
if [ -d "$TREE/backend/raw/_probe" ]; then echo "  ① 变异生效 backend/raw/_probe 存在: PASS"; else echo "  ① 变异生效: FAIL ⛔ 变异没跑, 本轮无效"; fi
# ② 失败身份：必须是本卡这道门，且指名 backend/raw
if grep -q 'CARD-TEST-hygiene-vaultinit 不变量门' "$RED"; then echo "  ② 拒因出自本卡的门: PASS"; else echo "  ② 拒因出自本卡的门: FAIL ⛔"; fi
if grep -q "新出现 vault 骨架.*backend/raw" "$RED"; then echo "  ③ 消息指名 backend/raw: PASS"; else echo "  ③ 消息指名 backend/raw: FAIL ⛔"; fi
# ④ 被测用例本身是通过的（红只能来自门，不能来自用例断言）
if grep -qE '1 passed' "$RED"; then echo "  ④ 用例本身 passed（红只来自门）: PASS"; else echo "  ④ 用例本身 passed: 需人工看 log"; fi

# ════════════════ 清掉污染, 跑绿轮 ════════════════
./.venv/bin/python - <<'PY'
import shutil, pathlib
p = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/raw")
if p.exists():
    shutil.rmtree(p); print("已清掉红轮造的 backend/raw")
PY

cat > "$PROBE" <<'PY'
"""临时负控用例 —— 绿轮：同一个用例，不往仓库写。"""

from pathlib import Path


def test_negctl_writes_into_repo(tmp_path: Path):
    (tmp_path / "raw/_probe").mkdir(parents=True, exist_ok=True)
    assert (tmp_path / "raw/_probe").is_dir()
PY

GREEN="$E/negctl-green.txt"
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest tests/unit/test_zz_hygiene_negctl.py \
  -q -p no:cacheprovider -p no:randomly --override-ini='addopts=' > "$GREEN" 2>&1
GREEN_RC=$?
echo ""
echo "=== 绿轮 rc=$GREEN_RC ==="
tail -6 "$GREEN"
echo ""
echo "=== 绿轮判据 ==="
if [ "$GREEN_RC" -eq 0 ]; then echo "  rc=0: PASS"; else echo "  rc=$GREEN_RC: FAIL ⛔"; fi
if grep -q 'CARD-TEST-hygiene-vaultinit 不变量门' "$GREEN"; then echo "  门未误报: FAIL ⛔ 门在绿轮也报了"; else echo "  门未误报: PASS"; fi
if [ -e "$TREE/backend/raw" ]; then echo "  backend/raw 不存在: FAIL ⛔"; else echo "  backend/raw 不存在: PASS"; fi
