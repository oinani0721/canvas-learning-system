#!/usr/bin/env bash
# ============================================================================
# DEBT-15 · hook 写副作用断言脚本
# BATCH-2026-08-29-第六批 / CARD-DEBT-15
#
# 目的：把「哪些 hook 允许写 git」变成可机械复核的硬门。
#       **被本扫描器识别到的**未登记 git 写 → FAIL；识别不到的构造一律
#       fail-closed 报 UNANALYZABLE / UNREACHABLE / UNPARSEABLE。
#
# ⚠️ 能力边界（Codex 两轮审查结论，勿高估）：
#    本脚本**不能**证明「所有未登记的 auto stage/commit/push 都会被抓到」。
#    未覆盖：managed/MDM settings、CLI --settings/--plugin-dir、
#    skill/agent frontmatter hooks。详见台账 §3.6。
#    ⇒ auto-sync 锁仍是主要防线，本脚本不是。
#
# ⛔⛔⛔ 首要警示（门 1）⛔⛔⛔
#   ~/.claude/auto-sync.lock.d 是一个 mkdir 原子锁的**僵尸残留**（持锁进程早死）。
#   它当前是**唯一一道在 `git add -A` 真正执行之前生效的闸门**，挡住主仓
#   Stop hook 对整个工作树做 stage + commit + push。
#   主仓现状：869 条 tracked 删除 + 1139 个 untracked 文件 + 2.2GB 未被
#   .gitignore 排除的 archive/ —— 一旦此锁被「清理」，下一次主仓 session 的
#   Stop 事件就会把它们全部 stage 并尝试提交推送。
#   ⇒ 本脚本门 1 断言该锁**必须存在**。禁止以「清理僵尸锁」为由删除它。
#
# 三道门：
#   门 1  锁哨兵        auto-sync.lock.d 必须存在
#   门 2  来源可达性    十处来源不得静默缺失（防「文件没了⇒扫不到⇒假 PASS」）
#   门 3  写副作用登记  未登记的 git 写 / 解析不了的命令 → FAIL（fail-closed）
#
# 命令解析交给 lib/scan_git_occurrences.py（真词法分析，非逐行正则）——
# 逐行正则会在下列写法上逐一失守，详见该文件头部说明：
#   git add -A 与 git add <path> 共享签名 / 一行多命令 / echo x && git push /
#   "git" push / git -C path push / 行尾注释里的假命令 / A.sh 调 B.sh
#
# 用法：
#   bash scripts/assert-hook-write-safety.sh            # 断言（判据命令）
#   bash scripts/assert-hook-write-safety.sh --list     # 列出实测签名
#   bash scripts/assert-hook-write-safety.sh --emit-ledger  # 输出台账表格
#
# 退出码：0=全门通过；1=有门 FAIL
# ============================================================================

set -uo pipefail

MODE="${1:-assert}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR="${SCRIPT_DIR}/lib/collect_hook_signatures.py"

# 四个锚点支持环境变量覆盖，**仅供负验证**在临时副本上做变异注入。
# ⛔ 特别是 DEBT15_LOCK_DIR：负验证靠指向不存在的临时路径触发门 1 FAIL，
#    **绝不允许**用删除真实 ~/.claude/auto-sync.lock.d 的方式来测试。
HOME_DIR="${DEBT15_HOME_DIR:-${HOME}}"
MAIN_REPO="${DEBT15_MAIN_REPO:-/Users/Heishing/Desktop/canvas/canvas-learning-system}"
WT_REPO="${DEBT15_WT_REPO:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
LOCK_DIR="${DEBT15_LOCK_DIR:-${HOME_DIR}/.claude/auto-sync.lock.d}"

FAIL_COUNT=0; WARN_COUNT=0; PASS_COUNT=0

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }
fail() { red    "  [FAIL] $*"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn() { yellow "  [WARN] $*"; WARN_COUNT=$((WARN_COUNT+1)); }
pass() { green  "  [PASS] $*"; PASS_COUNT=$((PASS_COUNT+1)); }

# ============================================================================
# 登记表  <source_key>::<signature> → <裁定>|<理由>
#
# 裁定三档：
#   KEEP   保留（用户知情）
#   REMOVE 建议去除（hook 本体改动须用户确认后才动，本卡只出建议不擅自改）
#   ACK    已人工核查的解析边界（UNANALYZABLE/UNREACHABLE 的显式认领）
#
# 签名形状（由 lib/scan_git_occurrences.py 产出）：
#   add:ALL        git add -A / . / --all / -u    覆盖整个工作树
#   add:path       git add <具体路径>              窄范围
#   commit         git commit …
#   push:<remote>  git push <remote> …
#   push:DEFAULT   git push（走默认上游）
#
# ⚠️ add:ALL 与 add:path 必须是**不同**签名。用单一 "git-add" 当签名会让
#    危险的全量 add 命中窄 add 的 KEEP 登记而放行。
#
# 未出现在本表中的任何签名 → 门 3 判 FAIL。
# ============================================================================
registry_lookup() {
  case "$1" in
    # ---- 主仓 Stop 链 · stop-auto-sync-to-remote.sh（全工作树自动同步）----
    "main-settings:auto-sync::add:ALL")\
      echo "REMOVE|git add -A 覆盖整个主仓工作树，射程含 869 条 tracked 删除 + 1139 个 untracked + 2.2GB 未被 .gitignore 排除的 archive/（git check-ignore 实测未命中）；脚本 Stage 7 仅 reset 掉 _backups/ 与 backend/mutants/" ;;
    "main-settings:auto-sync::commit")\
      echo "REMOVE|对上述全量 stage 结果自动 commit，message 由脚本合成，用户无审阅机会。此门在 git add -A **之后**，即便 lefthook pre-commit 拦下 commit，index 已被污染" ;;
    "main-settings:auto-sync::push:origin")\
      echo "REMOVE|--force-with-lease 推 origin wip/auto-sync；网络写，发生在用户未审阅的自动 commit 之后" ;;
    "main-settings:auto-sync::push:backup")\
      echo "REMOVE|--force-with-lease 推 backup wip/auto-sync；同上" ;;

    # ---- 主仓 / worktree lefthook.yml ----
    "main-lefthook::add:path")\
      echo "KEEP|pre-commit spec-sync 只在 backend/app/{api,models,schemas} 变更时把重新导出的 openapi.json 补进本次提交；窄范围、幂等、属既定 spec 同步需求" ;;
    "wt-lefthook::add:path")\
      echo "KEEP|同上（worktree 版）" ;;
    "main-lefthook::push:backup")\
      echo "KEEP|post-commit backup-push（--no-verify，archive 语义永不丢工作）；MEMORY feedback_auto_backup_push 载明为用户既定需求" ;;
    "main-lefthook::push:origin")\
      echo "KEEP|post-commit origin-push（canonical 语义，触发 pre-push 测试）。⚠️ 本项在 worktree 版 lefthook.yml 已被移除，两份配置已分叉——处置见 CARD-DEBT-14" ;;

    # ---- LaunchAgents ----
    "launch-agents:ai.openclaw.daily-brief::add:ALL")\
      echo "KEEP|作用域是 \$WS=~/.openclaw/workspace（**非 canvas 仓**，实测 oc-daily-brief.sh:27），用途是防 memory 文件被误删的本地快照；**无任何 push**（实测该脚本 git push 计数=0），不产生网络写" ;;
    "launch-agents:ai.openclaw.daily-brief::commit")\
      echo "KEEP|同上，本地快照 commit，无 push" ;;

    # ---- 已人工核查的解析边界（ACK）----
    #
    # ⚠️ ACK 的含义与局限（Codex round-2 M-02 整改后的准确表述）：
    #    它**不是**「该来源没有 git 写」的授权——main-lefthook / wt-lefthook /
    #    daily-brief 三者都确有 git 写，且已各自以 KEEP 单独登记。
    #    ACK 只认领「该来源里**这一类**静态分析读不动的构造」，
    #    并附上人工核查时看到的具体内容。
    #
    #    残留风险（未解决，见台账 §3.5 与裁决点 U6）：ACK 按
    #    `<source>::<边界类型>` 登记，不绑定行号与命令指纹。同一来源日后
    #    **新增**另一条读不动的命令，会被同一条 ACK 覆盖而不报警。
    #    round-2 已实测到这个风险的第一次真实发作：lefthook 的
    #    `extends -> rogue-extend.yml` 曾被「动态 pathspec」那条 ACK 放行，
    #    故 extends/remotes 已改用独立签名后缀 UNANALYZABLE:EXTERNAL_CONFIG，
    #    不再共用。
    #
    # ⛔ EXTERNAL_CONFIG 一律不给 ACK：lefthook 的 extends/remotes 会把
    #    仓外配置合并进来，静态扫描根本看不到那部分内容，必须 FAIL。

    "main-lefthook::UNANALYZABLE")\
      echo "ACK|lefthook.yml:32 for 循环内的 git add \"\$schema\"（动态 pathspec）。人工核查：循环体遍历 specs/data/generated/*.schema.json，与同文件 L26 的 add:path 同源同窄" ;;
    "wt-lefthook::UNANALYZABLE")\
      echo "ACK|同上（worktree 版 lefthook.yml:32）" ;;

    "main-settings:post-tool-router::UNANALYZABLE")\
      echo "ACK|post-tool-router.sh 的 \$PROJECT_ROOT/.venv/bin/activate 一类动态 source 路径。人工核查：全文 git add/commit/push 计数 = 0" ;;
    "main-settings:pytest::UNREACHABLE")\
      echo "ACK|REF 解析到 pytest——那是 PATH 上的可执行名而非仓内脚本路径，非缺失文件" ;;

    "launch-agents:ai.openclaw.checkin-ask::UNANALYZABLE")\
      echo "ACK|oc-checkin-ask.sh 内嵌 python3 -c heredoc 与中文多行 PROMPT，shell 词法无法闭合。人工核查：全文 git add/commit/push 计数 = 0" ;;
    "launch-agents:ai.openclaw.checkin-failsafe::UNANALYZABLE")\
      echo "ACK|同上形态（内嵌 python3 -c）。人工核查：git 写计数 = 0" ;;
    "launch-agents:ai.openclaw.daily-brief::UNANALYZABLE")\
      echo "ACK|同一脚本内的 python3 -c heredoc 与 \$NVM_DIR/nvm.sh 动态 source。该脚本**确有** git 写，但已由上方两条 KEEP（add:ALL / commit）逐条显式登记，本 ACK 只认领读不动的那部分" ;;
    "launch-agents:<<PY::UNREACHABLE")\
      echo "ACK|REF 解析到 heredoc 起始标记 <<PY 而非真实路径，是解析假象非缺失文件" ;;

    "launch-agents:com.google.GoogleUpdater.wake::UNANALYZABLE")\
      echo "ACK|第三方二进制（GoogleUpdater.app 可执行体），静态分析读不了。人工核查：plist argv 四项均不含 git，与本仓无关" ;;
    "launch-agents:com.valvesoftware.steamclean::UNANALYZABLE")\
      echo "ACK|第三方二进制（Steam steamclean），argv 不含 git，与本仓无关" ;;
    "launch-agents:homebrew.mxcl.ollama::UNANALYZABLE")\
      echo "ACK|第三方二进制（ollama serve），argv 不含 git，与本仓无关" ;;

    "plugin-hooks:claude-security:banner_hook::UNANALYZABLE")\
      echo "ACK|banner_hook.sh 的 \$(dirname -- \$0)/banner_notice.py 动态路径。人工核查：该脚本 git 写计数 = 0" ;;
    "plugin-hooks:ralph-loop:hook::UNANALYZABLE")\
      echo "ACK|stop-hook.sh:133 是 perl 正则字面量被误识别为路径。人工核查：该脚本 git 写计数 = 0" ;;
    "plugin-hooks:6.3.0:%HOOK_DIR%%~1::UNREACHABLE")\
      echo "ACK|%HOOK_DIR%%~1 是 Windows 批处理变量语法（superpowers run-hook.cmd），非 POSIX 路径；该 .cmd 在 macOS 不执行，且全文无 git 写" ;;

    *) return 1 ;;
  esac
}

# ============================================================================
# 来源定义（判据 b）
# ============================================================================
SOURCES=(
  "main-settings|${MAIN_REPO}/.claude/settings.json|file|主仓 Claude Code hooks"
  "main-settings-local|${MAIN_REPO}/.claude/settings.local.json|file|主仓 Claude Code 本地覆盖"
  "wt-settings|${WT_REPO}/.claude/settings.json|file|worktree Claude Code hooks"
  "wt-settings-local|${WT_REPO}/.claude/settings.local.json|file|worktree Claude Code 本地覆盖"
  "global-settings|${HOME_DIR}/.claude/settings.json|file|全局 Claude Code hooks"
  "main-lefthook|${MAIN_REPO}/lefthook.yml|file|主仓 lefthook"
  "wt-lefthook|${WT_REPO}/lefthook.yml|file|worktree lefthook"
  "git-hooks|${MAIN_REPO}|gitrepo|共享 .git/hooks（按 git rev-parse --git-path hooks 实际解析）"
  "launch-agents|${HOME_DIR}/Library/LaunchAgents|dir|用户级 LaunchAgents"
  "plugin-hooks|${HOME_DIR}/.claude/plugins|dir|Claude Code 插件提供的 hooks"
)

collect_signatures() {
  python3 "$COLLECTOR" "main=${MAIN_REPO}" "wt=${WT_REPO}" "home=${HOME_DIR}" 2>/dev/null
}

# ============================================================================
gate_1_lock_sentinel() {
  echo "── 门 1 · auto-sync 锁哨兵（禁清理僵尸锁）────────────────────────"
  if [ -d "$LOCK_DIR" ]; then
    local mtime
    mtime="$(stat -f '%Sm' "$LOCK_DIR" 2>/dev/null || stat -c '%y' "$LOCK_DIR" 2>/dev/null)"
    pass "锁目录存在：${LOCK_DIR}（持锁自 ${mtime}）"
    echo "         ↳ 它挡住主仓 Stop hook 的 git add -A + commit + push 全工作树。禁止清理。"
  else
    fail "锁目录已消失：${LOCK_DIR}"
    echo "         ⛔ 主仓 Stop hook 的 auto-sync 闸门已解除！下一次主仓 session 的 Stop"
    echo "            事件会对整个工作树执行 git add -A + commit + push。"
    echo "            恢复方式（立即执行）：mkdir -p \"${LOCK_DIR}\""
  fi
  echo
}

gate_2_source_reachability() {
  echo "── 门 2 · 来源可达性（防「文件没了⇒扫不到⇒假 PASS」）────────────"
  local src key path typ desc hd
  for src in "${SOURCES[@]}"; do
    IFS='|' read -r key path typ desc <<< "$src"
    case "$typ" in
      dir)
        if [ -d "$path" ]; then pass "${key} → ${path}"
        else fail "${key} 目录缺失 → ${path}（${desc}）"; fi ;;
      gitrepo)
        hd="$(git -C "$path" rev-parse --git-path hooks 2>/dev/null)"
        if [ -n "$hd" ]; then
          [[ "$hd" = /* ]] || hd="${path}/${hd}"
          if [ -d "$hd" ]; then pass "${key} → ${hd}（实际解析，非硬编码）"
          else fail "${key} hooks 目录不存在 → ${hd}"; fi
        else fail "${key} 无法解析 hooks 路径 → ${path}"; fi ;;
      *)
        if [ -f "$path" ]; then pass "${key} → ${path}"
        else fail "${key} 文件缺失 → ${path}（${desc}）"; fi ;;
    esac
  done
  echo
}

gate_3_write_registry() {
  echo "── 门 3 · git 写副作用登记核对（fail-closed）─────────────────────"
  local sig loc entry verdict reason seen="" found=0
  while IFS=$'\t' read -r sig loc; do
    [ -z "$sig" ] && continue
    case "$sig" in *"__INFO_PATH__") continue ;; esac
    found=1
    case " $seen " in *" $sig "*) continue ;; esac
    seen="$seen $sig"
    if entry="$(registry_lookup "$sig")"; then
      verdict="${entry%%|*}"; reason="${entry#*|}"
      case "$verdict" in
        KEEP)   pass "${sig}  →  保留（用户知情）" ;;
        REMOVE) warn "${sig}  →  建议去除（待用户确认）" ;;
        ACK)    pass "${sig}  →  已核查的解析边界（ACK）" ;;
      esac
      echo "         ${loc}"
      echo "         理由：${reason}"
    else
      case "${sig##*::}" in
        UNPARSEABLE)
          fail "${sig}  →  ⛔ hooks 配置无法解析"
          echo "         ${loc}"
          echo "         不得当作「没有写副作用」放行：解析失败时该来源的全部 hook 都看不见。" ;;
        UNREACHABLE)
          fail "${sig}  →  ⛔ 挂载目标不可达"
          echo "         ${loc}"
          echo "         不得当作「没有写副作用」放行：看不到内容就无从判断。" ;;
        UNANALYZABLE)
          fail "${sig}  →  ⛔ 命令无法静态解析"
          echo "         ${loc}"
          echo "         fail-closed：解析不了就不能假定它没写 git。人工核查后登记为 ACK。" ;;
        *)
          fail "${sig}  →  ⛔ 未登记的写副作用"
          echo "         ${loc}"
          echo "         处置：确认该 hook 是否应自动写 git。若属既定需求，把签名补进"
          echo "               registry_lookup() 并在台账登记裁定；否则移除该写操作。" ;;
      esac
    fi
  done < <(collect_signatures)
  [ "$found" = "0" ] && fail "未扫出任何签名——收集器可能失效（正常环境应至少扫出主仓 lefthook 的 add:path）"
  echo
}

emit_ledger() {
  echo "| 来源 | 签名 | 裁定 | 证据 |"
  echo "|---|---|---|---|"
  local sig loc entry verdict seen=""
  while IFS=$'\t' read -r sig loc; do
    [ -z "$sig" ] && continue
    case "$sig" in *"__INFO_PATH__") continue ;; esac
    case " $seen " in *" $sig "*) continue ;; esac
    seen="$seen $sig"
    if entry="$(registry_lookup "$sig")"; then
      case "${entry%%|*}" in
        KEEP)   verdict="保留（用户知情）" ;;
        REMOVE) verdict="**建议去除（待确认）**" ;;
        ACK)    verdict="已核查边界（ACK）" ;;
      esac
    else
      verdict="**未登记 → FAIL**"
    fi
    echo "| \`${sig%%::*}\` | \`${sig##*::}\` | ${verdict} | ${loc} |"
  done < <(collect_signatures)
}

main() {
  case "$MODE" in
    --list)        collect_signatures | sort -u; exit 0 ;;
    --emit-ledger) emit_ledger; exit 0 ;;
  esac

  echo "════════════════════════════════════════════════════════════════"
  echo " DEBT-15 · hook 写副作用断言"
  echo " 主仓：${MAIN_REPO}"
  echo " 工作树：${WT_REPO}"
  echo "════════════════════════════════════════════════════════════════"
  echo
  gate_1_lock_sentinel
  gate_2_source_reachability
  gate_3_write_registry
  echo "════════════════════════════════════════════════════════════════"
  printf ' 结果：PASS=%d  WARN=%d  FAIL=%d\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
  echo "════════════════════════════════════════════════════════════════"

  # ⚠️ 三态而非二态（Codex round-2 M-01）：
  #    旧版在 FAIL=0 时一律打印「全门通过」，哪怕登记表里还挂着 4 条
  #    REMOVE（主仓 Stop 链的 add:ALL/commit/push×2 依然在位）。
  #    那读起来像「系统是安全的」，实际只是「现状与登记表吻合」。
  #    两者必须分开说。
  if [ "$FAIL_COUNT" -gt 0 ]; then
    red " [FAIL] 断言失败：存在未登记写副作用、无法解析的命令，或闸门失守。"
    exit 1
  fi
  if [ "$WARN_COUNT" -gt 0 ]; then
    yellow " [KNOWN_UNSAFE] 登记吻合，但仍有 ${WARN_COUNT} 条**已知危险写链在位**（裁定为「建议去除」，待用户确认）。"
    echo "                这**不等于安全**——它只说明现状与登记表一致，没有出现新的未登记写。"
    echo "                在这些写链被移除前，~/.claude/auto-sync.lock.d 仍是主要防线。"
    exit 0
  fi
  green " [SAFE] 登记吻合，且无「建议去除」项在位。"
  exit 0
}

main
