#!/usr/bin/env bash
# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
set -uo pipefail

export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="${HOME:-/Users/Heishing}"
export LANG="zh_CN.UTF-8"

BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
# 第一行探针: 连 ~/Library 都写不了 = launchd 环境彻底异常
echo "[$(date '+%F %T')] wrapper start" >> "$BOOTLOG"

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"

fail() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; exit 78; }
warn() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; }

# VAULT-SYNC (2026-08-02 用户拍板): 推送 vault 与 .env ACTIVE_VAULT 同源 —
# P0-3 确立「vault 由部署期 .env 固定」后, 推送链不再独立写死, 换 vault
# 只改 .env 一处, 后端/skills/推送全部跟走。解析失败回退 canvas-vault
# (与旧行为一致); VAULTS_ROOT 取 .env 宿主侧值, 缺省回退主仓根。
ENV_FILE="$WT/.env"
ACTIVE_VAULT=$(grep -E '^ACTIVE_VAULT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
VAULTS_ROOT_HOST=$(grep -E '^VAULTS_ROOT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')

# CARD-C1a 多 vault: .env DAILY_REVIEW_VAULTS (逗号/空格分隔目录名, 不支持
# 含空格的目录名) 声明推送清单, 缺省回退单 vault ACTIVE_VAULT。循环留在
# shell 层、每 vault 独立 runner 进程 — 严禁下沉 Python 进程内循环:
# pick.load_decay 的 sys.path + import 缓存会让第二个 vault 拿到第一个
# vault 的 decay_beta 模块 (pick.py:345 已知坑)。
REVIEW_VAULTS=$(grep -E '^DAILY_REVIEW_VAULTS=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
VAULT_NAMES=$(printf '%s' "${REVIEW_VAULTS:-${ACTIVE_VAULT:-canvas-vault}}" | tr ',' ' ')
# 未引号 for 循环只做词分割, 禁 glob 展开 (名含 * ? [ 不得变成文件匹配)
set -f
# 空清单守卫 (Codex-C1a round2/3: ",,," 或纯 TAB 都会让循环 0 次并成功
# 退出 — 静默不推任何库; 判空须剔除全部空白类字符)
[ -n "$(printf '%s' "$VAULT_NAMES" | tr -d '[:space:]')" ] \
    || fail "empty_vault_list — DAILY_REVIEW_VAULTS/ACTIVE_VAULT 解析为空"

# repo 级 preflight (与具体 vault 无关, 失败 = 整体异常直接退)
mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
# containment 基准: VAULTS_ROOT 物理路径 (symlink 穿透检查用, Codex-C1a F6)
REAL_ROOT=$(cd "${VAULTS_ROOT_HOST:-$REPO}" 2>/dev/null && pwd -P) \
    || fail "vaults_root_unreadable — ${VAULTS_ROOT_HOST:-$REPO}"

overall=0
for name in $VAULT_NAMES; do
    # 清单项必须是 VAULTS_ROOT 下的单层目录名 — 拒绝路径穿越与 glob 字符
    # (与 .env.example 声明一致; ../outside 会把推送链带出 vault 域)
    case "$name" in
        */*|..|.|*\**|*\?*|*\[*)
            echo "[$(date '+%F %T')] PREFLIGHT-FAIL: invalid_vault_name ($name) — 只允许 VAULTS_ROOT 下的目录名" >> "$BOOTLOG"
            [ "$overall" -eq 0 ] && overall=78
            continue
            ;;
    esac
    VAULT="${VAULTS_ROOT_HOST:-$REPO}/$name"
    # symlink containment (Codex-C1a F6): 清单项字面合法但可以是指向
    # VAULTS_ROOT 外的 symlink — 物理路径必须仍在 root 内, 否则推送链
    # 会读写 root 外的目录
    REAL_VAULT=$(cd "$VAULT" 2>/dev/null && pwd -P) || REAL_VAULT=""
    case "$REAL_VAULT/" in
        "$REAL_ROOT"/*) ;;
        *)
            warn "vault_outside_root ($name → ${REAL_VAULT:-unresolvable}) — 清单项须是 VAULTS_ROOT 下的真实目录"
            [ "$overall" -eq 0 ] && overall=78
            continue
            ;;
    esac
    # TOCTOU 收口 (round3 F6): 校验通过后全程改用物理路径 — alias 在校验
    # 后换向不再影响本轮 (后续 cmp/push 不再解析字面名)。
    # 已知边界 (round4/5, 已接受的 LOW 残余): "物理路径字符串在校验后被
    # rename 顶替为 symlink" 的竞态, 稳健闭合需 dirfd/openat 型 fd-relative
    # I/O。当前威胁模型 (单用户机、同一信任域): 能做该竞态改名的主体已
    # 拥有对 vault 数据的完全控制权, 不构成特权边界。⚠ 若未来把同 UID
    # 但受 App Sandbox/TCC 限权的进程纳入威胁模型 (本部署给 /bin/bash
    # Full Disk Access), 需重开此项 — 受限 app 可借该竞态让 wrapper 充当
    # confused deputy 读写其本无权访问的路径。
    VAULT="$REAL_VAULT"
    echo "[$(date '+%F %T')] vault=$VAULT (清单=${VAULT_NAMES})" >> "$BOOTLOG"
    # TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走
    # access() 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍
    # Operation not permitted), 只有 ls/head 这类真 I/O 才探得出来。
    # 单 vault 坏不拖累其余 vault: 记 BOOTLOG 后 continue, 整体退 78。
    if ! ls "$VAULT/节点" >/dev/null 2>&1; then
        warn "vault_not_readable_tcc ($name) — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
        [ "$overall" -eq 0 ] && overall=78
        continue
    fi
    # 双副本一致性 (Code-Review M4 + FSRS-V2 H1): runner/quiz-answer 用的是
    # 活 vault 里的副本, worktree 改了忘 cp 会造成静默行为漂移
    skew=0
    for f in decay_beta.py fsrs_bridge.py; do
        cmp -s "$WT/canvas-vault/.claude/scripts/$f" \
               "$VAULT/.claude/scripts/$f" \
            || { warn "${f}_version_skew ($name) — worktree 与活 vault 副本不一致, 需 cp 部署"; skew=1; }
    done
    if [ "$skew" = 1 ]; then
        [ "$overall" -eq 0 ] && overall=78
        continue
    fi
    # --vault 放在 "$@" 之后: runner argparse 与 push.sh 锁解析都取最后一次
    # 出现的值 — 外部若误传 --vault 也不能打穿循环 (编排者 wrapper 说了算)。
    # 退出码取自裸 $? (Codex-C1a F5: `if ! cmd; then rc=$?` 拿到的是取反
    # 后的 0, launchd 假绿), 保首个非零不互相掩盖。
    "$WT/scripts/daily-review-push.sh" "$@" --vault "$VAULT"
    rc=$?
    if [ "$rc" -ne 0 ] && [ "$overall" -eq 0 ]; then
        overall=$rc
    fi
done
exit $overall
