#!/bin/bash
# 定向 H2：在【改前代码】上对 setup-wizard 端点跑 schemathesis 属性输入。
# 全量 206 operation 需约 13 小时（实测 4 个 / 15:29），故缩到相关端点。
# 交换生产文件 → 必须 EXIT trap 无条件还原 + 事后 sha 自证。
set -uo pipefail

TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
E="$TREE/_bmad-output/审查/evidence-hygiene"
SCRATCH=/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-y6-testhygiene/d126f448-9717-47fb-9f6d-96b7e5259035/scratchpad
TARGET="$TREE/backend/app/api/v1/system.py"
MINE="$SCRATCH/system.py.mine"

cd "$TREE" || exit 90

# ── 备份我的版本 + 无条件还原 trap ─────────────────────────────────────────
cp "$TARGET" "$MINE" || exit 91
MINE_SHA=$(shasum -a 256 "$MINE" | awk '{print $1}')
restore() {
  cp "$MINE" "$TARGET"
  local now
  now=$(shasum -a 256 "$TARGET" | awk '{print $1}')
  if [ "$now" = "$MINE_SHA" ]; then
    echo "RESTORE-OK sha=$now"
  else
    echo "RESTORE-FAIL expected=$MINE_SHA got=$now  ⛔ 生产文件未还原!"
  fi
}
trap restore EXIT

# ── 换成 HEAD（改前）版本并自证 ────────────────────────────────────────────
git show HEAD:backend/app/api/v1/system.py > "$TARGET" || exit 92
HEAD_SHA=$(git show HEAD:backend/app/api/v1/system.py | shasum -a 256 | awk '{print $1}')
NOW_SHA=$(shasum -a 256 "$TARGET" | awk '{print $1}')
echo "=== 已换为改前代码 ==="
echo "HEAD sha = $HEAD_SHA"
echo "现文件 sha = $NOW_SHA"
[ "$HEAD_SHA" = "$NOW_SHA" ] || { echo "⛔ 换版失败"; exit 93; }
echo "改前代码是否含 field_validator（应为 0）: $(grep -c 'field_validator' "$TARGET")"

# ── 武装三签名 ─────────────────────────────────────────────────────────────
TS=$(date +%s)
for d in /tmp/test-vault /tmp/test-vault-wizard; do
  [ -e "$d" ] && mv "$d" "$d.h2d-$TS"
done
touch "$E/sentinel-h2d"
shasum -a 256 backend/config/subject_mapping.yaml backend/.gitignore > "$E/sha-before-h2d.txt"
echo "=== 武装后四路径 ==="
for p in backend/raw backend/wiki backend/outputs backend/CLAUDE.md; do
  [ -e "$p" ] && echo "  ⚠️ EXISTS $p" || echo "  absent $p"
done

# ── 跑定向 H2 ──────────────────────────────────────────────────────────────
L="$E/h2-directed-$(date +%Y%m%dT%H%M%S).txt"
echo "=== 跑定向 H2 → $L ==="
cd "$TREE/backend" || exit 94
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest \
  tests/contract/test_openapi_contract.py -k setup \
  -q -p no:cacheprovider -p no:randomly --override-ini='addopts=' > "$L" 2>&1
RC=$?
# 硬前置断言: 必须真的跑了 1 个用例, 否则「无污染」是假绿
if ! grep -qE '^(1 passed|1 failed|1 error)' "$L" && ! grep -qE '1 (passed|failed|error)' "$L"; then
  echo "⛔ 定向 H2 未实际执行 1 个用例 —— 本次判据无效, 不得据此下结论"
  echo "--- log 尾部 ---"; tail -5 "$L"
  exit 96
fi
echo "前置断言 OK: 确实执行了用例"
echo "rc=$RC" >> "$L"
echo "pytest rc=$RC"
tail -3 "$L"

# ── 采集判据（仍在改前代码下）──────────────────────────────────────────────
cd "$TREE" || exit 95
{
  echo "=== 定向 H2 判据（改前代码） ==="
  echo "--- 签名① backend 四路径 ---"
  for p in backend/raw backend/wiki backend/outputs backend/CLAUDE.md; do
    [ -e "$p" ] && echo "  ⚠️ EXISTS $p" || echo "  absent $p"
  done
  echo "--- 签名① git status backend ---"
  git -c core.quotepath=false status --porcelain backend | sed 's/^/  /'
  echo "--- find -maxdepth 1 -newer sentinel ---"
  find backend -maxdepth 1 -newer "$E/sentinel-h2d" -not -name .venv | sed 's/^/  /'
  echo "--- 签名③ sha diff ---"
  shasum -a 256 backend/config/subject_mapping.yaml backend/.gitignore | diff "$E/sha-before-h2d.txt" - && echo "  (未变)"
  echo "--- 签名② /tmp ---"
  ls -d /tmp/test-vault /tmp/test-vault-wizard 2>&1 | sed 's/^/  /'
} 2>&1 | tee "$E/status-after-h2-directed.txt"
