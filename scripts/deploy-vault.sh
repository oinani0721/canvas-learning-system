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
# ═══ 禁写面（--vault / --evidence-dir / --env-dir 三者过同一份 realpath 判据）═══
#   live vault（$CLS_LIVE_VAULT，缺省见下）/ $HOME/Library / $HOME/.claude* / $HOME/.codex /
#   $HOME/.pi / $HOME/.gemini / $HOME/.deepcode / $HOME/.config/opencode / $HOME/.dsh /
#   路径中任何名为 .git 的段 / 自身是 *.env|.env|.env.* 文件。
#   判据对每个参数做**三种解释并列判定**，任一命中即拦（宁可多拦，不可漏拦）：
#     ① resolve_abs — 解软链；对尚不存在的尾部取最近存在祖先的物理路径再拼回剩余段
#        （不能因为 realpath 对缺失路径返回空就跳过检查 = 静默放行）
#     ② norm_path   — 折叠 `.` 与 `..`；只靠 ① 会漏 `$HOME/missing/../.codex/x`（missing
#        不存在 ⇒ `..` 一个字符都没动，而 mkdir -p 会解析它）
#     ③ 大小写归一后比较 — macOS/APFS 缺省大小写不敏感，`$HOME/.CODEX/x` 与 `.codex/x`
#        是同一个目录；在大小写敏感的文件系统上这会多拦，方向可接受
#   `$HOME/.claude*` 用**前缀规则**而不是 glob 枚举 —— 枚举只登记当下已存在的条目，
#   而要防的恰恰是「现在不存在、脚本正要去建」的那一类。
#
# ═══ 环境开关 ═══
#   CLS_MIN_SKILLS            preflight 要求的「含 SKILL.md 的 skill 目录数」下限，缺省 9。
#                             ⚠️ 现状恰 9 = 零余量：退役任一 skill 会让本判据 FAIL 71，而
#                             install-vault.sh:188 的 ≥8 仍绿 —— 两条判据会给出相反结论，
#                             退役 skill 时必须同步改两处。
#   CLS_DEPLOY_ALLOW_DOCKER_UP  **缺省 0 = 步 5 只跑 `config` 断言后 SKIP，不 `up -d`**。
#                             显式 =1 才真起容器（顶替现网容器不可逆 ⇒ opt-in，需用户当次授权）。
#   CLS_LIVE_VAULT            live vault 绝对路径（禁写面第一条），缺省为主仓 canvas-vault。
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

# 纯字符串折叠 `.` 与 `..`（Codex r1 BLOCKER-1）。
# 为什么需要它：`resolve_abs` 对**不存在**的尾部只做「剥到存在祖先 + 原样拼回」，
# `..` 一个字符都没动 —— `$HOME/missing/../.codex/probe`（missing 不存在）会原样返回，
# 与 `$HOME/.codex` 字符串不匹配 ⇒ 漏拦，而 `mkdir -p` 会解析 `..` 真写进 `.codex`。
# ⚠️ 只对不含软链的段安全, 故与 resolve_abs 的结果**并列判定**（见 is_forbidden）：
# 两种解释任一命中就拦。方向是**多拦**, 禁写面上宁可误拦不可漏拦。
norm_path() {
    local p="$1" out="" seg oldifs="$IFS"
    case "$p" in
        "~") p="$HOME" ;;
        "~/"*) p="$HOME/${p#\~/}" ;;
    esac
    case "$p" in
        /*) ;;
        *) p="$PWD/$p" ;;
    esac
    IFS='/'
    # shellcheck disable=SC2086
    set -- $p
    IFS="$oldifs"
    for seg in "$@"; do
        case "$seg" in
            '' | .) ;;
            ..) out="${out%/*}" ;;
            *) out="$out/$seg" ;;
        esac
    done
    printf '%s' "${out:-/}"
}

# 大小写归一（Codex r1 BLOCKER-1）。macOS/APFS 缺省**大小写不敏感**：
# `$HOME/.CODEX/probe` 与 `$HOME/.codex/probe` 是同一个目录, 但字符串不等 ⇒ 漏拦。
# 归一后比较会在大小写敏感的文件系统上**多拦**（两个真不同的目录被当成一个）——
# 禁写面上这个方向是可接受的, 反过来不可接受。
lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

declare -a FORBIDDEN=()
declare -a FORBIDDEN_PREFIX=()
build_forbidden() {
    FORBIDDEN=()
    FORBIDDEN_PREFIX=()
    local d
    FORBIDDEN+=("$(resolve_abs "$CLS_LIVE_VAULT")")
    FORBIDDEN+=("$(resolve_abs "$HOME/Library")")
    for d in .codex .pi .gemini .deepcode .dsh; do
        FORBIDDEN+=("$(resolve_abs "$HOME/$d")")
    done
    FORBIDDEN+=("$(resolve_abs "$HOME/.config/opencode")")
    # ⚠️ `$HOME/.claude*` 必须是**前缀规则**而不是 glob 枚举（Codex r1 BLOCKER-1）：
    # `for d in "$HOME"/.claude*` 只登记**当下已存在**的条目, 于是 `$HOME/.claude-new/probe`
    # 这种「现在还不存在、脚本正要去创建」的路径完全不在名单里 —— 而它恰好是要防的那一类。
    FORBIDDEN_PREFIX+=("$(resolve_abs "$HOME")/.claude")
}

# 返回 0 = 命中禁写面（拦），并把命中的那一条写进 FORBIDDEN_HIT
FORBIDDEN_HIT=""
_hits_one() {
    # $1 = 待判路径（已归一）, 其余不用。命中则设 FORBIDDEN_HIT 并返回 0。
    local cand="$1" lc t lt seg probe
    lc="$(lower "$cand")"

    # 自身是 env 文件
    case "$(basename "$cand")" in
        .env | *.env | .env.*) FORBIDDEN_HIT="*.env 文件（${cand}）"; return 0 ;;
    esac
    # 路径中任何一段名为 .git
    probe="$cand"
    while [ -n "$probe" ] && [ "$probe" != "/" ]; do
        seg="$(basename "$probe")"
        if [ "$seg" = ".git" ]; then
            FORBIDDEN_HIT=".git 目录内（${cand}）"
            return 0
        fi
        probe="$(dirname "$probe")"
    done
    # 等于或位于禁写目标之下（大小写归一比较, 见 lower()）
    for t in "${FORBIDDEN[@]}"; do
        [ -n "$t" ] || continue
        lt="$(lower "$t")"
        if [ "$lc" = "$lt" ] || [ "${lc#"$lt"/}" != "$lc" ]; then
            FORBIDDEN_HIT="$t"
            return 0
        fi
    done
    # 前缀规则（$HOME/.claude* 这一族, 含尚不存在的）
    for t in "${FORBIDDEN_PREFIX[@]}"; do
        [ -n "$t" ] || continue
        lt="$(lower "$t")"
        if [ "${lc#"$lt"}" != "$lc" ]; then
            FORBIDDEN_HIT="${t}*（前缀规则）"
            return 0
        fi
    done
    return 1
}

is_forbidden() {
    local raw="$1" a b
    FORBIDDEN_HIT=""
    # 两种解释**并列**判定, 任一命中即拦（Codex r1 BLOCKER-1）：
    #   a = resolve_abs：解软链, 但对不存在的尾部不折叠 `..`
    #   b = norm_path  ：折叠 `..`, 但不解软链
    # 只用 a 会漏 `$HOME/missing/../.codex/probe`；只用 b 会漏软链。
    # 两者都查 ⇒ 方向是多拦, 禁写面上可接受。
    a="$(resolve_abs "$raw")"
    _hits_one "$a" && return 0
    b="$(norm_path "$a")"
    if [ "$b" != "$a" ]; then
        _hits_one "$b" && return 0
    fi
    b="$(norm_path "$raw")"
    if [ "$b" != "$a" ]; then
        _hits_one "$b" && return 0
    fi
    return 1
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
case "$PORT" in
    '' | *[!0-9]*) die64 "--port 必须是数字: $PORT" ;;
esac
[ "$ACTIVATE" = 1 ] && [ "$APPLY" != 1 ] && die64 "--activate 只能与 --apply 同用"

# --hosts：本版只 claude（E-1）
IFS=',' read -r -a _hosts_arr <<< "$HOSTS"
for _h in "${_hosts_arr[@]}"; do
    _h="$(printf '%s' "$_h" | tr -d '[:space:]')"
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

VAULT_NAME="$(basename "$VAULT")"
[ -n "$SUBJECT" ] || SUBJECT="$VAULT_NAME"
[ -n "$EVIDENCE_DIR" ] || EVIDENCE_DIR="$HARNESS/_bmad-output/审查/evidence-deploy-$VAULT_NAME"
[ -n "$ENV_DIR" ] || ENV_DIR="$HARNESS"
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

    build_forbidden
    local pname praw
    for pname in --vault --evidence-dir --env-dir; do
        case "$pname" in
            --vault) praw="$VAULT" ;;
            --evidence-dir) praw="$EVIDENCE_DIR" ;;
            --env-dir) praw="$ENV_DIR" ;;
        esac
        if is_forbidden "$praw"; then
            STEP_MSG="禁写面: $pname 指向 $FORBIDDEN_HIT"
            return 1
        fi
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
        if grep -qE "^ACTIVE_VAULT=[\"']?${VAULT_NAME}[\"']?[[:space:]]*$" "$e" 2> /dev/null; then
            STEP_MSG="vault 名与 $(basename "$e") 的 ACTIVE_VAULT 碰撞"
            return 1
        fi
    done

    # 端口
    case "$PORT" in
        7691 | 7692 | 7478 | 11434)
            STEP_MSG="--port $PORT 与既有服务端口冲突（7691/7692 Neo4j, 7478 Browser, 11434 Ollama）"
            return 1
            ;;
    esac
    if command -v lsof > /dev/null 2>&1; then
        if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1; then
            STEP_MSG="--port $PORT 已被占用（lsof LISTEN 命中）"
            return 1
        fi
    fi

    # skills 数（零余量, 见头注 CLS_MIN_SKILLS）
    local nskills
    nskills="$(find "$HARNESS/canvas-vault/.claude/skills" -mindepth 2 -maxdepth 2 -type f -name SKILL.md 2> /dev/null | wc -l | tr -d ' ')"
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
        if ! (cd "$HARNESS/frontend/obsidian-plugin" && npm run build) > /dev/null 2>&1; then
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
    : > "$ENV_FILE.tmp" || { SEED_ERR="建 .env 临时文件失败: $ENV_FILE.tmp"; return 1; }
    printf '# CARD-G2-7b deploy-vault.sh 生成 — vault=%s port=%s ts=%s\n' "$VAULT_NAME" "$PORT" "$TS" >> "$ENV_FILE.tmp"
    ENV_KEYS_SKIPPED=""
    for k in $ENV_KEYS_WHITELIST; do
        if [ -f "$src" ] && v="$(grep -E "^${k}=" "$src" 2> /dev/null | tail -1)"; then
            [ -n "$v" ] && printf '%s\n' "$v" >> "$ENV_FILE.tmp" && continue
        fi
        ENV_KEYS_SKIPPED="$ENV_KEYS_SKIPPED $k"
    done
    {
        printf 'ACTIVE_VAULT=%s\n' "$VAULT_NAME"
        printf 'VAULTS_ROOT=%s\n' "$(dirname "$VAULT")"
        printf 'API_PORT=%s\n' "$PORT"
        printf 'CLS_BACKEND_CONTAINER=cls-%s-backend\n' "$VAULT_NAME"
        printf 'INTERNAL_API_KEY=\n'
        printf 'DAILY_REVIEW_VAULTS=\n'
    } >> "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE" || { SEED_ERR="mv .env 失败: $ENV_FILE"; return 1; }
    chmod 600 "$ENV_FILE" || { SEED_ERR="chmod 600 .env 失败: $ENV_FILE"; return 1; }
    return 0
}

step2_install() {
    local cmd="$HARNESS/scripts/install-vault.sh $VAULT_NAME --subject $SUBJECT"
    cmd="$cmd --vaults-root $(dirname "$VAULT") --source $HARNESS/canvas-vault"
    cmd="$cmd --env-file $ENV_FILE --harness-tree $HARNESS --backend-url http://127.0.0.1:$PORT"
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
    : > "$ilog" || { STEP_MSG="无法写 install 日志(重定向失败, install 未执行): $ilog"; return 1; }
    local irc=0
    CLS_REPO="$HARNESS" "$HARNESS/scripts/install-vault.sh" "$VAULT_NAME" \
        --subject "$SUBJECT" --vaults-root "$(dirname "$VAULT")" \
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
        local want_pairs="API_PORT=$PORT ACTIVE_VAULT=$VAULT_NAME CLS_BACKEND_CONTAINER=cls-$VAULT_NAME-backend"
        local kv k v have
        for kv in $want_pairs; do
            k="${kv%%=*}"
            v="${kv#*=}"
            have="$(grep -E "^${k}=" "$ENV_FILE" 2> /dev/null | tail -1 | cut -d= -f2- | tr -d '"'"'" | tr -d '\r')"
            if [ -n "$have" ] && [ "$have" != "$v" ]; then
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
        local left=""
        for rel in $PORT_TEMPLATED_FILES; do
            grep -q ':8011' "$VAULT/$rel" 2> /dev/null && left="$left $rel"
        done
        grep -q ':8011' "$datajson" 2> /dev/null && left="$left data.json"
        if [ -n "$left" ]; then
            STEP_MSG="模板化后仍有 :8011 残留:$left"
            return 1
        fi
    fi

    # B3 插件 data.json internalApiKey 同值（只改这一键）
    if ! python3 - "$datajson" "$key" << 'PY'; then
import json, sys
p, key = sys.argv[1], sys.argv[2]
d = json.load(open(p, encoding="utf-8"))
d["internalApiKey"] = key
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(p, "a", encoding="utf-8").write("\n")
PY
        STEP_MSG="写 data.json internalApiKey 失败"
        return 1
    fi

    # B4 .env.<vault> 的 INTERNAL_API_KEY 同值
    if ! python3 - "$ENV_FILE" "$key" << 'PY'; then
import sys
p, key = sys.argv[1], sys.argv[2]
lines = open(p, encoding="utf-8").read().split("\n")
out, done = [], False
for l in lines:
    if l.startswith("INTERNAL_API_KEY="):
        out.append(f"INTERNAL_API_KEY={key}")
        done = True
    else:
        out.append(l)
if not done:
    out.append(f"INTERNAL_API_KEY={key}")
open(p, "w", encoding="utf-8").write("\n".join(out))
PY
        STEP_MSG="写 $ENV_FILE 的 INTERNAL_API_KEY 失败"
        return 1
    fi
    chmod 600 "$ENV_FILE" || { STEP_MSG="chmod 600 失败: $ENV_FILE"; return 1; }

    # B5 key **文件**落盘 —— 最后一步。A4 已确定值; 已存在则不重写、只校正权限。
    # 为什么最后：「key 文件存在」是 A4 判「不重生」的锚点。若它先落盘而后续两处失败，
    # 下次重跑会读到它、不重生, 而另两处仍旧空 —— 半成品被这个最强信号掩盖。放最后则
    # 前面任何失败都不会留下这个信号（如实声明：Phase B 内部失败仍可能留半成品，
    # 方向是「另两处有值、key 文件缺」, 重跑会重生并覆盖两处 ⇒ 自愈）。
    if [ "$KEY_REGENERATED" = "yes" ]; then
        mkdir -p "$(dirname "$keyfile")" || { STEP_MSG="建 key 文件父目录失败"; return 1; }
        # 原子落盘：先写 tmp（umask 077）→ 回读比对 → mv。中途失败不会留下**部分内容的**
        # key 文件, 而「key 文件存在」正是 A4 判「不重生」的锚点 —— 半个 key 比没有 key 更坏。
        (umask 077 && printf '%s\n' "$key" > "$keyfile.tmp") \
            || { STEP_MSG="写 key 临时文件失败"; return 1; }
        if [ "$(cat "$keyfile.tmp")" != "$key" ]; then
            rm -f -- "$keyfile.tmp"
            STEP_MSG="key 临时文件回读不一致, 已丢弃（未污染 ${keyfile}）"
            return 1
        fi
        mv "$keyfile.tmp" "$keyfile" || { STEP_MSG="mv key 文件失败"; return 1; }
    fi
    chmod 600 "$keyfile" || { STEP_MSG="chmod 600 key 文件失败"; return 1; }

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
        SRC_MIRROR="$(mktemp -d "${TMPDIR:-/tmp}/cls-srcmirror-XXXXXX")" || {
            STEP_MSG="建源镜像临时目录失败"
            return 1
        }
        if ! cp -R "$HARNESS/canvas-vault/." "$SRC_MIRROR/" 2> /dev/null; then
            STEP_MSG="镜像源失败: $SRC_MIRROR"
            return 1
        fi
        for t in $PORT_TEMPLATED_FILES; do
            if [ -f "$SRC_MIRROR/$t" ]; then
                sed -i '' "s|:8011|:$PORT|g" "$SRC_MIRROR/$t" || {
                    STEP_MSG="源镜像模板化失败: $t"
                    return 1
                }
            fi
        done
        src="$SRC_MIRROR"
        basis="源镜像(同 :$PORT 口径)"
    fi

    local rep="$EVIDENCE_DIR/verify-$TS.txt" rc=0
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
    mkdir -p "$EVIDENCE_DIR"
    # ⛔ `docker compose config` 会把 --env-file 与宿主 env 里的凭据**展开成明文**
    #    （INTERNAL_API_KEY / GOOGLE_API_KEY / NEO4J_PASSWORD / NEO4J_AUTH / …）。
    #    原样落盘 = 把密钥写进 evidence 目录, 而 evidence 是要入库的。
    #    故落盘前脱敏; 断言只看 container_name 与 ports, 不需要那些值 ——
    #    明文因此**从不落盘**（不是「落了再擦」）。
    local cfg="$EVIDENCE_DIR/compose-config-$TS.txt" rc=0
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
    local out="$EVIDENCE_DIR/deploy-$TS.txt" t
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
                printf '  %s  %s\n' "$(shasum -a 256 "$t" | cut -d' ' -f1)" "${t#"$VAULT"/}"
            else
                printf '  %-64s %s (ABSENT)\n' '-' "${t#"$VAULT"/}"
            fi
        done
    } > "$out.tmp" 2>&1 || { STEP_MSG="写 evidence 临时文件失败: $out.tmp"; return 1; }
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
