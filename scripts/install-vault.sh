#!/usr/bin/env bash
# Canvas Learning System — vault 一键部署 (DEPLOY-VAULT-2026-08-02, 方案 1 用户拍板)
#
# 「活 vault 即模板」: 从当前活 vault 复制全部系统件到新 vault, 没有第二份
# 模板要维护 (decay_beta.py 双副本 skew 教训)。系统件清单显式声明在下方
# MANIFEST 区 — 部署边界一目了然: 复制的是"系统", 不碰任何学习数据。
#
# 用法:
#   scripts/install-vault.sh <vault-name> [--subject <学科>] [--activate]
#                            [--vaults-root <dir>] [--source <vault-dir>]
#                            [--env-file <path>]
#   --activate: 把 .env ACTIVE_VAULT 切到新 vault (之后需 docker compose up -d backend)
#   缺省只部署不激活 — 可先建多个 vault 再选一个激活。
set -euo pipefail

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
ENV_FILE="$WT/.env"
VAULTS_ROOT="$REPO"
SOURCE=""
SUBJECT=""
ACTIVATE=0

VAULT_NAME="${1:?用法: install-vault.sh <vault-name> [--subject <学科>] [--activate]}"
shift
while [ $# -gt 0 ]; do
    case "$1" in
        --subject)     SUBJECT="$2"; shift 2 ;;
        --activate)    ACTIVATE=1; shift ;;
        --vaults-root) VAULTS_ROOT="$2"; shift 2 ;;
        --source)      SOURCE="$2"; shift 2 ;;
        --env-file)    ENV_FILE="$2"; shift 2 ;;
        *) echo "未知参数: $1" >&2; exit 64 ;;
    esac
done
SUBJECT="${SUBJECT:-$VAULT_NAME}"

# 审查 M1: vault 名白名单 — 特殊字符各有恶果 (& 破坏 sed 替换写坏 .env,
# / 嵌套进活 vault, .. 逃逸 VAULTS_ROOT, 引号破坏 yaml, -开头误当 flag)
case "$VAULT_NAME" in
    -*|*/*|*..*|*'|'*|*'&'*|*'"'*|*"'"*|*$'\n'*|*$'\t'*)
        echo "❌ vault 名含非法字符 (不允许: 开头-、/、..、|、&、引号、换行): $VAULT_NAME" >&2
        exit 64 ;;
esac

# 模板源: 缺省从 .env ACTIVE_VAULT + .env 宿主侧 VAULTS_ROOT 解析活 vault
# (与推送 VAULT-SYNC 同一逻辑)。注意源解析独立于 --vaults-root (那是目标根,
# 测试场景会指向 scratch 目录, 模板源不能跟着跑偏)。
if [ -z "$SOURCE" ]; then
    # 审查 M2: || true 防 set -e 在 .env 缺失/缺行时静默死亡, 让回退值生效
    AV=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
    SRC_ROOT=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
    SOURCE="${SRC_ROOT:-$REPO}/${AV:-canvas-vault}"
fi
TARGET="$VAULTS_ROOT/$VAULT_NAME"

[ -d "$SOURCE/.claude/skills" ] || { echo "❌ 模板源不完整 (缺 .claude/skills): $SOURCE" >&2; exit 65; }
[ -e "$TARGET" ] && { echo "❌ 目标已存在, 拒绝覆盖 (防误伤学习数据): $TARGET" >&2; exit 66; }

# ═══════════════════════════════════════════════════════════════════
# MANIFEST — 系统件清单 (相对 vault 根)。改动部署边界只改这里。
# ═══════════════════════════════════════════════════════════════════
SKELETON_DIRS=(原白板 检验白板 节点 outputs raw templates)
CLAUDE_ITEMS=(skills scripts hooks agents commands settings.json settings.local.json mcp.json)
OBSIDIAN_FILES=(app.json appearance.json core-plugins.json community-plugins.json hotkeys.json cls-internal-key.txt)
OBSIDIAN_PLUGINS=(canvas-learning-system claudian dataview breadcrumbs templater-obsidian)
ROOT_FILES=(CLAUDE.md Dashboard.md)
# 明确不复制: 原白板/检验白板/节点 内容、learning_events.jsonl、outputs 产物、
# workspace.json (会话状态)、.canvas-config.yaml (按 vault 重新生成)

echo "📦 部署 Canvas Learning System → $TARGET"
echo "   模板源: $SOURCE"

for d in "${SKELETON_DIRS[@]}"; do mkdir -p "$TARGET/$d"; done
mkdir -p "$TARGET/.claude" "$TARGET/.obsidian/plugins"

for item in "${CLAUDE_ITEMS[@]}"; do
    if [ -e "$SOURCE/.claude/$item" ]; then
        cp -R "$SOURCE/.claude/$item" "$TARGET/.claude/$item"
    else
        echo "   ⚠️ 模板缺 .claude/$item — 跳过"
    fi
done
find "$TARGET/.claude" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
# 审查 L4: hooks 目录会连带旧 vault 的归档队列文件 — 新 vault 不得重放
rm -f "$TARGET/.claude/hooks/pending_archives"*.jsonl 2>/dev/null || true

for f in "${OBSIDIAN_FILES[@]}"; do
    [ -e "$SOURCE/.obsidian/$f" ] && cp "$SOURCE/.obsidian/$f" "$TARGET/.obsidian/$f" \
        || echo "   ⚠️ 模板缺 .obsidian/$f — 跳过"
done
for p in "${OBSIDIAN_PLUGINS[@]}"; do
    [ -d "$SOURCE/.obsidian/plugins/$p" ] && cp -R "$SOURCE/.obsidian/plugins/$p" "$TARGET/.obsidian/plugins/$p" \
        || echo "   ⚠️ 模板缺插件 $p — 跳过"
done

for f in "${ROOT_FILES[@]}"; do
    [ -e "$SOURCE/$f" ] && cp "$SOURCE/$f" "$TARGET/$f" || echo "   ⚠️ 模板缺 $f — 跳过"
done

# .canvas-config.yaml 按 vault 重新生成 (vault_id 交给后端 sanitize —
# yaml-first 契约见 backend/tests/unit/test_vault_switch.py::TestVaultIdYamlFirst)
cat > "$TARGET/.canvas-config.yaml" <<EOF
# Canvas Learning System · Vault 级配置 (install-vault.sh 生成)
# 本 vault 只学一个学科 (subject), 不跨学科。
vault_id: "$VAULT_NAME"
subject: "$SUBJECT"
schema_version: "2.0-multi-vault-2026-05-10"
EOF

# ── 自检 ──────────────────────────────────────────────────────────
PASS=0; FAIL=0
check() { if eval "$2"; then echo "   ✅ $1"; PASS=$((PASS+1)); else echo "   ❌ $1"; FAIL=$((FAIL+1)); fi; }
echo ""
echo "🔍 自检:"
check "骨架目录 5 个"            '[ -d "$TARGET/原白板" ] && [ -d "$TARGET/检验白板" ] && [ -d "$TARGET/节点" ] && [ -d "$TARGET/outputs" ] && [ -d "$TARGET/raw" ]'
check "skills ≥8 个"             '[ "$(ls "$TARGET/.claude/skills" 2>/dev/null | wc -l)" -ge 8 ]'
check "decay_beta + fsrs_bridge" '[ -f "$TARGET/.claude/scripts/decay_beta.py" ] && [ -f "$TARGET/.claude/scripts/fsrs_bridge.py" ]'
check "hooks 配置 settings.json" '[ -f "$TARGET/.claude/settings.json" ]'
check "mcp.json"                 '[ -f "$TARGET/.claude/mcp.json" ]'
check "核心插件与模板源字节一致"  'cmp -s "$SOURCE/.obsidian/plugins/canvas-learning-system/main.js" "$TARGET/.obsidian/plugins/canvas-learning-system/main.js"'
check "插件启用清单+快捷键"       '[ -f "$TARGET/.obsidian/community-plugins.json" ] && [ -f "$TARGET/.obsidian/hotkeys.json" ]'
check "后端鉴权 key"             '[ -f "$TARGET/.obsidian/cls-internal-key.txt" ]'
check "Dashboard + CLAUDE.md"    '[ -f "$TARGET/Dashboard.md" ] && [ -f "$TARGET/CLAUDE.md" ]'
check "vault 配置 yaml"          'grep -q "vault_id" "$TARGET/.canvas-config.yaml"'

# 审查 H1: 自检有 ❌ 时禁止激活 — 不把后端切到坏 vault
# 审查 M3: 目标根偏离 .env VAULTS_ROOT (compose 挂载源) 时禁止激活 —
# 容器看不见挂载外的 vault, 激活即 404
ENV_VROOT=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
if [ "$ACTIVATE" = 1 ] && [ "$FAIL" != 0 ]; then
    echo "   ⛔ 自检有失败项, 跳过激活 (.env 未改)"
    ACTIVATE=0
fi
if [ "$ACTIVATE" = 1 ] && [ -n "$ENV_VROOT" ] && [ "$VAULTS_ROOT" != "$ENV_VROOT" ]; then
    echo "   ⛔ 目标根 ($VAULTS_ROOT) ≠ .env VAULTS_ROOT ($ENV_VROOT) — 容器看不见此 vault, 跳过激活"
    ACTIVATE=0
fi
if [ "$ACTIVATE" = 1 ]; then
    if grep -qE '^ACTIVE_VAULT=' "$ENV_FILE"; then
        sed -i '' "s|^ACTIVE_VAULT=.*|ACTIVE_VAULT=$VAULT_NAME|" "$ENV_FILE"
    else
        printf '\nACTIVE_VAULT=%s\n' "$VAULT_NAME" >> "$ENV_FILE"
    fi
    check "已激活 (.env ACTIVE_VAULT)" 'grep -qF "ACTIVE_VAULT=$VAULT_NAME" "$ENV_FILE"'
    NEXT_ACTIVATE="⚠️ 生效需重启后端: docker compose up -d backend"
else
    NEXT_ACTIVATE="激活: scripts/install-vault.sh 加 --activate, 或手改 .env ACTIVE_VAULT=$VAULT_NAME 后 docker compose up -d backend"
fi

echo ""
echo "═══ 结果: $PASS 项通过 / $FAIL 项失败 ═══"
echo "📋 后续步骤:"
echo "   1. Obsidian → 打开 vault → $TARGET (插件与快捷键已随 vault 就位)"
echo "   2. $NEXT_ACTIVATE"
echo "   3. 首验: 在新 vault 建原白板 (Cmd+P 建/配置原白板) → 写内容 → /start-exam-board 应能出题"
[ "$FAIL" = 0 ] || exit 1
