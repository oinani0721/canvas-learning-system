#!/usr/bin/env bash
# Canvas Learning System — 部署单元 =（vault, 后端实例）一键部署
# CARD-G2-7b [BATCH-2026-09-07-第十三批]。决策页 §一「部署单元」+ §五 六步。
#
# ═══ 六步 ═══
#   [1/6] preflight   — harness 树完整性 / 禁写面 / vault 名不动点 / 端口 / skills / main.js
#   [2/6] install     — 调 <harness>/scripts/install-vault.sh（不加 --activate）
#   [3/6] postprocess — 密钥按实例重生（E-3）/ .env.<vault> / 端口模板化 / 在位判
#   [4/6] verify      — 调 verify_vault_install.py，rc 必须 0
#   [5/6] activate    — 只 `docker compose config` 断言；`up -d` 需用户授权（G2-8）
#   [6/6] evidence    — 落 deploy-<ts>.txt（六行状态 + 参数 + 各文件 sha；密钥只 sha）
#                       dry-run 下 SKIP 不落盘 —— 「不传 --apply = 零写」优先于留证据。
#
# ═══ rc 表 ═══
#   0  成功
#   64 用法错（缺必填 / 未知参数 / --hosts 含二线宿主 / --activate 缺 --apply / --also-push 越界）
#   71 步 1 preflight 失败      74 步 4 verify 失败
#   72 步 2 install 失败        75 步 5 activate 失败
#   73 步 3 postprocess 失败    76 步 6 evidence 失败
#
# ═══ 参数全表 ═══
#   --vault <绝对路径>    必填。目标 vault 目录；basename = vault 名。
#   --harness <树路径>    缺省：`docker compose ls --format json` 恰 1 个 running 项目时取其
#                         ConfigFiles 所在目录；0 个或 ≥2 个 → rc 64（请显式传）。
#   --port <n>            缺省 8011（与 vault 内全部消费方同源：.mcp.json / settings.json hook /
#                         session-end-archive.py / 插件 data.json；compose :150 缺省是 8001，
#                         .env.example:84 是 8011 —— 不一致已登记，本脚本按 8011 选边）。
#   --hosts <list>        缺省 claude。本版**只**支持 claude；其余值 rc 64（E-1）。
#   --subject <s>         缺省 = vault 名。
#   --apply               不传 = dry-run（只打印每步将做什么，零写）。
#   --activate            仅与 --apply 同用（否则 rc 64）。真 `up -d` 需用户授权，见步 5。
#   --also-push           仅当 harness == feature 主干树时允许；本版**只解析不实现**（登记 G2-8）。
#   --evidence-dir <dir>  缺省 <harness>/_bmad-output/审查/evidence-deploy-<vault名>/
#   --env-dir <dir>       缺省 <harness>/ 。`.env.<vault名>` 的落点目录。
#
# ═══ 禁写面 ═══
#   判据本体在 **scripts/cls_forbidden_paths.py**（该文件头有完整规则与依据）。
#   ⚠️ 判定**不在 bash 里做**（Codex r2 BLOCKER-1）：`cd -L`+`pwd -P`、字符串折叠 `..`、
#   大小写归一这三种解释全在词法/逻辑层面，没有一种能回答「mkdir -p 最终写到哪个 inode」——
#   `/safe/link/../probe`（link → $HOME/.codex/sub）的物理落点是 `.codex/probe`，
#   而三条解释一致地得出 `/safe/probe`。改用 os.path.realpath（**先解链再折叠**）。
#
#   保护目标：live vault（$CLS_LIVE_VAULT）/ $HOME/Library / $HOME/.codex / .pi / .gemini
#   / .deepcode / .dsh / $HOME/.config/opencode；路径中任何名为 .git 的段；
#   `$HOME/.claude*` = **已存在条目的解析结果（含软链目标）+ HOME 下词法前缀，两条并存**。
#   全部在「物理路径 + 大小写归一」后的键上比较。
#
#   两类对象（Codex r2 BLOCKER-4）：
#     · strict  — 三个路径参数 --vault / --evidence-dir / --env-dir，含「自身是 *.env」规则
#     · outputs — 脚本自己的产出（.env.<vault> 与 .tmp / key 与 .tmp / 插件 data.json /
#                 build 落点），**跳过 env 文件名规则**（否则脚本会永远拦下自己的正常产出），
#                 其余规则一分不放
#   另：已存在的产出对象若本身是**软链**，直接拒（写入会沿链穿到别处）。
#
# ═══ 环境开关 ═══
#   CLS_MIN_SKILLS            preflight 要求的「含 SKILL.md 的 skill 目录数」下限，缺省 9。
#                             ⚠️ 现状恰 9 = 零余量：退役任一 skill 会让本判据 FAIL 71，而
#                             install-vault.sh:188 的 ≥8 仍绿 —— 两条判据会给出相反结论，
#                             退役 skill 时必须同步改两处。
#   CLS_DEPLOY_ALLOW_DOCKER_UP  **缺省 0 = 步 5 只跑 `config` 断言后 SKIP，不 `up -d`**。
#                             显式 =1 才真起容器（顶替现网容器不可逆 ⇒ opt-in，需用户当次授权）。
#   CLS_LIVE_VAULT            live vault 绝对路径（禁写面第一条），缺省为主仓 canvas-vault。
#   CLS_NPM_BUILD_TIMEOUT     步 1 `npm run build` 的**墙钟上限**（整数秒，取值 1..86400；
#                             含前导零在内**原串最多 20 位** —— Codex r3 LOW-3），
#                             缺省 300。到点对 npm 所在进程组 TERM→（2s）→KILL，步 1 以
#                             FAIL 71 + 超时专属文案返回，而不是无限挂起（集成期裁定 R-15：
#                             候选树跑 tests/unit 时真跑本脚本的用例逐个卡死，挂点就是这条
#                             原先没有上限的 build）。
#                             缺省 300 的依据：裁判侧兜底上限是 600（单测 _SUBPROCESS_TIMEOUT），
#                             脚本取其一半，**通常**脚本自己的超时文案会先于裁判超时出现，
#                             用户看到的是「哪一步超时」而不是一个无解释的挂死。
#                             ⚠️ 这只是「通常」不是保证：alarm 只覆盖 build 本身（步 1 前面的
#                             判据另计时），到点后还有 2s 清理宽限，且把本值调到 >600 时顺序
#                             必然反过来（Codex r1 LOW-2）。
#                             ⚠️ `0` 在 Perl 里就是**取消闹钟**；超 uint32 的值被**截断**
#                             （4294967296 → 0 = 取消，4294967297 → 1 秒），都不是你写的那个数
#                             ⇒ 一律显式拒绝（Codex r1 HIGH-1 / r2 LOW-3）。要「不设上限」
#                             请直接调大（上限 86400），不要写 0。取值只认 ASCII 十进制数字，
#                             逐字符枚举、与 locale 无关（`LC_ALL=ar_EG.UTF-8` 下的阿拉伯数字
#                             曾能过区间写法的门并最终变成 alarm 0 —— Codex r2 HIGH-1）。
#                             ⚠️ 本机无 timeout(1)/gtimeout ⇒ 用 perl 的 alarm 实现（走 PATH，
#                             本机实测解析到 /usr/bin/perl）。
#                             ⚠️ 若 build 的后代自己 `setsid()` 另开 session（如 Node 的
#                             `detached: true`），它会脱离被杀的进程组而继续运行。本上限保证的是
#                             **这条 build 不会无限等下去**，既不是「进程树一定清空」
#                             （Codex r1 MEDIUM-1），也不是「步 1 整体一定按时返回」——
#                             build 之后的 mkdir/cp 若卡在文件系统上，闹钟已经取消（r2 LOW-3）。
#   CLS_NPM_BUILD_OFFLINE     步 1 build 的 npm_config_offline 值，缺省 true：让 **npm 自己的
#                             取包路径**只用本地缓存、缓存缺失即快速失败。需要联网构建时显式 =false。
#                             ⚠️ 它**不是**网络隔离：`npm run build` 跑的是 package.json 里的脚本，
#                             那些脚本自己发的请求（curl / fetch / 下载 binary）不受此开关约束，
#                             真正兜住它们的是上面的墙钟上限（Codex r1 LOW-1）。
#
# ⚠️ set -e 与分步返回码的交互（Codex 问题 ②）：每个 stepN 函数都在 `|| rc=$?` 的条件
#    上下文里被调用，因此**函数体内 set -e 被抑制**——中间命令失败不会中止函数。所以函数
#    体内每一条判据都显式检查并 `return 1`，不依赖 set -e。SKIP 用 return 2，与 OK(0) /
#    FAIL(1) 三态分开，绝不让「某步没跑」被读成「跑过且通过」。
set -euo pipefail

CLS_MIN_SKILLS="${CLS_MIN_SKILLS:-9}"
# ⛔ 闸门方向（Codex r1 HIGH-2）：`up -d` 顶替现网容器 = 不可逆, 故**默认不做**。
#    旧的 CLS_DEPLOY_NO_DOCKER_UP 缺省 0 意味着「不设开关就真起容器」, 而「需用户授权」
#    只写在注释里、没有执行闸门。现在改成 opt-in：必须显式 =1 才会 up。
CLS_DEPLOY_ALLOW_DOCKER_UP="${CLS_DEPLOY_ALLOW_DOCKER_UP:-0}"
CLS_LIVE_VAULT="${CLS_LIVE_VAULT:-/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault}"
# 步 1 npm build 的墙钟上限与离线开关（CARD-DEPLOY-TIMEOUT / R-15，依据见头注 环境开关）
CLS_NPM_BUILD_TIMEOUT="${CLS_NPM_BUILD_TIMEOUT:-300}"
CLS_NPM_BUILD_OFFLINE="${CLS_NPM_BUILD_OFFLINE:-true}"
FEATURE_TREE="/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev"

VAULT=""
HARNESS=""
PORT="8011"
HOSTS="claude"
SUBJECT=""
APPLY=0
ACTIVATE=0
ALSO_PUSH=0
EVIDENCE_DIR=""
ENV_DIR=""
STEP_MSG=""
declare -a STEP_LINES=()

usage() {
    # 打第 2 行到**第一个非 # 开头的行**为止, 再删掉那一行 —— 对头注行数漂移免疫,
    # 不写死行号（写死会在头注增删时把代码打进 --help, 或把参数表截断）。
    sed -n '2,/^[^#]/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}

die64() {
    printf '❌ 用法错: %s\n' "$1" >&2
    printf '   `%s --help` 看六步与 rc 表。\n' "$(basename "$0")" >&2
    exit 64
}

# ── 脱敏过滤器：任何要落盘的渲染结果都必须过它 ─────────────────────────────────
# `docker compose config` 把 --env-file 与**宿主 env**里的凭据展开成明文
# （INTERNAL_API_KEY / GOOGLE_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY /
#  ANTHROPIC_API_KEY / NEO4J_PASSWORD / NEO4J_AUTH …）。evidence 是要入库的,
# 所以明文**不许落盘**。按键名而非值的形态匹配 —— 按值的形态（如 AIzaSy 前缀）
# 匹配等于要穷举所有厂商的 key 格式, 漏一种就泄一种。
# NEO4J_AUTH 是 user/password 复合值, 整值一起换掉。
redact_secrets() {
    sed -E \
        -e 's/^([[:space:]]*[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|CREDENTIAL)[A-Za-z0-9_]*:[[:space:]]*).*/\1<redacted>/' \
        -e 's/^([[:space:]]*-?[[:space:]]*[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|CREDENTIAL)[A-Za-z0-9_]*=).*/\1<redacted>/'
}

# ── 路径解析：对可能不存在的路径取最近存在祖先的物理路径 + 剩余段 ──────────────
# 不用 `realpath <缺失路径>`（BSD realpath 对缺失路径行为不一，返回空会让检查静默跳过）。
resolve_abs() {
    local p="$1" rest="" base dir
    case "$p" in
        "~") p="$HOME" ;;
        "~/"*) p="$HOME/${p#\~/}" ;;
    esac
    case "$p" in
        /*) ;;
        *) p="$PWD/$p" ;;
    esac
    while [ ! -e "$p" ]; do
        base="$(basename "$p")"
        dir="$(dirname "$p")"
        [ "$dir" = "$p" ] && break
        rest="/$base$rest"
        p="$dir"
    done
    if [ -d "$p" ]; then
        p="$(cd "$p" 2>/dev/null && pwd -P)" || p="$1"
    elif [ -e "$p" ]; then
        dir="$(cd "$(dirname "$p")" 2>/dev/null && pwd -P)" || dir="$(dirname "$p")"
        p="$dir/$(basename "$p")"
    fi
    printf '%s%s' "$p" "$rest"
}

# ── 禁写面判据 ────────────────────────────────────────────────────────────────
# ⛔ 判定**不在 bash 里做**（Codex r2 BLOCKER-1）：`cd -L`、字符串折叠 `..`、大小写归一
#    这三种解释全是词法/逻辑层面的，没有一种能回答「mkdir -p 最终写到哪个 inode」。
#    一个反例就让三条同时错到同一个错答案：
#        /safe/link/../probe   link → $HOME/.codex/sub
#        物理落点 = $HOME/.codex/probe  （`..` 是 link **目标**的父目录）
#        三种解释一致地得出 /safe/probe ⇒ 一致地漏拦
#    另有：命令替换剥掉末尾换行、`set -- $p` 会做**通配符展开**、字面 `~` 只有判据展开。
#    故整套判据搬到 scripts/cls_forbidden_paths.py，用 os.path.realpath（**先解链再折叠**）。
# ⛔ 禁字节码缓存（Codex r8 HIGH-2）：下面几处 `import cls_forbidden_paths` 会写
#    `scripts/__pycache__/*.pyc`, 而这次写入发生在 `open_pinned` 检查**之前**、
#    也不在 preflight 的待写清单里。若 `__pycache__` 指向保护目录就是一次未受检写入。
export PYTHONDONTWRITEBYTECODE=1
FORBID_PY="$(dirname "$0")/cls_forbidden_paths.py"

# 一次判**全部**待写对象（Codex r2 BLOCKER-4：三个参数过检 ≠ 实际写入对象过检）。
# 传入的不只是三个目录参数, 还有脚本真正会写的每个文件路径。
FORBIDDEN_HIT=""
check_forbidden_paths() {
    local out rc=0
    if [ ! -f "$FORBID_PY" ]; then
        FORBIDDEN_HIT="判据脚本缺失: $FORBID_PY"
        return 0
    fi
    out="$(python3 "$FORBID_PY" "$CLS_LIVE_VAULT" "$@" 2>&1)" || rc=$?
    if [ "$rc" = 64 ]; then
        FORBIDDEN_HIT="判据脚本用法错: $out"
        return 0
    fi
    if [ "$rc" != 0 ]; then
        FORBIDDEN_HIT="$(printf '%s\n' "$out" | grep '^HIT ' | head -1 | sed 's/^HIT //')"
        [ -n "$FORBIDDEN_HIT" ] || FORBIDDEN_HIT="判据脚本 rc=${rc}: $out"
        return 0
    fi
    FORBIDDEN_HIT=""
    return 1
}

# ── 权限收紧：一律走 pinned fd（Codex r7 HIGH-1 同族）────────────────
# 路径式 `chmod` 每次重新解析路径, 末段/祖先被换成软链时会改到**别人**的权限。
# chmod_pinned 见 cls_forbidden_paths：解析后当场过判据 + 逐级 O_NOFOLLOW + fchmod。
pinned_chmod600() {
    python3 - "$1" "$(dirname "$FORBID_PY")" "$CLS_LIVE_VAULT" << 'PYCHMOD'
import os, sys
sys.path.insert(0, sys.argv[2])
from cls_forbidden_paths import chmod_pinned
chmod_pinned(sys.argv[1], 0o600, live_vault=sys.argv[3])
PYCHMOD
}

WRITE_GUARD_ERR=""
# 写入**紧邻**前的复查（Codex r4 BLOCKER-4 + HIGH-1）：
#   ① 硬链接：`.env.<vault>.tmp` 与保护区文件共享 inode 时, realpath 得到的是合法路径、
#      `-L` 为假 —— 但 `: >` 截断改的是那个**共享 inode**。路径判据看不见 inode, 只能看链接数。
#   ② preflight 与真正打开之间存在时间窗, 期间对象可能被换成软链/硬链。
# ⚠️ 如实声明：bash 重定向做不到 open(O_NOFOLLOW) 的原子性, 这里只把窗口收到**最窄**,
#    残留窗口不为零（两处 python 写入已改用 O_NOFOLLOW, 那两处是真原子）。
assert_writable_now() {
    local p="$1" nlink=""
    WRITE_GUARD_ERR=""
    if [ -L "$p" ]; then
        WRITE_GUARD_ERR="写入前复查: 对象是软链, 写入会沿链穿到别处: $p -> $(readlink "$p")"
        return 1
    fi
    [ -e "$p" ] || return 0
    [ -d "$p" ] && return 0
    # 用 python3 取 st_nlink：`stat` 的 BSD/GNU 口径不同（GNU 的 `-f` 是**文件系统**信息,
    # `%l` 在那边是「文件名最大长度」—— 会回一个看似合理的数字, 比报错更坏）。
    nlink="$(python3 -c 'import os,sys
try:
    print(os.lstat(sys.argv[1]).st_nlink)
except OSError:
    pass' "$p" 2> /dev/null)"
    # 三态：数字 / 空 / 非数字。**非数字不能落到 `[ -gt ]`** —— 那会 rc=2、`if` 判假 ⇒
    # 静默 fail-open（该拦的放行了）。空与非数字一律 fail-closed。
    case "$nlink" in
        '' | *[!0-9]*)
            WRITE_GUARD_ERR="写入前复查: 问不出链接数(得到 '${nlink}'), 无从断言不是硬链接: $p"
            return 1
            ;;
    esac
    if [ "$nlink" -gt 1 ]; then
        WRITE_GUARD_ERR="写入前复查: 对象有 ${nlink} 个硬链接, 写入会改共享 inode: $p"
        return 1
    fi
    return 0
}

# ── 参数解析 ──────────────────────────────────────────────────────────────────
[ $# -eq 0 ] && { usage; exit 64; }
while [ $# -gt 0 ]; do
    case "$1" in
        --help | -h) usage; exit 0 ;;
        --vault) [ $# -ge 2 ] || die64 "--vault 缺值"; VAULT="$2"; shift 2 ;;
        --harness) [ $# -ge 2 ] || die64 "--harness 缺值"; HARNESS="$2"; shift 2 ;;
        --port) [ $# -ge 2 ] || die64 "--port 缺值"; PORT="$2"; shift 2 ;;
        --hosts) [ $# -ge 2 ] || die64 "--hosts 缺值"; HOSTS="$2"; shift 2 ;;
        --subject) [ $# -ge 2 ] || die64 "--subject 缺值"; SUBJECT="$2"; shift 2 ;;
        --apply) APPLY=1; shift ;;
        --activate) ACTIVATE=1; shift ;;
        --also-push) ALSO_PUSH=1; shift ;;
        --evidence-dir) [ $# -ge 2 ] || die64 "--evidence-dir 缺值"; EVIDENCE_DIR="$2"; shift 2 ;;
        --env-dir) [ $# -ge 2 ] || die64 "--env-dir 缺值"; ENV_DIR="$2"; shift 2 ;;
        *) die64 "未知参数: $1" ;;
    esac
done

[ -n "$VAULT" ] || die64 "缺 --vault <绝对路径>"
# ⛔ 必须是绝对路径（Codex r5 HIGH-2）：相对 `--vault` 会让 VAULTS_ROOT 的**解析基准分裂** ——
#    `--vault course` ⇒ VAULT_PARENT="." ⇒ installer 按**调用 cwd** 解释这个 `.`,
#    而写进 `.env.<vault>` 的 `VAULTS_ROOT=.` 由 compose 按 `--project-directory "$HARNESS"`
#    解释（compose `:218` 的 `"${VAULTS_ROOT:-.}:/vaults:…"`）。从非 harness 目录部署
#    ⇒ 库建在 cwd、容器却挂 harness, 而步 5 的 config 断言只验容器名与端口, **抓不到**。
#    头注 `:22` 本就写「必填绝对路径」, 此前只判非空 = 文档与实现不一致, 这里补上强制。
case "$VAULT" in
    /*) ;;
    *) die64 "--vault 必须是绝对路径（收到 '$VAULT'）: 相对路径会让 installer 按调用 cwd、compose 按 --project-directory 解释同一个 VAULTS_ROOT" ;;
esac
case "$PORT" in
    '' | *[!0-9]*) die64 "--port 必须是数字: $PORT" ;;
esac
[ "$ACTIVATE" = 1 ] && [ "$APPLY" != 1 ] && die64 "--activate 只能与 --apply 同用"

# --hosts：本版只 claude（E-1）
# ⛔ 不用 here-string（Codex r9 HIGH-1）：Bash 3.2（本机 /bin/bash）对 `<<<` 会在
#    `$TMPDIR` **建一个临时文件**。这一行在 preflight **之前**、dry-run 也会走到 ——
#    `TMPDIR` 若指向保护目录, 那就是一次先于任何判据的写入, 事后删除撤不回。
#    步 4 的 TMPDIR 检查（只覆盖非 8011 的镜像分支）来得太晚。
#    改成纯参数展开切分：零子进程、零临时文件。
_rest="$HOSTS"
while [ -n "$_rest" ]; do
    _h="${_rest%%,*}"
    if [ "$_h" = "$_rest" ]; then _rest=""; else _rest="${_rest#*,}"; fi
    # ⛔ 恢复旧 `tr -d '[:space:]'` 的语义（Codex r11 LOW-1）：它删的是**全部位置**的
    #    **所有** ASCII 空白（含 \v \f \r 与**中间**空白, `cl au\tde` → `claude`）。
    #    我 r9 只剥首尾空格、r10 改成不动点循环仍只剥首尾 —— 两版都不等价。
    #    bash 的模式替换 `${var//[类]/}` 一次删净, 零 fork、线性时间,
    #    顺带解决 r10 LOW-2 的二次复杂度。
    _h="${_h//[$' \t\n\r\v\f']/}"
    [ -n "$_h" ] || continue
    if [ "$_h" != "claude" ]; then
        printf '❌ 用法错: --hosts 含未实现的宿主 %s。\n' "$_h" >&2
        printf '   E-1 二线宿主（codex / opencode / dsh 等）等 HOST-PROBE 实测表（U4-A），本版不实现。\n' >&2
        exit 64
    fi
done

# --harness 缺省推断
if [ -z "$HARNESS" ]; then
    _n=0
    _cfg=""
    if command -v docker > /dev/null 2>&1; then
        _json="$(docker compose ls --format json 2>/dev/null || printf '[]')"
        # Codex r1 MEDIUM-2 两处收紧：
        #   ① Status 前缀匹配改**大小写不敏感**（`Running(1)` 之前会被漏掉 ⇒ 明明有一个
        #      在跑却报「0 个」并 rc 64，行为随 docker 输出大小写摇摆）
        #   ② ConfigFiles 含多份（base + override，逗号分隔）时**拒绝推断**而不是取第一份 ——
        #      取第一份等于静默丢掉 override 上下文，后续所有步骤都用错的 compose
        _n="$(printf '%s' "$_json" | python3 -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d=[]
print(len([p for p in d if str(p.get("Status","")).lower().startswith("running")]))' 2>/dev/null || printf '0')"
        _cfg="$(printf '%s' "$_json" | python3 -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d=[]
r=[p for p in d if str(p.get("Status","")).lower().startswith("running")]
print(r[0].get("ConfigFiles","") if len(r)==1 else "")' 2>/dev/null || printf '')"
    fi
    if [ "$_n" = "1" ] && [ -n "$_cfg" ]; then
        case "$_cfg" in
            *,*)
                die64 "--harness 无法推断：该项目有多份 compose 配置（${_cfg}）。取第一份会静默丢掉 override，请显式 --harness <树绝对路径>"
                ;;
        esac
        HARNESS="$(cd "$(dirname "$_cfg")" && pwd -P)" \
            || die64 "--harness 推断出的目录进不去: $(dirname "$_cfg")"
    else
        die64 "--harness 无法推断（running compose 项目数 = ${_n}，需恰 1）。请显式 --harness <树绝对路径>"
    fi
fi

# ⛔ 不用 $(basename)/$(dirname)（Codex r3 BLOCKER-4）：命令替换会**剥掉末尾换行**,
#    于是判据检查的是含 LF 的目录、而 installer 收到的是另一个目录 —— 若后者是指向
#    保护区的软链, 检查与实参就分裂了。bash 参数展开不经命令替换, 保真。
# ⛔ 参数展开要补齐 dirname/basename 的两个语义（Codex r4 MEDIUM-3，我 r3 换掉命令替换时
#    引入的回归）：① 单段相对路径 `course` ⇒ `${VAULT%/*}` 原样返回 `course`（dirname 给 `.`）
#    ② 尾斜杠 `/tmp/course/` ⇒ `${VAULT##*/}` 得**空** vault 名。
#    先剥尾部斜杠（保留根 `/`）, 再按有无 `/` 分支。仍不经命令替换（保末尾换行, r3 B-4）。
# ⚠️ ① 那一半自 r5 HIGH-2 起**由入口的绝对路径强制承担**（相对路径直接 rc 64, 到不了这里）;
#    ② 尾斜杠仍必须在这里处理 —— `--vault /tmp/course/` 是合法绝对路径, 不剥就得空 vault 名。
_v="$VAULT"
while [ "${_v%/}" != "$_v" ] && [ "$_v" != "/" ]; do _v="${_v%/}"; done
VAULT="$_v"
VAULT_NAME="${VAULT##*/}"
case "$VAULT" in
    */*) VAULT_PARENT="${VAULT%/*}"; [ -n "$VAULT_PARENT" ] || VAULT_PARENT="/" ;;
    # ⛔ 不留死代码（r4 的教训：不可达分支会让人以为有两道防线）。入口已保证 `/*`,
    #    所以「不含 `/`」只可能是上面的强制被改坏 —— 让它**出声**而不是静默给个 `.`。
    *) die64 "内部不变量破坏: --vault 已判绝对路径却不含 '/'（${VAULT}）" ;;
esac
[ -n "$VAULT_NAME" ] || die64 "--vault 解析不出 vault 名: $VAULT"
[ -n "$SUBJECT" ] || SUBJECT="$VAULT_NAME"
# ⛔ 基准固定（Codex r10 HIGH-1 后半 + r11 HIGH-1 收口）：相对目录会让**创建**与**使用**
#    分裂 —— npm 段先在调用 cwd 下 `mkdir -p`, 随后 `cd` 进插件目录再把**同一个相对串**
#    交给 npm ⇒ 两者落点不同。这里只做**词法**绝对化（不 realpath, 免得改变语义）。
# ⛔⛔ 顺序：绝对化必须在**默认值赋好之后**（r11 HIGH-1 —— 我 r10 放在了之前）。
#    `--harness .` + 省略 `--evidence-dir` 时, 默认值 `$HARNESS/_bmad-output/…` 是**之后**
#    才填进去的, 于是整条仍是相对串 ⇒ 绝对化白做。HARNESS 本身也要先绝对化, 否则
#    由它派生的两个默认值天然带相对前缀。
case "$HARNESS" in /*) ;; *) HARNESS="$PWD/$HARNESS" ;; esac
[ -n "$EVIDENCE_DIR" ] || EVIDENCE_DIR="$HARNESS/_bmad-output/审查/evidence-deploy-$VAULT_NAME"
[ -n "$ENV_DIR" ] || ENV_DIR="$HARNESS"
# 两个默认值都赋好了, 现在统一绝对化（显式传入的相对值也在这里被覆盖到）。
case "$EVIDENCE_DIR" in /*) ;; *) EVIDENCE_DIR="$PWD/$EVIDENCE_DIR" ;; esac
case "$ENV_DIR" in /*) ;; *) ENV_DIR="$PWD/$ENV_DIR" ;; esac
ENV_FILE="$ENV_DIR/.env.$VAULT_NAME"

if [ "$ALSO_PUSH" = 1 ]; then
    _hr="$(resolve_abs "$HARNESS")"
    _ft="$(resolve_abs "$FEATURE_TREE")"
    [ "$_hr" = "$_ft" ] || die64 "--also-push 只允许 harness == ${FEATURE_TREE}（实测 ${HARNESS}）"
fi

MODE="dry-run"
[ "$APPLY" = 1 ] && MODE="apply"
TS="$(date +%Y%m%dT%H%M%S)"

emit() { STEP_LINES+=("$1"); printf '%s\n' "$1"; }

run_step() {
    local n="$1" name="$2" fn="$3" rc=0
    STEP_MSG=""
    "$fn" || rc=$?
    case "$rc" in
        0) emit "[$n/6] $name: OK ${STEP_MSG:-—}" ;;
        2) emit "[$n/6] $name: SKIP ${STEP_MSG:-—}" ;;
        *)
            emit "[$n/6] $name: FAIL ${STEP_MSG:-未给原因}"
            exit $((70 + n))
            ;;
    esac
}

# ═══ 步 1 preflight ═════════════════════════════════════════════════════════
NEED_BUILD=0
step1_preflight() {
    local f missing=""
    for f in scripts/install-vault.sh scripts/verify_vault_install.py \
        scripts/vault-install-manifest.json docker-compose.yml; do
        [ -f "$HARNESS/$f" ] || missing="$missing $f"
    done
    [ -d "$HARNESS/canvas-vault/.claude/skills" ] || missing="$missing canvas-vault/.claude/skills"
    if [ -n "$missing" ]; then
        STEP_MSG="harness 树不完整, 缺:$missing"
        return 1
    fi

    # ⛔ 待写对象**单一清单**（Codex r4 HIGH-1）：原先「判据的 --outputs 列表」与「-L 列表」
    #    是两份手抄清单, **已经漂移** —— harness-mainjs / harness-build-out 只在判据列表里,
    #    这两个构建产物若是软链没有任何一层会拦。改成一个数组两个消费方, 结构上不可能再漂移。
    local -a PENDING_WRITES=(
        "env-file:$ENV_FILE"
        "env-file-tmp:$ENV_FILE.tmp"
        "key-file:$VAULT/.obsidian/cls-internal-key.txt"
        "key-file-tmp:$VAULT/.obsidian/cls-internal-key.txt.tmp"
        "plugin-data:$VAULT/.obsidian/plugins/canvas-learning-system/data.json"
        "harness-mainjs:$HARNESS/canvas-vault/.obsidian/plugins/canvas-learning-system/main.js"
        "harness-build-out:$HARNESS/frontend/obsidian-plugin/main.js"
        "ev-install-log:$EVIDENCE_DIR/install-$TS.txt"
        "ev-verify-report:$EVIDENCE_DIR/verify-$TS.txt"
        "ev-compose-config:$EVIDENCE_DIR/compose-config-$TS.txt"
        "ev-deploy-report:$EVIDENCE_DIR/deploy-$TS.txt"
        "ev-deploy-report-tmp:$EVIDENCE_DIR/deploy-$TS.txt.tmp"
        # ⛔ npm 缓存/日志目录（Codex r10 HIGH-1）：我 r9 为「约束 npm 写入面」新加的
        #    `mkdir -p "$EVIDENCE_DIR/npm-$TS/{cache,logs}"` **本身就是未过判据的写入面** ——
        #    evidence 下预置 `npm-$TS -> 保护目录` 时, 那个 mkdir 直接写进去,
        #    无需竞争窗口。为堵写入面而新开的写入面, 必须进同一份清单。
        "ev-npm-cache:$EVIDENCE_DIR/npm-$TS/cache"
        "ev-npm-logs:$EVIDENCE_DIR/npm-$TS/logs"
        # ⛔ TMPDIR（Codex r10 HIGH-2）：Bash 3.2 对 **here-document**（`<< '\''PY'\''`）
        #    同样在 `$TMPDIR` 建临时文件 —— 步 2 的 `pinned_chmod600`、步 3 两处 python 块
        #    都会触发。原来唯一的 TMPDIR 检查在步 4, **太晚**且缺省端口 8011 完全跳过。
        #    我 r9 删掉 `<<<` 只修好了 preflight **之前**那一条, 没闭合这一类。
        #    放进 preflight 清单 ⇒ 任何 heredoc 执行之前就判过（preflight 自身只用
        #    `python3 -c` 与带 argv 的调用, 无 heredoc）。
    )
    # ⛔ TMPDIR 单独判（Codex r11 MEDIUM-1 —— 我 r10 把它塞进 PENDING_WRITES 的回归）：
    #    它是「**写入其中**的目录」, 不是「本脚本创建/截断的叶子文件」。
    #    塞进同一份清单会让它过下面的 `-L` 软链规则, 而 macOS 的 `/tmp -> /private/tmp`
    #    是**合法**软链 ⇒ `TMPDIR=/tmp`（极常见, 未设时也回退到它）当场 rc 71, dry-run 同样中招。
    #    判据侧（realpath 物理解析）本来就能正确处理合法软链, 所以只走判据、不走叶子规则。
    local -a DIR_WRITES=("tmpdir:${TMPDIR:-/tmp}")

    # 三个路径参数 + **脚本真正会写的每个对象**（Codex r2 BLOCKER-4）
    if check_forbidden_paths \
        "--vault:$VAULT" \
        "--evidence-dir:$EVIDENCE_DIR" \
        "--env-dir:$ENV_DIR" \
        --outputs "${PENDING_WRITES[@]}" "${DIR_WRITES[@]}"; then
        STEP_MSG="禁写面: $FORBIDDEN_HIT"
        return 1
    fi
    # 已存在的待写对象若是**软链**, 写入会沿链穿到别处；若有**硬链接**, 截断会改共享 inode
    # （Codex r4 BLOCKER-4）。判据脚本只看路径, 这两条都得在这里补。含 .tmp（r3 BLOCKER-3）。
    local item lnk
    for item in "${PENDING_WRITES[@]}"; do
        lnk="${item#*:}"
        if [ -L "$lnk" ]; then
            STEP_MSG="待写对象是软链, 写入会沿链穿到别处: $lnk -> $(readlink "$lnk")"
            return 1
        fi
        assert_writable_now "$lnk" || { STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
    done

    # vault 名 = sanitize_vault_id 与 vault_key 的**共同不动点**（决策页 §二 G4 两套口径）
    local py="$HARNESS/backend/.venv/bin/python"
    if [ ! -x "$py" ]; then
        STEP_MSG="harness venv 缺: $py"
        return 1
    fi
    if ! "$py" -c '
import sys
sys.path.insert(0, sys.argv[2] + "/backend")
sys.path.insert(0, sys.argv[2] + "/scripts")
from app.config import sanitize_vault_id
from send_bark import vault_key
n = sys.argv[1]
s, v = sanitize_vault_id(n), vault_key(n)
if s != n or v != n:
    print(f"sanitize_vault_id={s!r} vault_key={v!r}", file=sys.stderr)
    sys.exit(1)
' "$VAULT_NAME" "$HARNESS" 2> /dev/null; then
        STEP_MSG="vault 名 '$VAULT_NAME' 不是 sanitize_vault_id/vault_key 的共同不动点（两套口径会分裂, 决策页 §二 G4）"
        return 1
    fi

    # 与 harness 已有 .env* 的 ACTIVE_VAULT 不碰撞（只读）
    local e
    for e in "$HARNESS"/.env "$HARNESS"/.env.*; do
        [ -f "$e" ] || continue
        local arc=0
        grep -qE "^ACTIVE_VAULT=[\"']?${VAULT_NAME}[\"']?[[:space:]]*$" "$e" 2> /dev/null || arc=$?
        case "$arc" in
            0) STEP_MSG="vault 名与 $(basename "$e") 的 ACTIVE_VAULT 碰撞"; return 1 ;;
            1) ;;
            *) STEP_MSG="读 $(basename "$e") 出错(grep rc=${arc}), 无从断言无碰撞"; return 1 ;;
        esac
    done

    # 端口
    case "$PORT" in
        7691 | 7692 | 7478 | 11434)
            STEP_MSG="--port $PORT 与既有服务端口冲突（7691/7692 Neo4j, 7478 Browser, 11434 Ollama）"
            return 1
            ;;
    esac
    if command -v lsof > /dev/null 2>&1; then
        # lsof 的 rc：0 有命中 / 1 无命中 / **其它 = 出错**（Codex r2 HIGH-2：
        # 原版把「出错」也当成「空闲」）。出错时不敢断言空闲, 直接拒。
        local lrc=0
        lsof -nP -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1 || lrc=$?
        case "$lrc" in
            0) STEP_MSG="--port $PORT 已被占用（lsof LISTEN 命中）"; return 1 ;;
            1) ;;
            *) STEP_MSG="lsof 查询 --port $PORT 出错(rc=${lrc}), 无从断言端口空闲"; return 1 ;;
        esac
    fi

    # skills 数（零余量, 见头注 CLS_MIN_SKILLS）
    # Codex r3 MEDIUM-3：`find | wc | tr` 的 rc 被忽略 ⇒ find 部分读取失败但计数够大时
    # 仍报「树完整」。用 pipefail 子 shell 取 find 的 rc。
    local nskills frc=0
    nskills="$(set -o pipefail; find "$HARNESS/canvas-vault/.claude/skills" \
        -mindepth 2 -maxdepth 2 -type f -name SKILL.md 2> /dev/null | wc -l | tr -d ' ')" || frc=$?
    if [ "$frc" != 0 ]; then
        STEP_MSG="枚举 skills 出错(rc=${frc}), 无从断言数量"
        return 1
    fi
    if [ "$nskills" -lt "$CLS_MIN_SKILLS" ]; then
        STEP_MSG="skills 含 SKILL.md 的目录数 $nskills < $CLS_MIN_SKILLS"
        return 1
    fi

    # main.js（gitignored 构建产物, E-4 preflight build）
    local mainjs="$HARNESS/canvas-vault/.obsidian/plugins/canvas-learning-system/main.js"
    if [ ! -f "$mainjs" ]; then
        NEED_BUILD=1
        if [ "$APPLY" != 1 ]; then
            STEP_MSG="树完整 / 禁写面过 / 名不动点 / port $PORT 空闲 / skills $nskills; will build main.js（dry-run 不执行）"
            return 0
        fi
        # ⛔ 约束 npm 的写入面（Codex r9 §二.5 补边界）：缺省下 npm 会往 `~/.npm`
        #    与日志目录写，而那两处**不在本卡的待写清单里**、也没过判据。
        #    这里把 cache 与 logs 钉到 evidence 目录下（该目录已在 preflight 过判据），
        #    并关掉 audit/fund 的网络与额外输出。
        #    ⚠️ 如实声明：这只约束了 npm **配置层**能约束的部分；npm 及其依赖是否还有
        #    别的写入路径, 本卡未读其实现, **完整写入集合未证明**（已登记）。
        local _npmroot="$EVIDENCE_DIR/npm-$TS"
        mkdir -p "$_npmroot/cache" "$_npmroot/logs" \
            || { STEP_MSG="建 npm 缓存目录失败: $_npmroot"; return 1; }
        # ⛔ 墙钟上限（CARD-DEPLOY-TIMEOUT，集成期裁定 R-15）：这条 build 原先**没有任何上限**,
        #    npm 等网/等锁时会无限挂起 —— 候选树跑 tests/unit 时用例逐个卡死就是挂在这里。
        #    本机没有 timeout(1)/gtimeout（GNU coreutils 未装）⇒ 用 perl 的 alarm（走 PATH）:
        #    fork 一个**自成进程组**（setpgrp）的子进程 exec npm, 到点对**整个进程组**发
        #    TERM→KILL —— 只杀壳的话 npm fork 出来的孙子进程会变成还在跑的孤儿。
        # ⛔ 取值必须是**有界正整数**（Codex r1 HIGH-1）：`0` / `000` 在 Perl 里是
        #    `alarm 0` = **取消闹钟**；超 uint32 的值被截断（4294967296 → 0 = 取消,
        #    4294967297 → 1 秒）—— 都不是调用者写的那个数。这些值都能通过「只判非负整数」
        #    的旧校验, 于是保护被**静默关掉**, 正好退回本卡要修的那个状态。
        # ⛔ 字符集必须**逐字符枚举**而不是写区间（Codex r2 HIGH-1）：`[!0-9]` 的区间由
        #    locale 的排序决定 —— `LC_ALL=ar_EG.UTF-8` 下 `٠٥`（阿拉伯数字）能过这道门,
        #    随后 `[ -lt ]` 报 "integer expression expected" rc=2、`if` 判假 ⇒ **放行**,
        #    最终 `alarm '٠٥'` = alarm 0。写 `[!0123456789]` 与 locale 无关。
        #    并且数值比较必须放在「已确认是 1-5 位纯 ASCII 数字」**之后**, 它才不可能出错
        #    （比较一旦出错就是 rc=2 → if 判假 → 反而放行, 这类 fail-open 是本条的根源）。
        local _cap="$CLS_NPM_BUILD_TIMEOUT"
        case "$_cap" in
            '' | *[!0123456789]*)
                STEP_MSG="CLS_NPM_BUILD_TIMEOUT 必须是 ASCII 十进制整数秒, 实为 '${CLS_NPM_BUILD_TIMEOUT}'"
                return 1
                ;;
        esac
        # 先按原串长度拦（十万个 0 的剥零实测约 14s, 且发生在闹钟装上之前）
        if [ "${#_cap}" -gt 20 ]; then
            STEP_MSG="CLS_NPM_BUILD_TIMEOUT 位数过多（最多 20 位）, 实为 '${CLS_NPM_BUILD_TIMEOUT}'"
            return 1
        fi
        _cap="${_cap#"${_cap%%[!0]*}"}"   # 剥前导零（005 → 5；000 → 空）
        case "$_cap" in
            '' | *[!0123456789]*)         # 剥零后再判一次：空串(000) 与残留非数字都在这里落地
                STEP_MSG="CLS_NPM_BUILD_TIMEOUT 必须在 1..86400 秒内（0 会让上限静默失效）, 实为 '${CLS_NPM_BUILD_TIMEOUT}'"
                return 1
                ;;
        esac
        if [ "${#_cap}" -gt 5 ]; then     # 86400 是 5 位 ⇒ 再长必超界, 且不必做数值比较
            STEP_MSG="CLS_NPM_BUILD_TIMEOUT 必须在 1..86400 秒内（超界会让上限静默失效）, 实为 '${CLS_NPM_BUILD_TIMEOUT}'"
            return 1
        fi
        # 到这里 _cap 已确定是 1-5 位纯 ASCII 数字 ⇒ 下面的数值比较不可能 rc=2
        if [ "$_cap" -lt 1 ] || [ "$_cap" -gt 86400 ]; then
            STEP_MSG="CLS_NPM_BUILD_TIMEOUT 必须在 1..86400 秒内, 实为 '${CLS_NPM_BUILD_TIMEOUT}'"
            return 1
        fi
        # ⛔ 超时信号走**带外标记**而不是退出码（Codex r1 MEDIUM-2）：npm 自己立刻 `exit 124`
        #    与「上限到点」在退出码上无法区分, 会把普通失败误报成超时。标记串由 shell 生成
        #    并作为参数传给 perl（单一来源, 不手抄两份）, 带 pid 与时间戳 ⇒ npm 不可能撞上。
        #    子进程的 stdout/stderr 在 exec 前已改到 /dev/null, 所以捕获到的只可能是这个标记。
        local _mark="CLS-NPM-BUILD-TIMEDOUT-$$-$TS"
        local _build_rc=0 _build_out=""
        _build_out="$( (cd "$HARNESS/frontend/obsidian-plugin" \
            && npm_config_cache="$_npmroot/cache" \
               npm_config_logs_dir="$_npmroot/logs" \
               npm_config_update_notifier=false \
               npm_config_offline="$CLS_NPM_BUILD_OFFLINE" \
               npm_config_fund=false npm_config_audit=false \
               perl -e '
my $mark = shift @ARGV;
my $t = shift @ARGV;
my $pid = fork();
exit 125 unless defined $pid;
if ($pid == 0) {
    setpgrp(0, 0);
    open(STDOUT, ">", "/dev/null"); open(STDERR, ">", "/dev/null");
    exec { $ARGV[0] } @ARGV;
    exit 127;
}
$SIG{ALRM} = sub {
    kill(-15, $pid) or kill(15, $pid);
    select(undef, undef, undef, 2);
    kill(-9, $pid) or kill(9, $pid);
    print "$mark\n";
    exit 124;
};
alarm $t;
waitpid($pid, 0);
alarm 0;
my $st = $?;
exit($st & 127 ? 128 + ($st & 127) : $st >> 8);
' "$_mark" "$_cap" npm run build) 2> /dev/null )" || _build_rc=$?
        case "$_build_out" in
            *"$_mark"*)
                STEP_MSG="npm run build 超时（墙钟上限 ${_cap}s, 已杀 npm 所在进程组）: $HARNESS/frontend/obsidian-plugin"
                return 1
                ;;
        esac
        if [ "$_build_rc" != 0 ]; then
            STEP_MSG="npm run build 失败（$HARNESS/frontend/obsidian-plugin）"
            return 1
        fi
        if [ ! -f "$HARNESS/frontend/obsidian-plugin/main.js" ]; then
            STEP_MSG="npm run build 未产出 main.js"
            return 1
        fi
        mkdir -p "$(dirname "$mainjs")" \
            || { STEP_MSG="建插件目录失败: $(dirname "$mainjs")"; return 1; }
        cp "$HARNESS/frontend/obsidian-plugin/main.js" "$mainjs" \
            || { STEP_MSG="cp main.js 失败: $mainjs"; return 1; }
        [ -s "$mainjs" ] || { STEP_MSG="main.js 就位后为空: $mainjs"; return 1; }
        STEP_MSG="树完整 / 禁写面过 / 名不动点 / port $PORT 空闲 / skills $nskills; main.js 已 build 并就位"
        return 0
    fi
    STEP_MSG="树完整 / 禁写面过 / 名不动点 / port $PORT 空闲 / skills $nskills / main.js 在位"
    return 0
}

# ═══ 步 2 install ═══════════════════════════════════════════════════════════
ENV_KEYS_WHITELIST="NEO4J_HTTP_PORT NEO4J_BOLT_PORT OLLAMA_HOST VAULT_MOUNT_MODE LOCAL_EMBEDDER_BASE_URL"
ENV_KEYS_SKIPPED=""
SEED_ERR=""

seed_env_file() {
    # 从 <harness>/.env 只抄白名单键；源里没有的键**跳过**（不写空值——空键会让读者
    # 分不清「没配」与「配成空」；compose 侧 ${VAR:-默认} 对 unset 与 empty 同样回落，
    # 故跳过与写空在 compose 语义上等价, 跳过更诚实）。跳过清单进步 3 的输出。
    local src="$HARNESS/.env" k v
    SEED_ERR=""
    mkdir -p "$ENV_DIR" || { SEED_ERR="建 --env-dir 失败: $ENV_DIR"; return 1; }
    assert_writable_now "$ENV_FILE.tmp" || { SEED_ERR="$WRITE_GUARD_ERR"; return 1; }
    # umask 077 纵深（Codex r5 HIGH-3 同族）：临时文件从**诞生那一刻**就是 0600, 而不是
    # 先按缺省 umask 落 0644、等末尾 mv 后再 chmod。`||` 在子 shell 外, return 仍在函数里。
    (umask 077 && : > "$ENV_FILE.tmp") \
        || { SEED_ERR="建 .env 临时文件失败: $ENV_FILE.tmp"; return 1; }
    printf '# CARD-G2-7b deploy-vault.sh 生成 — vault=%s port=%s ts=%s\n' "$VAULT_NAME" "$PORT" "$TS" >> "$ENV_FILE.tmp"
    ENV_KEYS_SKIPPED=""
    local wrc
    for k in $ENV_KEYS_WHITELIST; do
        if [ ! -f "$src" ]; then
            ENV_KEYS_SKIPPED="$ENV_KEYS_SKIPPED $k"
            continue
        fi
        # ⛔ 区分 rc=1（没这个键）与 rc>1（读不动）（Codex r4 MEDIUM-2）：原版把两者都当
        #    「没有该键」⇒ 读取出错时白名单值静默丢失, 而六个固定键照写、步骤照样成功。
        wrc=0
        v="$(grep -E "^${k}=" "$src" 2> /dev/null | tail -1)" || wrc=$?
        if [ "$wrc" -gt 1 ]; then
            SEED_ERR="读 ${src##*/} 的 ${k} 出错(rc=${wrc}), 无从断言该键不存在"
            return 1
        fi
        if [ "$wrc" = 0 ]; then
            if [ -n "$v" ]; then
                # ⛔ 逐项判 rc（Codex r2 HIGH-2）：原版靠 `&& continue` 串起来,
                #    追加失败会静默落到「记为 skipped」而不是报错。
                printf '%s\n' "$v" >> "$ENV_FILE.tmp" \
                    || { SEED_ERR="写 .env 白名单键 ${k} 失败"; return 1; }
                continue
            fi
        fi
        ENV_KEYS_SKIPPED="$ENV_KEYS_SKIPPED $k"
    done
    # ⛔ 不用 `{ …; || exit 1; }`（Codex r3 MEDIUM-1，我上一轮引入的回归）：
    #    大括号在**当前 shell** 执行, 里面的 `exit 1` 会直接结束整个部署 ——
    #    绕过 run_step 的 7N 映射, 用户只看到进程 rc=1、没有任何 [N/6] FAIL 行。
    #    改为逐条判 rc 后 `return 1`, 让 run_step 正常映射成 72/73。
    local _fk
    for _fk in \
        "ACTIVE_VAULT=$VAULT_NAME" \
        "VAULTS_ROOT=$VAULT_PARENT" \
        "API_PORT=$PORT" \
        "CLS_BACKEND_CONTAINER=cls-$VAULT_NAME-backend" \
        "INTERNAL_API_KEY=" \
        "DAILY_REVIEW_VAULTS="; do
        printf '%s\n' "$_fk" >> "$ENV_FILE.tmp" \
            || { SEED_ERR="写 .env 固定字段失败: ${_fk%%=*}"; return 1; }
    done
    # 回读校验：确认六个必填键都真的落进去了（追加成功 ≠ 内容完整）
    local kk
    for kk in ACTIVE_VAULT VAULTS_ROOT API_PORT CLS_BACKEND_CONTAINER INTERNAL_API_KEY DAILY_REVIEW_VAULTS; do
        grep -qE "^${kk}=" "$ENV_FILE.tmp" \
            || { SEED_ERR="写 .env 后回读缺键: ${kk}"; return 1; }
    done
    mv "$ENV_FILE.tmp" "$ENV_FILE" || { SEED_ERR="mv .env 失败: $ENV_FILE"; return 1; }
    pinned_chmod600 "$ENV_FILE" || { SEED_ERR="chmod 600 .env 失败: $ENV_FILE"; return 1; }
    return 0
}

step2_install() {
    # dry-run 的 "will run" 是用户唯一的预览 —— 与下面**真正执行**的那条必须逐项同值
    # （Codex r4 MEDIUM-3：这行曾残留 `$(dirname "$VAULT")`, 与实际传的 $VAULT_PARENT 分叉）,
    # 且值里有空格时仍要**能粘贴执行** ⇒ 逐值 %q。cmd 只用于显示, 不用于执行。
    local cmd
    cmd="$(printf '%q %q --subject %q --vaults-root %q --source %q --env-file %q --harness-tree %q --backend-url %q' \
        "$HARNESS/scripts/install-vault.sh" "$VAULT_NAME" "$SUBJECT" "$VAULT_PARENT" \
        "$HARNESS/canvas-vault" "$ENV_FILE" "$HARNESS" "http://127.0.0.1:$PORT")"
    if [ "$APPLY" != 1 ]; then
        STEP_MSG="will run: $cmd"
        return 2
    fi
    if [ ! -f "$ENV_FILE" ]; then
        seed_env_file || { STEP_MSG="${SEED_ERR:-派生 .env 失败}"; return 1; }
    fi
    # ⚠️ evidence 目录必须**在这里**建, 不能在主流程顶层建（Codex r1 BLOCKER-2：那样会早于
    #    preflight, 禁写面拒绝时目录已经落地）。此刻 preflight 已过, 建它是安全的。
    #    这一步不是可选的：下面 install 的输出要重定向进去, 目录不存在 ⇒ 重定向失败 ⇒
    #    install **根本没跑**, 而旧消息会把它说成「install-vault.sh 非零退出」（误导）。
    mkdir -p "$EVIDENCE_DIR" || { STEP_MSG="建 evidence 目录失败: $EVIDENCE_DIR"; return 1; }
    local ilog="$EVIDENCE_DIR/install-$TS.txt"
    # ⛔ 截断前再查一次（Codex r3 BLOCKER-2）：preflight 到此刻之间文件可能被换成软链,
    #    而 `: >` 会沿链把目标文件清空。这一步是**写之前的最后一道**。
    if [ -L "$ilog" ]; then
        STEP_MSG="install 日志是软链, 截断会穿到别处: $ilog -> $(readlink "$ilog")"
        return 1
    fi
    assert_writable_now "$ilog" || { STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
    : > "$ilog" || { STEP_MSG="无法写 install 日志(重定向失败, install 未执行): $ilog"; return 1; }
    local irc=0
    CLS_REPO="$HARNESS" "$HARNESS/scripts/install-vault.sh" "$VAULT_NAME" \
        --subject "$SUBJECT" --vaults-root "$VAULT_PARENT" \
        --source "$HARNESS/canvas-vault" --env-file "$ENV_FILE" \
        --harness-tree "$HARNESS" --backend-url "http://127.0.0.1:$PORT" \
        >> "$ilog" 2>&1 || irc=$?
    if [ "$irc" != 0 ]; then
        STEP_MSG="install-vault.sh rc=${irc}, 见 $ilog"
        return 1
    fi
    STEP_MSG="install-vault.sh rc 0, 输出 $ilog"
    return 0
}

# ═══ 步 3 postprocess ═══════════════════════════════════════════════════════
KEY_REGENERATED="no"
step3_postprocess() {
    local keyfile="$VAULT/.obsidian/cls-internal-key.txt"
    local datajson="$VAULT/.obsidian/plugins/canvas-learning-system/data.json"
    if [ "$APPLY" != 1 ]; then
        STEP_MSG="will: 重生 key(0600) → 同值写 $keyfile / $(basename "$ENV_FILE") INTERNAL_API_KEY / data.json internalApiKey; :8011 → :$PORT ×4; 在位判 CLAUDE.md/.claude/skills/.mcp.json"
        return 2
    fi

    # ══ Phase A：只读前置校验 ══════════════════════════════════════════════════
    # 全部过了才动手写。⚠️ 之前的版本把「写 key」排在「.env 一致性断言」之前，导致断言
    # 失败时留下「key 已写、.env 与 data.json 未同步」的半成品（Codex 问题 ③ 的正是这个）。
    local t rel

    # A1 宿主绑定三件在位（--hosts claude 的「绑定」定义）
    for t in "$VAULT/CLAUDE.md" "$VAULT/.mcp.json"; do
        [ -f "$t" ] || { STEP_MSG="宿主绑定件缺失: $t"; return 1; }
    done
    [ -d "$VAULT/.claude/skills" ] || { STEP_MSG="宿主绑定件缺失: $VAULT/.claude/skills"; return 1; }

    # A2 端口模板化的全部目标先只查存在性 —— 不能边查边改, 否则第 3 个缺失时前 2 个已被改
    for rel in $PORT_TEMPLATED_FILES; do
        [ -f "$VAULT/$rel" ] || { STEP_MSG="端口模板化目标缺失: $VAULT/$rel"; return 1; }
    done
    [ -f "$datajson" ] || { STEP_MSG="插件 data.json 缺失: $datajson"; return 1; }

    # A3 已存在的 .env.<vault> 必须与本次参数一致 —— 否则「实例监听 .env 的 API_PORT，
    #    而 vault 内四个文件被模板化成 --port」= 静默不一致，只有传 --activate 时步 5 的
    #    config 断言才会撞上。这里提前 fail-closed，且**不静默覆盖**用户已有的 .env。
    #    （.env 不存在时由 B1 的 seed 按参数写出，天然一致，无需断言。）
    if [ -f "$ENV_FILE" ]; then
        # Codex r3 HIGH-4 三处收紧：① 读取管道判 rc（原版读失败 ⇒ have 空 ⇒ 放行）
        #   ② 缺键也要拒（原版只在 have 非空时比较, 缺 API_PORT/ACTIVE_VAULT 直接通过）
        #   ③ 比较范围补上 VAULTS_ROOT（它决定容器看不看得见这个 vault）
        # ⛔ 不能用「空格分隔的字符串 + for 拆词」（Codex r4 HIGH-2，我 r3 加 VAULTS_ROOT 时
        #    引入的回归）：父路径含空格时 `/tmp/course vaults/course` 会被拆成两项, 比较拿到
        #    截断值 ⇒ 合法部署在安装完成后 rc=73、重跑又被 72 拦住。改用**数组**, 元素含空格不拆。
        local -a want_keys=(API_PORT ACTIVE_VAULT CLS_BACKEND_CONTAINER VAULTS_ROOT)
        local -a want_vals=("$PORT" "$VAULT_NAME" "cls-$VAULT_NAME-backend" "$VAULT_PARENT")
        local i k v have grc line
        for i in "${!want_keys[@]}"; do
            k="${want_keys[$i]}"
            v="${want_vals[$i]}"
            grc=0
            line="$(grep -E "^${k}=" "$ENV_FILE" 2> /dev/null | tail -1)" || grc=$?
            if [ "$grc" -gt 1 ]; then
                STEP_MSG="读 $(basename "$ENV_FILE") 的 ${k} 出错(rc=${grc}), 无从断言一致"
                return 1
            fi
            if [ -z "$line" ]; then
                STEP_MSG="已有 $(basename "$ENV_FILE") 缺键 ${k}（无法确认与本次参数一致；删掉该 .env 重来）"
                return 1
            fi
            have="$(printf '%s' "$line" | cut -d= -f2- | tr -d '"'"'" | tr -d '\r')"
            if [ "$have" != "$v" ]; then
                STEP_MSG="已有 $(basename "$ENV_FILE") 的 ${k}=${have} 与本次参数 ${v} 矛盾（拒绝静默覆盖；改 --port/--vault 或删掉该 .env 重来）"
                return 1
            fi
        done
    fi

    # A4 key 值确定（已存在则读, 不重生 = 幂等）——**此时不落盘**, 见 B5
    local key krc=0
    if [ -f "$keyfile" ]; then
        # ⛔ 必须检查 cat 的 rc 并校验格式（Codex r1 HIGH-4 指出的精确条件）：
        #    `key="$(cat …)"` 在读到**部分内容后失败**时（I/O 错误、被并发截断）会返回
        #    非空前缀且 rc≠0。原版忽略 rc ⇒ B3/B4 用那个残缺前缀写 .env 与 data.json,
        #    而 B5 见「文件已存在」不重写 ⇒ 文件里是完整旧 key、另两处是残缺前缀。
        key="$(cat "$keyfile")" || krc=$?
        if [ "$krc" != 0 ]; then
            STEP_MSG="读 key 文件失败(rc=${krc}), 拒绝用可能残缺的值同步三处: $keyfile"
            return 1
        fi
        KEY_REGENERATED="no(已存在)"
    else
        key="$(openssl rand -hex 32)" || { STEP_MSG="openssl rand 失败"; return 1; }
        KEY_REGENERATED="yes"
    fi
    # 格式校验：openssl rand -hex 32 恒为 64 个小写 hex。任何别的形态都拒 ——
    # 残缺前缀、被编辑器加了尾注、文件里被写进别的内容, 都在这里止住。
    case "$key" in
        *[!0-9a-f]* | "") STEP_MSG="key 形态非法(应为 64 位小写 hex), 拒绝同步"; return 1 ;;
    esac
    if [ "${#key}" != 64 ]; then
        STEP_MSG="key 长度 ${#key} != 64, 拒绝同步（疑为读取残缺或被改写）"
        return 1
    fi

    # ══ Phase B：写 ═══════════════════════════════════════════════════════════
    # 顺序讲究：key **文件**最后写。「key 文件存在」是幂等锚点（A4 据它判不重生），
    # 只在其余两处都同步完成后才让这个最强信号出现。
    # B1 .env.<vault> 不存在则按白名单派生
    if [ ! -f "$ENV_FILE" ]; then
        seed_env_file || { STEP_MSG="${SEED_ERR:-派生 .env 失败}"; return 1; }
    fi

    # B2 端口模板化（只对目标副本；:8011 精确到端口段, 不误伤别的数字）
    # 清单单一来源 = $PORT_TEMPLATED_FILES（步 4 的源镜像用同一份）+ data.json。
    # data.json 不进镜像清单: 它是 generate 项、源里本就不存在（.gitignore:210）。
    for rel in $PORT_TEMPLATED_FILES; do
        sed -i '' "s|:8011|:$PORT|g" "$VAULT/$rel" || { STEP_MSG="sed 模板化失败: $rel"; return 1; }
    done
    sed -i '' "s|:8011|:$PORT|g" "$datajson" || { STEP_MSG="sed 模板化失败: $datajson"; return 1; }
    if [ "$PORT" != "8011" ]; then
        # ⛔ grep 的 rc 有三态（Codex r2 HIGH-2）：0 命中 / 1 未命中 / **2 出错**。
        #    原版 `grep -q … && left=…` 把 rc 2 当成「未命中 = 无残留」 ⇒ 读不动文件时假绿。
        local left="" grc=0
        for rel in $PORT_TEMPLATED_FILES; do
            grc=0
            grep -q ':8011' "$VAULT/$rel" 2> /dev/null || grc=$?
            case "$grc" in
                0) left="$left $rel" ;;
                1) ;;
                *) STEP_MSG="残留检查读不动 ${rel}（grep rc=${grc}）, 无从断言"; return 1 ;;
            esac
        done
        grc=0
        grep -q ':8011' "$datajson" 2> /dev/null || grc=$?
        case "$grc" in
            0) left="$left data.json" ;;
            1) ;;
            *) STEP_MSG="残留检查读不动 data.json（grep rc=${grc}）, 无从断言"; return 1 ;;
        esac
        if [ -n "$left" ]; then
            STEP_MSG="模板化后仍有 :8011 残留:$left"
            return 1
        fi
    fi

    # B3 插件 data.json internalApiKey 同值（只改这一键）
    if ! python3 - "$datajson" "$key" "$(dirname "$FORBID_PY")" "$CLS_LIVE_VAULT" << 'PY'; then
import json, os, sys
p, key, moddir, live = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, moddir)
from cls_forbidden_paths import open_pinned, write_all


# 同 .env：读与写绑同一个 pinned fd（Codex r7 HIGH-1）
# ⛔ 不带 O_CREAT（Codex r8 MEDIUM-4）：`.env`/`data.json` 到这一步**必然已存在**
#    （seed / installer 建的）。带 O_CREAT 会在文件被移走时**造一个空文件**继续走完,
#    把「实例字段全丢了」伪装成成功；不带则 ENOENT, 如实失败。
fd = open_pinned(p, os.O_RDWR, 0o600, live_vault=live)
try:
    st = os.fstat(fd)
    if st.st_nlink > 1:
        raise SystemExit(f"data.json 有 {st.st_nlink} 个硬链接, 写入会改共享 inode: {p}")
    os.fchmod(fd, 0o600)
    chunks = []
    while True:
        b = os.read(fd, 65536)
        if not b:
            break
        chunks.append(b)
    d = json.loads(b"".join(chunks).decode("utf-8"))
    d["internalApiKey"] = key
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    write_all(fd, (json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    os.fsync(fd)
finally:
    os.close(fd)
PY
        STEP_MSG="写 data.json internalApiKey 失败"
        return 1
    fi

    # B4 .env.<vault> 的 INTERNAL_API_KEY 同值
    # ⛔ 收紧权限必须在 O_NOFOLLOW **打开并查过链接数之后**, 且作用在**同一个 fd** 上
    #    （Codex r6 HIGH-1 —— 这是我 r5 修 HIGH-3 时引入的第 5 次自伤）：
    #    r5 我在 bash 里写了 `[ -e ] && chmod 600 "$ENV_FILE"` 放在 python 块**之前**。
    #    若 `.env.<vault>` 在 A3 校验之后、B4 之前被换成指向保护文件的**软链或硬链接**,
    #    那次 chmod 会**先改掉保护对象的权限**, 之后才轮到 O_NOFOLLOW / nlink 把写拒掉 ——
    #    旧版反而没有这个越界写。而且它改的是元数据, 内容 sha 与 `find -newermt` 都看不见。
    #    ⇒ 正解：`os.fchmod(fd)`。fd 由 O_NOFOLLOW 取得（末段是软链就根本打不开）,
    #      且已过 nlink 检查, 此时改权限只可能落在那个已确认安全的 inode 上。
    #      bash 侧的写前 chmod 与写后 chmod 一并删除, 权限收紧只剩这一处。
    if ! python3 - "$ENV_FILE" "$key" "$(dirname "$FORBID_PY")" "$CLS_LIVE_VAULT" << 'PY'; then
import os, sys
p, key, moddir, live = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, moddir)
from cls_forbidden_paths import open_pinned, write_all


# ⛔ 读与写必须绑在**同一个** pinned fd 上（Codex r7 HIGH-1）：
#    原来「先按路径 open() 读、再按路径 open() 写」有两个各自跟随祖先的解析,
#    父目录在两次之间被换掉就会把**安全文件的旧内容**写进保护文件。
#    open_pinned 见 cls_forbidden_paths：解析后当场过判据 + 逐级 O_NOFOLLOW。
# ⛔ 不带 O_CREAT（Codex r8 MEDIUM-4）：`.env`/`data.json` 到这一步**必然已存在**
#    （seed / installer 建的）。带 O_CREAT 会在文件被移走时**造一个空文件**继续走完,
#    把「实例字段全丢了」伪装成成功；不带则 ENOENT, 如实失败。
fd = open_pinned(p, os.O_RDWR, 0o600, live_vault=live)
try:
    st = os.fstat(fd)
    if st.st_nlink > 1:
        raise SystemExit(f".env 有 {st.st_nlink} 个硬链接, 写入会改共享 inode: {p}")
    # ⛔ 唯一的权限收紧点（r6 HIGH-1）：在 O_NOFOLLOW + nlink 之后, 作用于同一 fd。
    os.fchmod(fd, 0o600)
    chunks = []
    while True:
        b = os.read(fd, 65536)
        if not b:
            break
        chunks.append(b)
    # ⛔ 恢复通用换行（Codex r8 MEDIUM-3）：旧的文本模式读取把 `\r` / `\r\n` 也当换行,
    #    换成裸字节后只按 `\n` 切会把 `KEY=old\rEXTRA=keep` 整段当**一行**替换掉,
    #    连带删掉 EXTRA。先归一到 `\n` 再切, 与旧行为等价。
    _raw = b"".join(chunks).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    lines = _raw.split("\n")
    out, done = [], False
    for line in lines:
        if line.startswith("INTERNAL_API_KEY="):
            out.append(f"INTERNAL_API_KEY={key}")
            done = True
        else:
            out.append(line)
    if not done:
        out.append(f"INTERNAL_API_KEY={key}")
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    write_all(fd, "\n".join(out).encode("utf-8"))
    os.fsync(fd)
finally:
    os.close(fd)
PY
        STEP_MSG="写 $ENV_FILE 的 INTERNAL_API_KEY 失败"
        return 1
    fi
    # （原写后 `chmod 600 "$ENV_FILE"` 已删 —— 权限收紧统一由上面的 `os.fchmod(fd)` 承担,
    #   那一处在 O_NOFOLLOW + nlink 之后, 不会像路径式 chmod 那样改到被换掉的对象。r6 HIGH-1）

    # B5 key **文件**落盘 —— 最后一步。A4 已确定值; 已存在则不重写、只校正权限。
    # 为什么最后：「key 文件存在」是 A4 判「不重生」的锚点。若它先落盘而后续两处失败，
    # 下次重跑会读到它、不重生, 而另两处仍旧空 —— 半成品被这个最强信号掩盖。放最后则
    # 前面任何失败都不会留下这个信号。
    # ⚠️ 如实声明（Codex r2 MEDIUM 更正了原注释）：tmp + 回读 + mv 只保证**这一个文件**的
    #    发布是原子的, **不是三文件事务**。Phase B 内部失败后三处可能不一致；而**整脚本
    #    重跑会先被 install 的防覆盖闸门拦成 rc 72**, 到不了步 3 ⇒ **不会自动收敛**。
    #    原注释写的「重跑会重生并覆盖两处 ⇒ 自愈」与实际入口不符, 已删。
    #    收敛需要 adopt 语义（重新绑定已有 vault）, 归 CARD-G2-7c。
    if [ "$KEY_REGENERATED" = "yes" ]; then
        mkdir -p "$(dirname "$keyfile")" || { STEP_MSG="建 key 文件父目录失败"; return 1; }
        # 原子落盘：先写 tmp（umask 077）→ 回读比对 → mv。中途失败不会留下**部分内容的**
        # key 文件, 而「key 文件存在」正是 A4 判「不重生」的锚点 —— 半个 key 比没有 key 更坏。
        assert_writable_now "$keyfile.tmp" || { STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
        (umask 077 && printf '%s\n' "$key" > "$keyfile.tmp") \
            || { STEP_MSG="写 key 临时文件失败"; return 1; }
        # ⛔ 回读也要判 rc（Codex r2 MEDIUM）：完整输出后 rc≠0 时比较仍相等 ⇒ 假绿。
        local rb rbrc=0
        rb="$(cat "$keyfile.tmp")" || rbrc=$?
        if [ "$rbrc" != 0 ] || [ "$rb" != "$key" ]; then
            rm -f -- "$keyfile.tmp"
            STEP_MSG="key 临时文件回读不一致, 已丢弃（未污染 ${keyfile}）"
            return 1
        fi
        mv "$keyfile.tmp" "$keyfile" || { STEP_MSG="mv key 文件失败"; return 1; }
    fi
    pinned_chmod600 "$keyfile" || { STEP_MSG="chmod 600 key 文件失败"; return 1; }

    STEP_MSG="key 重生=$KEY_REGENERATED(0600) 三处同值; :8011→:$PORT ×4 已验残留 0; 绑定三件在位;"
    STEP_MSG="$STEP_MSG .env 白名单跳过:${ENV_KEYS_SKIPPED:- 无}"
    return 0
}

# ═══ 步 4 verify ════════════════════════════════════════════════════════════
# 步 3 ③ 会把目标副本里的 :8011 改成 :<port>（实例特化）。若拿它与**未特化的源**逐字节
# 比，那三个 copy 项必然报 content-drift —— 而目标其实是对的。
# 两个错解：① 步 4 不传 --source（校验器会打 content-drift: not evaluated）—— 那是把
# 内容比较**整个轴**丢掉，门却还是绿的；② 放宽步 4 的 rc 判据 —— 禁放宽。
# 正解：把比较基准搬到与被比对象**同一端口口径**上 —— 镜像源、对同样那三个文件做同样的
# 模板化，再当 --source。drift 轴保留：步 3 若改坏别的东西照样报。
PORT_TEMPLATED_FILES=".mcp.json .claude/settings.json .claude/hooks/session-end-archive.py"
SRC_MIRROR=""
CLEANUP_MIRROR_ERR=""
cleanup_mirror() {
    if [ -n "$SRC_MIRROR" ] && [ -d "$SRC_MIRROR" ]; then
        # ⛔ 清理失败必须留痕（Codex r1 HIGH-3）：原版无论成败都把 SRC_MIRROR 清空,
        #    于是「tmp 里留了一份源镜像」被静默吞掉, 步 4 仍报 OK。
        if rm -rf -- "$SRC_MIRROR"; then
            SRC_MIRROR=""
        else
            CLEANUP_MIRROR_ERR="源镜像未能清理: $SRC_MIRROR"
        fi
    fi
}
trap cleanup_mirror EXIT INT TERM

step4_verify() {
    # ⛔ dry-run 一律 SKIP（Codex r1 HIGH-1）：原版只判 vault 是否存在, 没判 APPLY ——
    #    目标**已存在**时的 dry-run 会建 evidence 目录、写报告, 非 8011 还会建源镜像,
    #    「不传 --apply = 零写」当场不成立。零写复验此前只测过「目标不存在」那一支。
    if [ "$APPLY" != 1 ]; then
        STEP_MSG="will run: verify_vault_install.py --vault ${VAULT}（dry-run 零写, 不跑不落报告）"
        return 2
    fi
    if [ ! -d "$VAULT" ]; then
        STEP_MSG="目标 vault 不存在, 无从校验"
        return 1
    fi
    mkdir -p "$EVIDENCE_DIR" || { STEP_MSG="建 evidence 目录失败: $EVIDENCE_DIR"; return 1; }

    local src="$HARNESS/canvas-vault" basis="源本体" t
    if [ "$PORT" != "8011" ]; then
        # ⛔ TMPDIR 是**继承来的**（Codex r4 BLOCKER-3）：指向保护目录时, 这里的
        #    mktemp/cp/sed 会直接往保护区写, 而 preflight 的产出清单里根本没有它。
        #    先把镜像根交给判据, 过了才建。
        if check_forbidden_paths --outputs "src-mirror-root:${TMPDIR:-/tmp}"; then
            STEP_MSG="禁写面: 源镜像根（TMPDIR）指向 $FORBIDDEN_HIT"
            return 1
        fi
        SRC_MIRROR="$(mktemp -d "${TMPDIR:-/tmp}/cls-srcmirror-XXXXXX")" || {
            STEP_MSG="建源镜像临时目录失败"
            return 1
        }
        if ! cp -R "$HARNESS/canvas-vault/." "$SRC_MIRROR/" 2> /dev/null; then
            STEP_MSG="镜像源失败: $SRC_MIRROR"
            return 1
        fi
        # ⛔ 镜像**根**合法 ≠ 镜像**里**要写的对象合法（Codex r5 BLOCKER-4）：
        #    `cp -R` 会**保留源树里的软链**。源树若有 `canvas-vault/.claude/hooks -> <保护目录>`,
        #    镜像里那一段仍是指向保护区的软链, 下面的 `sed -i` 会沿链写过去 —— 无需任何
        #    竞争窗口, 而 r4 只把 `TMPDIR` 这个**根**交给了判据。
        #    修法与 preflight 的 PENDING_WRITES 同律：把**实际要写的每个文件**过同一份
        #    判据 + 同一个写前复查, 而不是再发明一层新判据（新形状 = 新的边）。
        # ⚠️ 必须 `local -a` 且显式赋空：bash 3.2 下对**未声明**数组做 `"${a[@]}"` 在
        #    `set -u` 里会报错；先 `=()` 声明成空数组, 再用计数守住展开。
        local mt
        local -a MIRROR_WRITES=()
        for t in $PORT_TEMPLATED_FILES; do
            [ -f "$SRC_MIRROR/$t" ] && MIRROR_WRITES+=("mirror-$t:$SRC_MIRROR/$t")
        done
        if [ "${#MIRROR_WRITES[@]}" -gt 0 ]; then
            if check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"; then
                cleanup_mirror
                STEP_MSG="禁写面: 源镜像内待模板化文件 $FORBIDDEN_HIT"
                return 1
            fi
            for mt in "${MIRROR_WRITES[@]}"; do
                assert_writable_now "${mt#*:}" || {
                    cleanup_mirror
                    STEP_MSG="$WRITE_GUARD_ERR"
                    return 1
                }
            done
        fi
        for t in $PORT_TEMPLATED_FILES; do
            if [ -f "$SRC_MIRROR/$t" ]; then
                sed -i '' "s|:8011|:$PORT|g" "$SRC_MIRROR/$t" || {
                    cleanup_mirror
                    STEP_MSG="源镜像模板化失败: $t"
                    return 1
                }
            fi
        done
        src="$SRC_MIRROR"
        basis="源镜像(同 :$PORT 口径)"
    fi

    local rep="$EVIDENCE_DIR/verify-$TS.txt" rc=0
    assert_writable_now "$rep" || { cleanup_mirror; STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
    python3 "$HARNESS/scripts/verify_vault_install.py" --vault "$VAULT" \
        --source "$src" \
        --manifest "$HARNESS/scripts/vault-install-manifest.json" \
        --report "$rep" > /dev/null 2>&1 || rc=$?
    cleanup_mirror
    if [ "$rc" != 0 ]; then
        STEP_MSG="verify_vault_install.py rc=${rc}（1 missing / 2 mismatch / 3 usage）, 基准=$basis, 报告 $rep"
        return 1
    fi
    if [ -n "$CLEANUP_MIRROR_ERR" ]; then
        STEP_MSG="校验器 rc 0（基准=${basis}）但 $CLEANUP_MIRROR_ERR"
        return 1
    fi
    STEP_MSG="校验器 rc 0（含 content-drift 轴, 基准=${basis}）, 报告 $rep"
    return 0
}

# ═══ 步 5 activate ══════════════════════════════════════════════════════════
step5_activate() {
    if [ "$ACTIVATE" != 1 ]; then
        STEP_MSG="未传 --activate（缺省只部署不激活）"
        return 2
    fi
    mkdir -p "$EVIDENCE_DIR" || { STEP_MSG="建 evidence 目录失败: $EVIDENCE_DIR"; return 1; }
    # ⛔ `docker compose config` 会把 --env-file 与宿主 env 里的凭据**展开成明文**
    #    （INTERNAL_API_KEY / GOOGLE_API_KEY / NEO4J_PASSWORD / NEO4J_AUTH / …）。
    #    原样落盘 = 把密钥写进 evidence 目录, 而 evidence 是要入库的。
    #    故落盘前脱敏; 断言只看 container_name 与 ports, 不需要那些值 ——
    #    明文因此**从不落盘**（不是「落了再擦」）。
    local cfg="$EVIDENCE_DIR/compose-config-$TS.txt" rc=0
    assert_writable_now "$cfg" || { STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
    docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
        -p "cls-$VAULT_NAME" --project-directory "$HARNESS" config 2> /dev/null \
        | redact_secrets > "$cfg" || rc=$?
    if [ "$rc" != 0 ]; then
        STEP_MSG="docker compose config rc=${rc}（未起任何容器）"
        return 1
    fi
    # ⚠️ 结构化断言, 不用 grep 单行：`docker compose config` 把 ports 展开成**长格式**
    #    （mode/host_ip/target/published/protocol 各一行），短格式字面量 "127.0.0.1:<p>:8001"
    #    根本不存在；而单独 grep `published: "<p>"` 又不带服务归属，别的服务用同端口就假绿。
    #    故解析 YAML, 断言 services.backend 的 container_name 与 ports 恰含一条
    #    {host_ip:127.0.0.1, target:8001, published:<port>}。
    # ⚠️ 用 rc 判定, 不用「输出是否为空」：若 python 因别的原因失败（pyyaml 缺、文件读不动）
    #    却没打印任何东西, 「空输出 = 通过」就是假绿。
    local py="$HARNESS/backend/.venv/bin/python" pout="" prc=0
    if [ ! -x "$py" ]; then
        STEP_MSG="harness venv 缺, 无法结构化断言 config: $py"
        return 1
    fi
    pout="$("$py" - "$cfg" "cls-$VAULT_NAME-backend" "$PORT" << 'PY' 2>&1
import sys, yaml
cfg, want_name, port = sys.argv[1], sys.argv[2], sys.argv[3]
d = yaml.safe_load(open(cfg, encoding="utf-8")) or {}
be = (d.get("services") or {}).get("backend") or {}
cn = be.get("container_name")
if cn != want_name:
    sys.stdout.write("container_name=%r want %r" % (cn, want_name))
    sys.exit(1)
hits = [p for p in (be.get("ports") or [])
        if str(p.get("published")) == port
        and str(p.get("target")) == "8001"
        and p.get("host_ip") == "127.0.0.1"]
if len(hits) != 1:
    sys.stdout.write("backend ports 命中 %d 条 (期望 1): %r" % (len(hits), be.get("ports")))
    sys.exit(1)
PY
)" || prc=$?
    if [ "$prc" != 0 ]; then
        STEP_MSG="config 结构化断言不成立(rc=${prc}): ${pout:-无输出}"
        return 1
    fi
    if [ "$CLS_DEPLOY_ALLOW_DOCKER_UP" != 1 ]; then
        STEP_MSG="config 断言过（container_name/端口各 1）; 未设 CLS_DEPLOY_ALLOW_DOCKER_UP=1 ⇒ 不执行 up -d（缺省即不做, 需用户当次授权）"
        return 2
    fi
    # 真 activate（G2-8 面）：起/重建该 vault 的绑定实例 + 健康断言 + 失败回滚。
    # 需用户当次授权；车道禁跑（见头注与 §三）。
    local up_rc=0
    docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
        -p "cls-$VAULT_NAME" --project-directory "$HARNESS" up -d backend \
        >> "$cfg" 2>&1 || up_rc=$?
    if [ "$up_rc" != 0 ]; then
        local down_rc=0
        docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
            -p "cls-$VAULT_NAME" --project-directory "$HARNESS" down >> "$cfg" 2>&1 || down_rc=$?
        # ⛔ down 失败时不得仍声称「已回滚」（Codex r1 HIGH-3）
        if [ "$down_rc" = 0 ]; then
            STEP_MSG="up -d backend rc=${up_rc}, 已回滚 down"
        else
            STEP_MSG="up -d backend rc=${up_rc}, 且回滚 down 也失败(rc=${down_rc}) — 容器可能仍在, 需人工处置"
        fi
        return 1
    fi
    # ⛔ curl 的 rc 必须单独判（Codex r1 HIGH-3）：`… || printf ''` 会把「已输出部分
    #    响应后失败」变成「拿到了内容」, 而那段部分响应里恰好可能已经含 vault 名 ⇒ 假绿。
    local cur="" curl_rc=0
    cur="$(curl -sS --fail -m 10 "http://127.0.0.1:$PORT/api/v1/vault/current" 2> /dev/null)" || curl_rc=$?
    if [ "$curl_rc" != 0 ]; then
        cur=""
    fi
    if [ -z "$cur" ] || ! printf '%s' "$cur" | grep -q "$VAULT_NAME"; then
        local down_rc2=0
        docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
            -p "cls-$VAULT_NAME" --project-directory "$HARNESS" down >> "$cfg" 2>&1 || down_rc2=$?
        if [ "$down_rc2" = 0 ]; then
            STEP_MSG="/api/v1/vault/current 未报告 $VAULT_NAME, 已回滚 down"
        else
            STEP_MSG="/api/v1/vault/current 未报告 $VAULT_NAME, 且回滚 down 失败(rc=${down_rc2}) — 需人工处置"
        fi
        return 1
    fi
    STEP_MSG="实例 cls-$VAULT_NAME 已起, /vault/current 报告 $VAULT_NAME"
    return 0
}

# ═══ 步 6 evidence ══════════════════════════════════════════════════════════
step6_evidence() {
    # dry-run 一律不落盘。(c) 参数表承诺「不传 --apply = 零写」，而缺省 evidence-dir 就在
    # <harness>/_bmad-output/ 内 —— 若 dry-run 也写，探一下就会在 harness 树里留未追踪文件。
    # 「零写」是安全承诺，evidence 只是副产物，冲突时前者优先（本卡裁定, 验收单登记）。
    if [ "$APPLY" != 1 ]; then
        STEP_MSG="will write: $EVIDENCE_DIR/deploy-<ts>.txt（dry-run 零写, 不落盘）"
        return 2
    fi
    mkdir -p "$EVIDENCE_DIR" || { STEP_MSG="建 evidence 目录失败: $EVIDENCE_DIR"; return 1; }
    local out="$EVIDENCE_DIR/deploy-$TS.txt" t _sha _sha_fail=0 _src=0
    assert_writable_now "$out.tmp" || { STEP_MSG="$WRITE_GUARD_ERR"; return 1; }
    {
        printf '# CARD-G2-7b deploy-vault.sh — %s\n' "$TS"
        printf '## 参数\n'
        printf '  mode=%s vault=%s vault_name=%s\n' "$MODE" "$VAULT" "$VAULT_NAME"
        printf '  harness=%s port=%s hosts=%s subject=%s\n' "$HARNESS" "$PORT" "$HOSTS" "$SUBJECT"
        printf '  activate=%s also_push=%s(未实现,登记 G2-8) evidence_dir=%s env_dir=%s\n' \
            "$ACTIVATE" "$ALSO_PUSH" "$EVIDENCE_DIR" "$ENV_DIR"
        printf '  CLS_MIN_SKILLS=%s CLS_DEPLOY_ALLOW_DOCKER_UP=%s\n' "$CLS_MIN_SKILLS" "$CLS_DEPLOY_ALLOW_DOCKER_UP"
        printf '## 六行状态\n'
        for t in "${STEP_LINES[@]}"; do printf '  %s\n' "$t"; done
        printf '## 文件 sha256（密钥件只 sha, 不记内容）\n'
        for t in "$VAULT/.canvas-config.yaml" "$VAULT/.mcp.json" \
            "$VAULT/.claude/settings.json" "$VAULT/.claude/hooks/session-end-archive.py" \
            "$VAULT/.obsidian/plugins/canvas-learning-system/data.json" \
            "$VAULT/.obsidian/cls-internal-key.txt" "$ENV_FILE"; do
            if [ -f "$t" ]; then
                # ⛔ shasum 失败会被外层 printf 的成功掩盖（Codex r2 HIGH-2）⇒ 先算再判。
                # Codex r3 MEDIUM-2：非空输出 + 非零退出仍算成功 ⇒ 必须判 rc。
                _src=0
                _sha="$(shasum -a 256 "$t" 2> /dev/null | cut -d' ' -f1)" || _src=$?
                if [ "$_src" != 0 ] || [ -z "$_sha" ]; then
                    printf '  %-64s %s (SHASUM-FAILED)\n' '-' "${t#"$VAULT"/}"
                    _sha_fail=1
                else
                    printf '  %s  %s\n' "$_sha" "${t#"$VAULT"/}"
                fi
            else
                printf '  %-64s %s (ABSENT)\n' '-' "${t#"$VAULT"/}"
            fi
        done
    } > "$out.tmp" 2>&1 || { STEP_MSG="写 evidence 临时文件失败: $out.tmp"; return 1; }
    # ⛔ 先判失败再写 rc 行（Codex r3 MEDIUM-2）：原版先写 `rc=0` 再 return 76,
    #    落盘的证据与进程返回码自相矛盾。
    if [ "$_sha_fail" = 1 ]; then
        # ⛔ 不用 `|| true`（Codex r4 MEDIUM-1，我 r3 引入的回归）：那会把「证据没发布出去」
        #    吞掉, 而消息仍宣称「证据已标 rc=76」。两种失败分开报。
        local _pub=1
        printf 'rc=76\n' >> "$out.tmp" || _pub=0
        [ "$_pub" = 1 ] && { mv "$out.tmp" "$out" || _pub=0; }
        if [ "$_pub" = 1 ]; then
            STEP_MSG="有文件 shasum 失败（见 SHASUM-FAILED 行）, 证据已标 rc=76: $out"
        else
            STEP_MSG="有文件 shasum 失败, 且证据**未能发布**（$out.tmp 残留或 mv 失败）, 报告不可信"
        fi
        return 1
    fi
    printf 'rc=0\n' >> "$out.tmp" || { STEP_MSG="追加 rc 行失败: $out.tmp"; return 1; }
    mv "$out.tmp" "$out" || { STEP_MSG="mv evidence 失败: $out"; return 1; }
    [ -s "$out" ] || { STEP_MSG="evidence 落盘后为空: $out"; return 1; }
    STEP_MSG="$out"
    return 0
}

# ── 主流程 ────────────────────────────────────────────────────────────────────
printf '📦 deploy-vault [%s] vault=%s port=%s hosts=%s\n' "$MODE" "$VAULT_NAME" "$PORT" "$HOSTS"
printf '   harness=%s\n' "$HARNESS"
# ⛔ 不在这里建 evidence 目录（Codex r1 BLOCKER-2）：它早于 preflight，
#    `--apply --evidence-dir "$HOME/.codex/x"` 会先把目录建出来、再被 71 拒 ——
#    返回码撤不回已经发生的写入。改为由**通过了 preflight 的**步骤按需自建。

run_step 1 preflight step1_preflight
run_step 2 install step2_install
run_step 3 postprocess step3_postprocess
run_step 4 verify step4_verify
run_step 5 activate step5_activate
run_step 6 evidence step6_evidence

printf '✅ rc=0（%s）\n' "$MODE"
exit 0
