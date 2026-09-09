#!/usr/bin/env bash
# Canvas Learning System — vault 一键部署 (DEPLOY-VAULT-2026-08-02, 方案 1 用户拍板)
#
# 模板源 (E-4, CARD-G2-7a): `<harness>/canvas-vault/` 的 git 追踪系统件 + 本脚本
# 的生成件。`--source` 可改指一个活 vault, 用来取那些 gitignored、树里本就没有的件
# (Obsidian 配置、第三方插件、插件 data.json)。清单显式声明在下方 MANIFEST 区 —
# 部署边界一目了然: 复制的是"系统", 不碰任何学习数据。
# ⚠️ 每 vault 应当不同的东西 (后端鉴权 key、插件绑定值、MCP 批准) 一律**生成**而非复制,
#    否则会把上一个 vault 的私有状态带进新库。
#
# 用法:
#   scripts/install-vault.sh <vault-name> [--subject <学科>] [--activate]
#                            [--vaults-root <dir>] [--source <vault-dir>]
#                            [--env-file <path>] [--harness-tree <path>]
#                            [--backend-url <url>]
#   --harness-tree / --backend-url: 只写进新 vault 的 .canvas-config.yaml (schema 2.1),
#     供 skill 侧定位 harness 树与后端地址; 不影响复制行为。
#   --activate: 把 .env ACTIVE_VAULT 切到新 vault (之后需 docker compose up -d backend)
#   缺省只部署不激活 — 可先建多个 vault 再选一个激活。
set -euo pipefail

REPO="${CLS_REPO:-/Users/Heishing/Desktop/canvas/canvas-learning-system}"  # CLS_REPO 可覆盖仓根 (测试/换机); 不设时逐字节同旧值
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
ENV_FILE="$WT/.env"
VAULTS_ROOT="$REPO"
SOURCE=""
SUBJECT=""
ACTIVATE=0
HARNESS_TREE="$WT"                        # 写进 yaml 的 harness_tree (skill 侧定位仓根)
BACKEND_URL="http://127.0.0.1:8011"       # 写进 yaml 的 backend_url (与 .mcp.json 同源)

VAULT_NAME="${1:?用法: install-vault.sh <vault-name> [--subject <学科>] [--activate]}"
shift
while [ $# -gt 0 ]; do
    case "$1" in
        --subject)     SUBJECT="$2"; shift 2 ;;
        --activate)    ACTIVATE=1; shift ;;
        --vaults-root) VAULTS_ROOT="$2"; shift 2 ;;
        --source)      SOURCE="$2"; shift 2 ;;
        --env-file)    ENV_FILE="$2"; shift 2 ;;
        --harness-tree) HARNESS_TREE="$2"; shift 2 ;;
        --backend-url)  BACKEND_URL="$2"; shift 2 ;;
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

# 模板源 (E-4, CARD-G2-7a): 缺省 = **harness 树的 canvas-vault/**(git 追踪系统件)。
# ⚠️ 不再从 .env ACTIVE_VAULT 解析 —— 那会把「当前活 vault」当模板, 活 vault 里的
# gitignored 件(密钥/插件绑定值)会整个带进新库, 正是 E-3 要停的行为。
# 要取那些 gitignored 件(Obsidian 配置/第三方插件), **显式** --source <活 vault>。
if [ -z "$SOURCE" ]; then
    SOURCE="$REPO/canvas-vault"
fi
TARGET="$VAULTS_ROOT/$VAULT_NAME"

[ -d "$SOURCE/.claude/skills" ] || { echo "❌ 模板源不完整 (缺 .claude/skills): $SOURCE" >&2; exit 65; }
[ -e "$TARGET" ] && { echo "❌ 目标已存在, 拒绝覆盖 (防误伤学习数据): $TARGET" >&2; exit 66; }

# ═══════════════════════════════════════════════════════════════════
# MANIFEST — 系统件清单 (相对 vault 根)。改动部署边界只改这里。
# ═══════════════════════════════════════════════════════════════════
SKELETON_DIRS=(原白板 检验白板 节点 outputs raw templates wiki/concepts wiki/canvases)
CLAUDE_ITEMS=(skills scripts hooks agents commands settings.json)
OBSIDIAN_FILES=(app.json appearance.json core-plugins.json community-plugins.json hotkeys.json templates/concept.md templates/exam-board.md themes/Underwater/manifest.json themes/Underwater/theme.css)
OBSIDIAN_PLUGINS=(canvas-learning-system dataview breadcrumbs templater-obsidian)
ROOT_FILES=(CLAUDE.md Dashboard.md .mcp.json)
# 明确不复制: 原白板/检验白板/节点 内容、learning_events.jsonl、outputs 产物、
# workspace.json (会话状态)、.canvas-config.yaml (按 vault 重新生成)

echo "📦 部署 Canvas Learning System → $TARGET"
echo "   模板源: $SOURCE"

for d in "${SKELETON_DIRS[@]}"; do mkdir -p "$TARGET/$d"; done
mkdir -p "$TARGET/.claude" "$TARGET/.obsidian/plugins"

for item in "${CLAUDE_ITEMS[@]}"; do
    if [ -e "$SOURCE/.claude/$item" ]; then
        # -H: 跟随**操作数**软链复制成真目录。裸 -R 会把目录软链原样放进 TARGET,
        # 后续清理/生成沿链写穿模板源(实测 macOS cp -R 保留链接, shared data.json 被改)。
        cp -R -H "$SOURCE/.claude/$item" "$TARGET/.claude/$item"
    else
        echo "   ⚠️ 模板缺 .claude/$item — 跳过"
    fi
done
find "$TARGET/.claude" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
# 审查 L4: hooks 目录会连带旧 vault 的归档队列文件 — 新 vault 不得重放
rm -f "$TARGET/.claude/hooks/pending_archives"*.jsonl 2>/dev/null || true

for f in "${OBSIDIAN_FILES[@]}"; do
    # 数组里现在有含 `/` 的条目 (templates/*.md、themes/Underwater/*), 裸 cp 会因为
    # 父目录不存在而失败 —— 先建父目录。对不含 `/` 的条目 dirname 得到 `.`, mkdir -p 无副作用。
    mkdir -p "$(dirname "$TARGET/.obsidian/$f")"
    [ -e "$SOURCE/.obsidian/$f" ] && cp "$SOURCE/.obsidian/$f" "$TARGET/.obsidian/$f" \
        || echo "   ⚠️ 模板缺 .obsidian/$f — 跳过"
done
for p in "${OBSIDIAN_PLUGINS[@]}"; do
    # -H 同上: 插件目录若是软链, 必须复制内容而非链接 —— 否则生成段清 data.json
    # 会删到共享源、写入也会写穿(Codex round-2 HIGH-1, 实测坐实)。
    [ -d "$SOURCE/.obsidian/plugins/$p" ] && cp -R -H "$SOURCE/.obsidian/plugins/$p" "$TARGET/.obsidian/plugins/$p" \
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
# 如需切换学科 → 新建 vault: 仓根 .claude/skills/deploy-vault/SKILL.md (不在 vault 内)。
vault_id: "$VAULT_NAME"
subject: "$SUBJECT"
schema_version: "2.1-vault-harness-2026-09-07"
# backend_url: 后端地址, 与 .mcp.json 同源 (缺省 127.0.0.1:8011)。
backend_url: "$BACKEND_URL"
# harness_tree: 这套 vault 归哪棵 harness 树管 — skill 侧据此定位 backend/scripts,
#   不再靠 os.path.dirname(VAULT) 猜 (quiz-answer/SKILL.md:333 那条假设)。
harness_tree: "$HARNESS_TREE"
# push_enabled: 缺省 false; 由 deploy-vault.sh --also-push 打开 (CARD-G2-7b)。
push_enabled: false
EOF

# ── 生成件 (CARD-G2-7a): 每 vault 应当**不同**的东西一律生成, 不从模板源复制 ──
# ⚠️ 先清再写: 插件目录是**整目录** cp -R 过来的, --source 指 live 时 live 的旧 data.json
#    (含上一个 vault 的 internalApiKey/backendUrl)会跟着进来 —— 只靠下面的 [ ! -e ] 生成
#    会被它短路。生成位必须先删, 与上面清会话残留件同一模式。
#    (Codex round-1 HIGH-1; (h)② 真跑实测目标 data.json 里是 live 的真实 key。)
# ⚠️ 后端鉴权 key 不在这里生成: 它归 deploy-vault.sh 的 activate 步 (CARD-G2-7b),
#    那一步才知道要跟哪个后端实例配对。自检 :key 反向判会确认这里**没有**从源复制过来。
rm -f "$TARGET/.obsidian/plugins/canvas-learning-system/data.json" \
      "$TARGET/.obsidian/plugins/templater-obsidian/data.json" \
      "$TARGET/.claude/settings.local.json"

PLUGIN_DATA="$TARGET/.obsidian/plugins/canvas-learning-system/data.json"
if [ ! -e "$PLUGIN_DATA" ]; then    # 上面已清, 此守卫是防御式(防手工预放/未来重入)
    mkdir -p "$(dirname "$PLUGIN_DATA")"
    cat > "$PLUGIN_DATA" <<EOF
{
  "backendUrl": "$BACKEND_URL",
  "nodePathPrefixes": ["节点/"],
  "activeVaultName": "",
  "internalApiKey": ""
}
EOF
    echo "   ✏️  生成 插件 data.json (backendUrl=$BACKEND_URL; key 由 activate 步写入)"
fi

# templater 目录在树源部署时整个不存在(manifest optional), 只在 from-live 时被复制进来
TEMPLATER_DATA="$TARGET/.obsidian/plugins/templater-obsidian/data.json"
if [ -d "$(dirname "$TEMPLATER_DATA")" ] && [ ! -e "$TEMPLATER_DATA" ]; then
    cat > "$TEMPLATER_DATA" <<'TPLEOF'
{
  "templates_folder": ".obsidian/templates"
}
TPLEOF
    echo "   ✏️  生成 templater data.json (templates_folder)"
fi

# settings.local.json: 只批准本系统自己的 MCP。⛔ 绝不从模板源复制 —— 那会把上一个
# vault 的私有批准清单(含用户全局开发用 MCP)带进新库。键名核自 Claude Code 2.1.263。
CLAUDE_LOCAL="$TARGET/.claude/settings.local.json"
if [ ! -e "$CLAUDE_LOCAL" ]; then
    cat > "$CLAUDE_LOCAL" <<'LOCALEOF'
{
  "enabledMcpjsonServers": ["canvas-learning-mcp"]
}
LOCALEOF
    echo "   ✏️  生成 .claude/settings.local.json (只批准 canvas-learning-mcp)"
fi

# ── 自检 ──────────────────────────────────────────────────────────
PASS=0; FAIL=0
check() { if eval "$2"; then echo "   ✅ $1"; PASS=$((PASS+1)); else echo "   ❌ $1"; FAIL=$((FAIL+1)); fi; }
echo ""
echo "🔍 自检:"
check "骨架目录 (含 wiki 两件)"   '[ -d "$TARGET/原白板" ] && [ -d "$TARGET/检验白板" ] && [ -d "$TARGET/节点" ] && [ -d "$TARGET/outputs" ] && [ -d "$TARGET/raw" ] && [ -d "$TARGET/wiki/concepts" ] && [ -d "$TARGET/wiki/canvases" ]'
check "skills ≥8 个 (含 SKILL.md)" '[ "$(find "$TARGET/.claude/skills" -mindepth 2 -maxdepth 2 -type f -name SKILL.md 2>/dev/null | wc -l)" -ge 8 ]'
check "decay_beta + fsrs_bridge" '[ -f "$TARGET/.claude/scripts/decay_beta.py" ] && [ -f "$TARGET/.claude/scripts/fsrs_bridge.py" ]'
check "hooks 配置 settings.json" '[ -f "$TARGET/.claude/settings.json" ]'
check "MCP 注册件 .mcp.json"      '[ -f "$TARGET/.mcp.json" ]'
check "核心插件与模板源字节一致"  'if [ -e "$SOURCE/.obsidian/plugins/canvas-learning-system/main.js" ]; then cmp -s "$SOURCE/.obsidian/plugins/canvas-learning-system/main.js" "$TARGET/.obsidian/plugins/canvas-learning-system/main.js"; else echo "      ↳ 模板源没有 main.js — 先在 harness 树跑 npm run build (deploy-vault.sh preflight, CARD-G2-7b)"; false; fi'
check "插件启用清单+快捷键"       '[ -f "$TARGET/.obsidian/community-plugins.json" ] && [ -f "$TARGET/.obsidian/hotkeys.json" ]'
check "后端鉴权 key 未从源复制"   'K="$TARGET/.obsidian/cls-internal-key.txt"; S="$SOURCE/.obsidian/cls-internal-key.txt"; if [ ! -e "$K" ]; then true; elif [ -f "$K" ] && [ -r "$K" ] && [ -f "$S" ] && [ -r "$S" ]; then ! cmp -s "$S" "$K"; else echo "      ↳ key 形态/可读性异常, 无法证明未复制"; false; fi'
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
