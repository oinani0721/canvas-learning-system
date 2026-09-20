#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# j01_e2e.sh — J01「新 vault bootstrap」黑盒 E2E harness
# [BATCH-2026-09-18-第十五批 / CARD-G2-11]
#
# 一次性 throwaway vault 走 deploy-vault.sh 的 G2-8 六步
# (preflight → install → postprocess → verify → activate → evidence)，
# 外加隔离预检 (compose 共享面) / 首索引 / 新笔记经 search_notes 真检回 /
# DELETE /index/{vault} 表清单回零 / rollback-down / 状态 diff=0，
# 并断言「无旧 secret」「无绝对路径」。证据自绑 HEAD。
#
# ⛔ 本脚本**只调用**既有脚本，零改动 deploy-vault.sh / install-vault.sh /
#    verify_vault_install.py / docker-compose.yml。
#
# ═══ 子命令 ═══
#   run  [--mode fixture|live] [--allow-up] [--harness DIR] [--port N]
#        [--evidence-dir DIR] [--keep-root]
#   scan <DIR> [--ref-env FILE]... [--source-baseline DIR]
#        独立可调的 secret / 绝对路径扫描器（供负控与 run 复用；同一实现，
#        空 baseline 是它的退化输入，不是第二份实现）。
#   isolation-check <compose-config.yml>
#        对任意一份 compose config 跑隔离预检（与 run --mode live 同一函数）。
#        存在的理由是**验伪锚**：门必须能在「已隔离」的配置上变绿、在现网配置
#        上变红。⛔ 它自己也必须先证输入面非空 —— 一道「没东西可看就放行」的门
#        和一道恒红的门一样没用（见 isolation_preflight 的输入面断言）。
#
# ═══ 断言 rc 约定（三态，日志头也会打印一遍）═══
#   rc=0 通过 / rc=1 失败（红，整跑 rc 非 0）/ rc=2 跳过（不红，必带 reason=）
#   ⛔ 所有「数命中数，0 命中即绿」的判据，都必须先断言**输入面非空**，否则
#      「没跑成」与「真的干净」是同一个数字。
#
# ═══ 13 条断言（少一条即该次运行作废，收尾自检比身份集合 + 计数）═══
#   throwaway-outside-protected  deploy-rc   verify-rc   no-old-secret
#   no-abs-path   isolation-preflight   backend-ready   first-index
#   search-hit    table-diff            rollback-down   state-diff
#   evidence-redacted
#
# ═══ 进程 rc ═══
#   0 全部断言 rc ∈ {0,2}  /  1 有断言 rc=1 或收尾自检不过  /  64 用法错
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── 常量 ───────────────────────────────────────────────────────────────────
# 13 条断言的**权威顺序表**。收尾拿它与实际 emit 过的集合比对：既比身份集合
# （挡得住拼错 / 漏写），也比计数（挡得住同一条 emit 两次 —— 集合相等对重复
# 是盲的：重复项两边都在，差集都空）。
ASSERT_ORDER="throwaway-outside-protected deploy-rc verify-rc no-old-secret no-abs-path isolation-preflight backend-ready first-index search-hit table-diff rollback-down state-diff evidence-redacted"
ASSERT_EXPECTED_N=13

# 绝对路径针：macOS 家目录前缀。⚠️ 不含 Linux 的 /home/ —— 本机只有 macOS 可
# 实测，写进来而不实测等于加一条没验过的门（「未证明」已登记该缺口）。
J01_ABS_NEEDLE="/Users/"

# no-abs-path 的唯一白名单：**vault 根**的 .canvas-config.yaml，且只放行设计
# 写入的那两个键所在的行。⛔ 不按 basename 放行 —— basename 不带目录也不带深度，
# 任意子目录里同名的文件都会被放行；也不放行该文件里**别的**键。
J01_ABS_WHITELIST_RELPATH=".canvas-config.yaml"
J01_ABS_WHITELIST_KEYS="harness_tree backend_url"

# --port 黑名单（与 deploy-vault.sh:817 同口径）。下面出现的每一个 7691/7692/
# 7478/7687 都是**拒绝值**，没有一个是连接目标。比较前先做十进制归一，
# 否则 `--port 07691` 这种字符串不等、数值相等的输入会被放过去。
J01_FORBIDDEN_API_PORTS="7691 7692 7478 11434"
# 隔离预检里 neo4j 的 published 端口**拒绝集合**：撞上任何一个 = 与现网抢口。
J01_FORBIDDEN_PUBLISHED_PORTS="7691 7692 7478 7687 11434"
# 隔离预检拒绝的现网固定名。
J01_FORBIDDEN_NEO4J_CONTAINER="canvas-learning-system-neo4j"
J01_FORBIDDEN_NETWORK_NAME="canvas-learning-network"
# 参照 env 里长度 < 该值的值不参与「明文出现在证据里」的比对（避免 "1"/"true"
# 这类短值造成海量假阳）。
J01_SECRET_MIN_LEN=12
# deploy-vault.sh:972 的 ENV_KEYS_WHITELIST —— 这五个键是**设计上要从 harness .env
# 原样抄进实例 .env** 的（端口 / ollama 地址 / 挂载模式）。它们与参照 env 同值是
# 正确行为，不是「旧密钥复用」。⛔ 不排除它们，`no-old-secret` 会在任何**有**树根
# .env 的树上恒红（本车道恰好没有树根 .env 才没暴露）。
# 除白名单五键外，deploy 还会**自己算出**六个固定键（:1040-1046）。其中
# ACTIVE_VAULT / VAULTS_ROOT / API_PORT / CLS_BACKEND_CONTAINER / DAILY_REVIEW_VAULTS
# 是实例绑定信息，与参照 env 同值是正常的（例如两边都用 8187 这个空闲端口），
# 不是「旧密钥复用」。⛔ INTERNAL_API_KEY **不在**这个排除集合里 —— 它恰恰是
# 本判据要盯的那一个。
J01_DEPLOY_COPY_KEYS="NEO4J_HTTP_PORT NEO4J_BOLT_PORT OLLAMA_HOST VAULT_MOUNT_MODE LOCAL_EMBEDDER_BASE_URL ACTIVE_VAULT VAULTS_ROOT API_PORT CLS_BACKEND_CONTAINER DAILY_REVIEW_VAULTS"

# ── 全局状态 ───────────────────────────────────────────────────────────────
MODE="fixture"
ALLOW_UP=0
HARNESS=""
PORT=8187
EVDIR=""
KEEP_ROOT=0
ROOT=""
LOG=""
TS=""
VAULT_NAME=""
VAULT=""
ENV_FILE=""
DEPLOY_EV=""
EMITTED=""          # 已 emit 的 assert id，空格分隔
EMITTED_N=0
FAILED_N=0
SKIPPED_N=0
SCAN_REF_ENVS=""    # 换行分隔的参照 env 路径
SCAN_BASELINE=""
SCAN_LAST_RC=0
THROWAWAY_OK=0
ROOT_ID=""          # mktemp 刚建出来时的 (st_dev, st_ino)，拆除前据此核身份
UP_ATTEMPTED=0      # 是否真的尝试过 up（决定拆除要不要查容器）
GUARD_VERDICT=""
GUARD_RR=""
GUARD_RTMP=""
GUARD_MREPO=""
GUARD_NBL=0
ISOLATION_RC=1
RUN_ID=""
EV_STAGED=0
EV_BAD=0
EV_INSPECTED=0
EV_DEP_N=0
EV_DEP_RC=0
EV_INST_KEY=""
SNAPSHOT_OK_N=0
SNAPSHOT_BAD_N=0
DOCKER_PROJECTS_BEFORE="<not-captured>"
LANCE_TIMEOUT=120

# ⛔ 继承来的 CLS_DEPLOY_ALLOW_DOCKER_UP 一进门就**摘掉**，只留一个只读副本。
#    这样即便调用者 export 了 =1，下面预检那一趟 deploy 也一定在「无该 env」
#    下跑（`env -u` 再兜一层），不会有任何一条路径靠 env 泄入把 up 起起来。
USER_ALLOW_UP_ENV="${CLS_DEPLOY_ALLOW_DOCKER_UP:-0}"
unset CLS_DEPLOY_ALLOW_DOCKER_UP || :

# ── 基础工具 ───────────────────────────────────────────────────────────────
log() {
    # 双写：stdout 给调用者看，LOG 是入库证据。LOG 未就绪时只走 stdout。
    if [ -n "$LOG" ]; then
        printf '%s\n' "$*" | tee -a "$LOG"
    else
        printf '%s\n' "$*"
    fi
}

die() {
    printf 'j01_e2e: %s\n' "$*" >&2
    exit 64
}

# need_val <flag> <剩余参数个数> —— `shift 2` 在只剩一个参数时返回非 0，
# `set -e` 下会**当场杀掉脚本**（rc=1、还没走到 die），用法错就报不出 64 了。
need_val() {
    [ "$2" -ge 2 ] || die "$1 需要一个值"
}

# emit_assert <id> <rc> [reason]
# ⛔ rc **必须由调用方先捕获再传进来**（`rc=0; cmd || rc=$?`）。断言函数自身
#    恒 return 0 —— 否则 `set -e` 会在「预期会红的断言」处直接杀掉脚本，
#    后面的断言与拆除都不执行，日志里 assert 行数不足 13、$ROOT 还会残留。
emit_assert() {
    local id="$1" rc="$2" reason="${3:-}"
    case " $EMITTED " in
        *" $id "*) log "# WARN 断言 $id 重复 emit（收尾自检按计数会抓到）" ;;
    esac
    EMITTED="$EMITTED $id"
    EMITTED_N=$((EMITTED_N + 1))
    # rc 归一到三态：被调方的原始退出码（如 deploy 的 71..76）必须进 reason，
    # 不能直接当 assert 的 rc —— 否则日志里出现文档里没有的第四、第五种 rc。
    case "$rc" in
        0) : ;;
        2) SKIPPED_N=$((SKIPPED_N + 1)) ;;
        1) FAILED_N=$((FAILED_N + 1)) ;;
        *)
            reason="${reason:+$reason }raw-rc=$rc"
            rc=1
            FAILED_N=$((FAILED_N + 1))
            ;;
    esac
    if [ "$rc" = 2 ] && [ -z "$reason" ]; then
        # 跳过而不说为什么 = 隐含前提。宁可自打成红。
        reason="MISSING-REASON-treated-as-red"
        rc=1
        FAILED_N=$((FAILED_N + 1))
        SKIPPED_N=$((SKIPPED_N - 1))
    fi
    if [ -n "$reason" ]; then
        log "assert=$id rc=$rc reason=$reason"
    else
        log "assert=$id rc=$rc"
    fi
    return 0
}

step() { log "step=$1 rc=$2"; }

py() { "$HARNESS/backend/.venv/bin/python" "$@"; }

sha_file() {
    # 只回 64 位 hex，不回文件名（密钥件的名字也不必进日志）。
    shasum -a 256 "$1" 2> /dev/null | awk '{print $1}'
}

sha_stdin() { shasum -a 256 | awk '{print $1}'; }

# dequote —— 去掉成对包裹的引号。⛔ 引号是 shell/compose 的语法，不是密钥的一部分：
# 参照里写 `OLD="abc"`、实例里写 `NEW=abc`，两者 sha 不同但**是同一个密钥**。
dequote() {
    case "$1" in
        '"'*'"') printf '%s' "$1" | sed -E 's/^"(.*)"$/\1/' ;;
        "'"*"'") printf '%s' "$1" | sed -E "s/^'(.*)'\$/\1/" ;;
        *) printf '%s' "$1" ;;
    esac
}

# env_kv_of <file> —— 逐行吐 `键=值`；值若被成对引号包着，**额外再吐一份去引号的**。
# 下游按值比 sha 时两种写法因此等价。
env_kv_of() {
    local line k v d
    # ⛔ 几个静默漏检一起堵：
    #   ① 文件**末行没有换行符**时会被 sed 吞掉（那行恰恰常是最后加的那个键）；
    #   ② CRLF 的 `\r` 会留在值尾，与 LF 侧的同一个密钥 sha 不同；
    #   ③ `export KEY=v` 前缀、`KEY = v` 的空白、`KEY=v  # 注释` 的行内注释、
    #      尾随空白 —— 都是 .env 的合法写法，但会让「同一个密钥」算出不同的 sha。
    #   归一后**既吐原样也吐归一形式**，两边怎么写都能对上。
    { cat "$1" 2> /dev/null; printf '\n'; } | tr -d '\r' \
        | sed -n -E 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$/\2=\3/p' \
        | while IFS= read -r line; do
            k="${line%%=*}"
            v="${line#*=}"
            [ -n "$v" ] || continue
            printf '%s=%s\n' "$k" "$v"
            # 去尾随空白
            d="$(printf '%s' "$v" | sed -E 's/[[:space:]]+$//')"
            # ⛔ 只在**引号外**认行内注释。
            #    `PASSWORD="same # secret" # real comment` 这一行：整值既不是
            #    「首尾都是引号」也不是「没有引号」，上一版的两分支写法把它从第一个
            #    ` #` 截成了 `"same` —— 归一本身变成了新的漏检面。
            #    正确做法：值以引号开头时，取到**第一个闭合引号**为止，之后一律是注释。
            case "$d" in
                '"'*) d="$(printf '%s' "$d" | sed -E 's/^("[^"]*").*$/\1/')" ;;
                "'"*) d="$(printf '%s' "$d" | sed -E "s/^('[^']*').*\$/\1/")" ;;
                *' #'*) d="$(printf '%s' "$d" | sed -E 's/[[:space:]]+#.*$//')" ;;
            esac
            [ -z "$d" ] || [ "$d" = "$v" ] || printf '%s=%s\n' "$k" "$d"
            # 去成对引号
            local dq
            dq="$(dequote "$d")"
            [ -z "$dq" ] || [ "$dq" = "$d" ] || printf '%s=%s\n' "$k" "$dq"
        done
}

# is_sensitive_key —— 键名形态上就是密钥的，**任何长度**都不许在证据里出现明文。
# （长度下限只是为了挡 "1"/"true" 这类短值的海量假阳，不该把 9 位的真密码也放过。）
is_sensitive_key() {
    # ⛔ 大小写归一后再比：`password=abc` / `Api_Token=…` 这类小写或混合大小写的键名
    #    原先完全不命中（.env 里大写是惯例不是规则）。
    local u
    u="$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')"
    case "$u" in
        *KEY* | *TOKEN* | *SECRET* | *PASSWORD* | *PASSWD* | *AUTH* | *CREDENTIAL* | *PRIVATE*) return 0 ;;
    esac
    return 1
}

# looks_like_secret —— 键名不敏感时的兜底：只有「看起来像高熵令牌」的值才查明文。
# ⛔ 不能对参照 env 里**所有**值都查：`VAULTS_ROOT` / `ACTIVE_VAULT` 这类路径和名字
#    本来就该出现在部署证据里（证据的用处正在于此），按「只要出现就判红」会把
#    判据变成恒红 —— 判据范围必须恰好等于它的主张（这里的主张是「没有**密钥**明文」）。
looks_like_secret() {
    case "$1" in
        # ⛔ 带 userinfo 的 URL（`scheme://user:pass@host`）**本身就装着凭据**，
        #    必须查。原先「凡 URL 一律跳过」把这一类整个放过了。
        *://*@*) return 0 ;;
        # URL 的 query 里挂令牌同样是明文凭据（`?token=…` / `&api_key=…`）
        *'?'*[Tt][Oo][Kk][Ee][Nn]=* | *'&'*[Tt][Oo][Kk][Ee][Nn]=*) return 0 ;;
        *'?'*[Kk][Ee][Yy]=* | *'&'*[Kk][Ee][Yy]=*) return 0 ;;
        *'?'*[Ss][Ii][Gg]*=* | *'&'*[Ss][Ii][Gg]*=*) return 0 ;;
        /*) return 1 ;;                       # 绝对路径
        *://*) return 1 ;;                    # 不带凭据、query 里也没有令牌的普通 URL
        *" "*) return 1 ;;                    # 含空格
        *[!A-Za-z0-9+/=_.:-]*) return 1 ;;    # 含令牌里不会有的字符
    esac
    [ "${#1}" -ge 16 ] || return 1
    return 0
}

# 大小写归一：macOS 缺省是大小写不敏感 FS，`/Tmp/x` 与 `/tmp/x` 是同一个对象，
# 按原样比前缀会漏判。
lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

# 十进制归一：`07691` 与 `7691` 字符串不等但是同一个端口。非纯数字回空串，
# 调用方按「问不出来」处理（fail-closed），不当成 0。
num_of() {
    case "$1" in
        '' | *[!0-9]*) printf '' ;;
        *) printf '%d' "$((10#$1))" ;;
    esac
}

# realpath：解掉全部软链（中间段也解），路径不存在时回空串。
real_of() {
    py -c 'import os,sys
try:
    print(os.path.realpath(sys.argv[1]))
except Exception:
    print("")' "$1" 2> /dev/null || printf ''
}

# is_under <child> <parent> — 前缀比较**必带分隔符**：否则 /a/b 会被判成在
# /a/bc 之内（与 group_id 前缀 `vault__a` 吃掉 `vault__ab` 同型）。
is_under() {
    local c p
    c="$(lower "$1")"
    p="$(lower "$2")"
    [ -n "$c" ] && [ -n "$p" ] || return 1
    case "$c/" in
        "$p"/*) return 0 ;;
    esac
    return 1
}

# path_identity <path> —— "dev:ino"，问不出来回空串。路径是**名字**，inode 才是
# **对象**：名字可以在两次检查之间被指到别的对象上（软链改指 / 目录被换掉）。
path_identity() {
    py -c 'import os,sys
try:
    st = os.stat(sys.argv[1])
    print("%d:%d" % (st.st_dev, st.st_ino))
except Exception:
    print("")' "$1" 2> /dev/null || printf ''
}

# 主仓根：worktree 里 `rev-parse --show-toplevel` 回的是**本 worktree**，
# 不是主仓；而 docker-compose.yml 的 neo4j bind 是写死的**主仓**绝对路径。
# 只用 show-toplevel 去比前缀 ⇒ 那几条 mount 永远匹配不上（门看着在、其实不判）。
main_repo_root() {
    local gcd
    gcd="$(git -C "$HARNESS" rev-parse --path-format=absolute --git-common-dir 2> /dev/null || printf '')"
    [ -n "$gcd" ] || { printf ''; return 0; }
    real_of "${gcd%/.git}"
}

# is_binary <file> — 前 64KiB 里有没有 NUL。
# ⛔ 不用 `grep -q $'\x00'`：shell 传不了 NUL 参数，模式会塌成**空串**从而
#    匹配一切（实测把 34/34 个文本文件全判成二进制）。改为「删掉 NUL 后长度
#    是否变短」——这个判据不经过 shell 的参数层。
is_binary() {
    local a b
    a="$(head -c 65536 "$1" 2> /dev/null | wc -c | tr -d ' ')"
    b="$(head -c 65536 "$1" 2> /dev/null | LC_ALL=C tr -d '\000' | wc -c | tr -d ' ')"
    [ "$a" != "$b" ]
}

# ── 扫描器（no-old-secret / no-abs-path 的唯一实现）────────────────────────
# scan_tree <secret_dir> <abs_dir>
#   读全局 SCAN_REF_ENVS（换行分隔的参照 env）与 SCAN_BASELINE（模板源根，可空）。
#   emit 两条断言；把整体红/绿写进 SCAN_LAST_RC。
#   run 与 scan 子命令共用本函数 —— baseline 为空只是它的退化输入，不是
#   第二份实现（两份手抄清单必然漂移）。
#   ⛔ 两个范围分开传是**有意**的：
#     secret_dir = ${ROOT}（要含 env/，实例 .env 就落在那）；
#     abs_dir    = ${VAULT}（**只**是装出来的库）。deploy 自己的证据文件
#     （ev/deploy-*.txt 等）本来就该记录 vault/harness 的绝对路径，那是诊断
#     产物不是交付物，把它算进 no-abs-path 会制造假红（实测三条）。
#   scan 子命令两参同值 ⇒ 退化成单目录口径。
scan_tree() {
    local dir="$1"
    local absdir="${2:-$1}"
    local rc_secret=0 rc_abs=0
    local reason_secret="" reason_abs=""

    # ── ① no-old-secret ────────────────────────────────────────────────
    # 参照集合 = 各参照 env 文件里**所有键的所有值**的 sha256。
    # 比「≠ 同名键 INTERNAL_API_KEY」强：能抓「把 NEO4J_PASSWORD 拿来当
    # internal key 复用」这类换了键名的旧密钥。
    local refsha n_ref=0 refcount
    refsha="$(mktemp "${TMPDIR:-/tmp}/j01refsha-XXXXXX")"
    # ⛔ 参照清单**只按整行读一次**。原先第二个循环用 `for f in $(… tr '\n' ' ')`
    #    走未加引号的命令替换（IFS 词分割 + 路径名展开），同一份清单被两种口径
    #    读了两遍：含空格的路径在此处被切碎 ⇒ n_ref=0 而 refcount≠0 ⇒ 日志自曝
    #    矛盾「参照 env 文件数=0 参照值 sha 数=1」并误触 fail-closed。
    local f refbad=0
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        [ -f "$f" ] || continue
        n_ref=$((n_ref + 1))
        # 参照文件读不动 ⇒ 参照面**不完整**：另一个可读的参照会让计数非零，
        # 而真正藏着旧密钥的那个从未被读过。计红，不让部分参照冒充完整参照。
        if [ ! -r "$f" ]; then
            refbad=$((refbad + 1))
            log "# scan: 参照 env 不可读（参照面不完整）: ${f##*/}"
            continue
        fi
        # 值只进 sha，绝不进日志、绝不进变量之外的任何落盘面。
        env_kv_of "$f" | while IFS= read -r kv; do
            printf '%s' "${kv#*=}" | sha_stdin
        done >> "$refsha"
    done << EOF
$SCAN_REF_ENVS
EOF
    refcount="$(wc -l < "$refsha" | tr -d ' ')"
    log "# scan: 参照 env 文件数=$n_ref 参照值 sha 数=$refcount baseline=${SCAN_BASELINE:-<none>}"

    if [ "${refbad:-0}" != 0 ]; then
        rc_secret=1
        reason_secret="reference-env-unreadable=$refbad(partial-reference-surface)"
    elif [ "$n_ref" = 0 ] || [ "$refcount" = 0 ]; then
        # ⛔ fail-closed：参照面为空时「新 key 与旧 key 不同」这句话无从证明，
        #    绿在这里就是空洞通过（期望「不相等」的判据必须先证参照面非空）。
        rc_secret=1
        reason_secret="no-reference-env-value-found(fail-closed)"
    fi

    # 待查的 env 形态文件：dir 下一切 .env / .env.* 命名者。
    # ⛔ 用 heredoc + read 走整行，不用 `for x in $(find …)`：后者做 IFS 词分割
    #    与路径名展开，含空格/中文的路径会被切成不存在的片段 ⇒ 下游 grep/sed
    #    全部落空 ⇒ 计数恒 0 ⇒ 判据**绿在什么都没扫**上。
    local envf hit_reuse=0 n_env=0 badkey=0 unreadable=0 envlist elrc=0 badlink=0 skipped_wl=0
    envlist="$(mktemp "${TMPDIR:-/tmp}/j01envlist-XXXXXX")"
    # ⛔ find 的 rc 必须接住：枚举失败（子目录不可遍历）时「没找到」与「没去看」
    #    是同一个空列表。也把 `-type l` 收进来 —— 一个指向别处的 `.env` 软链
    #    原本被 `-type f` 整个排除，等于把旧密钥藏在链后面就不会被扫到。
    find "$dir" \( -type f -o -type l \) \( -name '.env' -o -name '.env.*' \) 2> /dev/null \
        | sort > "$envlist" || elrc=$?
    if [ "$elrc" != 0 ]; then
        unreadable=$((unreadable + 1))
        log "# scan: env 枚举失败（find rc=${elrc}）⇒ 不敢断言扫全了"
    fi
    while IFS= read -r envf; do
        [ -n "$envf" ] || continue
        n_env=$((n_env + 1))
        if [ -L "$envf" ]; then
            # 一次性 vault 的 .env 不该是软链：它意味着真正的内容在别处，
            # 本扫描器看到的只是链本身。计红而不是跟随。
            badlink=$((badlink + 1))
            log "# scan: env 形态文件是软链（内容在别处, 判红）: ${envf##*/} -> $(readlink "$envf" 2> /dev/null)"
            continue
        fi
        # ⛔ 禁带键名要查**归一后**的键名：`export OPENAI_API_KEY=x` / `KEY = x`
        #    都是合法 .env 写法，原来的行首正则一个都不匹配。
        local grc=0 bk
        grc=1
        while IFS= read -r bk; do
            [ -n "$bk" ] || continue
            case "${bk%%=*}" in
                GOOGLE_API_KEY | GEMINI_API_KEY | OPENAI_API_KEY | NEO4J_PASSWORD | NEO4J_AUTH | ANTHROPIC_API_KEY)
                    grc=0 ;;
            esac
        done << EOFBK
$(env_kv_of "$envf")
EOFBK
        if [ ! -r "$envf" ]; then grc=2; fi
        if [ "$grc" = 0 ]; then
            badkey=$((badkey + 1))
            log "# scan: 禁带键名出现在 ${envf##*/}"
        elif [ "$grc" -gt 1 ]; then
            # rc>1 = 读不动，不是「没有该键」。两者塌成一个分支就等于
            # 「文件读不了 ⇒ 判它干净」。
            unreadable=$((unreadable + 1))
            log "# scan: 读不动（grep rc=${grc}）: ${envf##*/}"
        fi
        if [ "$refcount" != 0 ]; then
            local kv s tk wk
            while IFS= read -r kv; do
                [ -n "$kv" ] || continue
                tk="${kv%%=*}"
                # deploy 设计要抄的键：同值是正确行为，跳过并计数（不静默）
                for wk in $J01_DEPLOY_COPY_KEYS; do
                    if [ "$tk" = "$wk" ]; then
                        skipped_wl=$((skipped_wl + 1))
                        continue 2
                    fi
                done
                s="$(printf '%s' "${kv#*=}" | sha_stdin)"
                if grep -qxF "$s" "$refsha"; then
                    hit_reuse=$((hit_reuse + 1))
                    log "# scan: ${envf##*/} 内某键 ${tk} 的值 sha=${s} 与参照 env 的某个值相同（值不打印）"
                fi
            done << EOF2
$(env_kv_of "$envf")
EOF2
        fi
    done < "$envlist"
    rm -f "$refsha" "$envlist"
    log "# scan: env 形态文件数=$n_env 旧值复用命中=$hit_reuse 禁带键名文件数=$badkey 软链 env=$badlink 读不动=$unreadable deploy 白名单键跳过=${skipped_wl:-0}"
    if [ "$n_env" = 0 ] && [ "$rc_secret" = 0 ]; then
        # ⛔ 输入面为空 ⇒ 不许绿：「一个 env 文件都没查」与「查了都干净」在
        #    命中数上是同一个 0。J01 要证的恰恰是新实例的 .env 是干净的，
        #    没有 .env 可查时这句话没有内容。
        rc_secret=1
        reason_secret="no-env-file-examined(empty-input-surface)"
    elif [ "$unreadable" != 0 ] && [ "$rc_secret" = 0 ]; then
        rc_secret=1
        reason_secret="unreadable-env-files=$unreadable"
    elif [ "$badlink" != 0 ] && [ "$rc_secret" = 0 ]; then
        rc_secret=1
        reason_secret="env-file-is-symlink=$badlink"
    elif [ "$hit_reuse" != 0 ]; then
        rc_secret=1
        reason_secret="old-secret-value-reused-count=$hit_reuse"
    elif [ "$badkey" != 0 ]; then
        rc_secret=1
        reason_secret="forbidden-key-name-present-count=$badkey"
    fi
    emit_assert no-old-secret "$rc_secret" "$reason_secret"

    # ── ② no-abs-path ──────────────────────────────────────────────────
    # 命中分两类：
    #   inherited — 整文件 sha256 与 <baseline>/<相对路径> 逐字节相同 ⇒ 是模板
    #               源里本来就有的字面量，不是这次部署烤进去的。计数 + 逐条列，
    #               不判红；有人事后改过该文件 ⇒ sha 变 ⇒ 立刻归 new 判红。
    #   new       — 其余一切 ⇒ 判红。
    local n_files=0 n_scanned=0 n_link=0 n_link_hit=0 n_bin=0 n_wl=0 n_inherit=0 n_new=0 n_unread=0
    local rel bl ff l
    log "# scan: abs 扫描范围=${absdir}（secret 扫描范围=${dir}）"

    local linklist filelist llrc=0 flrc=0
    linklist="$(mktemp "${TMPDIR:-/tmp}/j01links-XXXXXX")"
    filelist="$(mktemp "${TMPDIR:-/tmp}/j01files-XXXXXX")"
    find "$absdir" -type l 2> /dev/null | sort > "$linklist" || llrc=$?
    find "$absdir" -type f 2> /dev/null | sort > "$filelist" || flrc=$?
    if [ "$llrc" != 0 ] || [ "$flrc" != 0 ]; then
        n_unread=$((n_unread + 1))
        log "# scan: abs 枚举失败（link rc=$llrc file rc=${flrc}）⇒ 不敢断言扫全了"
    fi

    # 软链：`find -type f` 不含软链，所以**链本身**从来没被看过。链的 target
    # 可能就是一条本机绝对路径（新 vault 带着它换台机器就断）。这里单独走一遍，
    # 判的是 target 字面量，不跟随链读内容（不跟随 = 不可能被链带出 vault 外）。
    while IFS= read -r ff; do
        [ -n "$ff" ] || continue
        n_link=$((n_link + 1))
        local tgt trc=0
        tgt="$(readlink "$ff" 2> /dev/null)" || trc=$?
        if [ "$trc" != 0 ]; then
            # 读不出 target ≠ target 里没有本机路径。
            n_unread=$((n_unread + 1))
            log "# scan: 软链读不动（readlink rc=${trc}）: ${ff#$absdir/}"
            continue
        fi
        case "$tgt" in
            *"$J01_ABS_NEEDLE"*)
                n_link_hit=$((n_link_hit + 1))
                log "#   NEW-ABS-HIT(symlink-target) ${ff#$absdir/} -> $tgt"
                ;;
        esac
    done < "$linklist"

    while IFS= read -r ff; do
        [ -n "$ff" ] || continue
        n_files=$((n_files + 1))
        if is_binary "$ff"; then
            n_bin=$((n_bin + 1))
            # 二进制被跳过 ⇒ 它**没有被 grep 过**，不能算进「确实看过的文件」
            log "# scan: 跳过二进制（含 NUL）: ${ff#$absdir/}"
            continue
        fi
        local grc2=0
        grep -qF "$J01_ABS_NEEDLE" "$ff" || grc2=$?
        if [ "$grc2" -gt 1 ]; then
            # 读不动 ≠ 没命中。塌成一个分支 = 「读不了就算它干净」。
            n_unread=$((n_unread + 1))
            log "# scan: 读不动（grep rc=${grc2}）: ${ff#$absdir/}"
            continue
        fi
        n_scanned=$((n_scanned + 1))
        [ "$grc2" = 0 ] || continue
        rel="${ff#${absdir}/}"
        if [ "$rel" = "$J01_ABS_WHITELIST_RELPATH" ]; then
            # 白名单只放行 **vault 根**那一个文件，且只放行设计写入的那几个键
            # 所在的行。该文件里任何**别的**键带上本机路径仍判红。
            local bad_wl=0 k ok wk
            while IFS= read -r l; do
                [ -n "$l" ] || continue
                k="$(printf '%s' "$l" | sed -n -E 's/^[0-9]+:[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*:.*$/\1/p')"
                ok=0
                for wk in $J01_ABS_WHITELIST_KEYS; do
                    [ "$k" = "$wk" ] && ok=1
                done
                if [ "$ok" = 1 ]; then
                    log "#   whitelisted-hit $rel:${l%%:*} key=$k"
                else
                    bad_wl=$((bad_wl + 1))
                    log "#   NEW-ABS-HIT $rel:${l%%:*} key=${k:-<非键值行>}（白名单文件内的非设计键）"
                fi
            done << EOF5
$(grep -nF "$J01_ABS_NEEDLE" "$ff" 2> /dev/null)
EOF5
            if [ "$bad_wl" = 0 ]; then
                n_wl=$((n_wl + 1))
                continue
            fi
            n_new=$((n_new + bad_wl))
            continue
        fi
        bl=""
        if [ -n "$SCAN_BASELINE" ] && [ -f "$SCAN_BASELINE/$rel" ]; then
            if [ "$(sha_file "$ff")" = "$(sha_file "$SCAN_BASELINE/$rel")" ]; then
                bl="inherited"
            fi
        fi
        if [ "$bl" = "inherited" ]; then
            n_inherit=$((n_inherit + 1))
            log "# scan: 继承自模板源（整文件 sha 相同, 非本次部署引入）: $rel"
            while IFS= read -r l; do
                [ -n "$l" ] || continue
                log "#   inherited-hit $rel:${l%%:*}"
            done << EOF6
$(grep -nF "$J01_ABS_NEEDLE" "$ff" 2> /dev/null)
EOF6
        else
            n_new=$((n_new + 1))
            while IFS= read -r l; do
                [ -n "$l" ] || continue
                log "#   NEW-ABS-HIT $rel:${l%%:*}"
            done << EOF7
$(grep -nF "$J01_ABS_NEEDLE" "$ff" 2> /dev/null)
EOF7
        fi
    done < "$filelist"
    rm -f "$linklist" "$filelist"
    log "# scan: 枚举文件=$n_files 真扫过=$n_scanned 软链=$n_link 软链命中=$n_link_hit 二进制跳过=$n_bin 白名单=$n_wl 继承=$n_inherit 新引入=$n_new 读不动=$n_unread"
    if [ "$n_scanned" = 0 ] && [ "$n_link" = 0 ]; then
        # ⛔ 输入面为空 ⇒ 不许绿。数的是**真的 grep 过**的文件，不是枚举到的：
        #    一目录全是二进制时前者为 0 而后者非 0，用后者证明「看过了」是假证明。
        rc_abs=1
        reason_abs="empty-scan-surface(no-file-actually-grepped)"
    elif [ "$n_unread" != 0 ]; then
        rc_abs=1
        reason_abs="unreadable-files=$n_unread"
    elif [ "$((n_new + n_link_hit))" != 0 ]; then
        rc_abs=1
        reason_abs="new-abs-path-hits=$((n_new + n_link_hit))"
    elif [ "$n_inherit" != 0 ]; then
        reason_abs="ok-inherited-from-template=$n_inherit(registered-not-blocking)"
    fi
    emit_assert no-abs-path "$rc_abs" "$reason_abs"

    SCAN_LAST_RC=0
    [ "$rc_secret" = 0 ] && [ "$rc_abs" = 0 ] || SCAN_LAST_RC=1
    return 0
}

# ── throwaway 保护 ─────────────────────────────────────────────────────────
# ⛔ 诚实口径（原先写「三重保护」是自我夸大）：
#   ① 「realpath(ROOT) 在 TMPDIR 之内」与 ② 「basename 是 j01-*」这两条，对
#      本脚本自己 mktemp 出来的 ROOT 是**恒真**的（ROOT 就是用 TMPDIR 和该
#      模板造出来的）—— 它们是结构不变量的复述，不是独立判据。保留它们只为
#      「ROOT 被别处改过」这一种情形兜底，并如实标注。
#   ③ **真正在挡事的是黑名单**：ROOT 不得落在 harness 树 / **主仓根**（worktree
#      的 show-toplevel 不等于主仓！）/ live vault / $HOME/Library / $HOME/.claude*
#      / $HOME/.codex 之内；且 TMPDIR 本身也要过同一张黑名单（否则把 TMPDIR
#      指进仓里，①② 照样恒真）。
#   ④ deploy-vault.sh 自带的禁写面在它那一侧再判一次。
# throwaway_guard_verdict —— 把判定结果放进 GUARD_VERDICT（"ok" 或一条 reason），
# 过程量放进 GUARD_* 供调用方打日志。⛔ 每次调用都**重新解析** realpath：
# 初检与真正删除之间隔着整条部署（分钟级），TMPDIR 的中间段软链在这期间被改指
# 别处，初检那次的 realpath 结果就不再约束真正被删的那个对象（TOCTOU）。
# 所以 teardown 前必须原样再判一次，而不是复用 THROWAWAY_OK 这个旧结论。
throwaway_guard_verdict() {
    local p blacklist n_bl=0
    GUARD_RR="$(real_of "$ROOT")"
    GUARD_RTMP="$(real_of "${TMPDIR:-/tmp}")"
    GUARD_MREPO="$(main_repo_root)"
    GUARD_NBL=0
    GUARD_VERDICT="ok"

    if [ -z "$GUARD_RR" ]; then
        GUARD_VERDICT="root-realpath-unresolvable(fail-closed)"; return 0
    fi
    if [ -z "$GUARD_RTMP" ]; then
        GUARD_VERDICT="tmpdir-realpath-unresolvable(fail-closed)"; return 0
    fi
    if ! is_under "$GUARD_RR" "$GUARD_RTMP"; then
        GUARD_VERDICT="root-not-under-tmpdir"; return 0
    fi
    case "${ROOT##*/}" in
        j01-*) : ;;
        *) GUARD_VERDICT="root-basename-not-from-our-mktemp-template"; return 0 ;;
    esac

    # 黑名单：ROOT 与 TMPDIR **都**要过。主仓根用 --git-common-dir 推，
    # 不用 show-toplevel（worktree 里后者回的是 worktree 自己）。
    blacklist="$(real_of "$HARNESS")"
    if [ -n "$GUARD_MREPO" ]; then
        blacklist="$blacklist
$GUARD_MREPO
$GUARD_MREPO/canvas-vault"
    fi
    blacklist="$blacklist
$(real_of "$HOME/Library")
$(real_of "$HOME/.claude")
$(real_of "$HOME/.codex")"
    while IFS= read -r p; do
        [ -n "$p" ] || continue
        n_bl=$((n_bl + 1))
        if is_under "$GUARD_RR" "$p"; then
            GUARD_NBL=$n_bl; GUARD_VERDICT="root-under-protected:$p"; return 0
        fi
        if is_under "$GUARD_RTMP" "$p"; then
            GUARD_NBL=$n_bl; GUARD_VERDICT="tmpdir-under-protected:$p"; return 0
        fi
    done << EOF
$blacklist
EOF
    GUARD_NBL=$n_bl
    if [ "$n_bl" = 0 ]; then
        # 黑名单一条都没解析出来 ⇒ 等于没判 ⇒ fail-closed。
        GUARD_VERDICT="protected-path-list-empty(fail-closed)"
        return 0
    fi
    # ⛔ 最后一道、也是唯一一道**按对象**而不是按名字的判据：
    #    路径可以在初检与真删之间被指到别的对象上（TMPDIR 软链改指，且新目标下
    #    恰好也有一个同名 j01-XXXXXX）。只比路径的判据对此完全看不见。
    # ⛔ ROOT_ID 为空 ⇒ 建根时就没问出身份 ⇒ **整条身份保护是关的**。
    #    原先 `if [ -n "$ROOT_ID" ]` 让这种情况静默跳过全部比对，正是 fail-open。
    local now_id
    if [ -z "$ROOT_ID" ]; then
        GUARD_VERDICT="root-identity-never-captured(fail-closed)"
        return 0
    fi
    now_id="$(path_identity "$ROOT")"
    if [ -z "$now_id" ]; then
        GUARD_VERDICT="root-identity-unresolvable(fail-closed)"
    elif [ "$now_id" != "$ROOT_ID" ]; then
        GUARD_VERDICT="root-identity-changed(was=$ROOT_ID now=$now_id)"
    fi
    return 0
}

assert_throwaway_safe() {
    local rc=0 reason=""
    throwaway_guard_verdict
    log "# throwaway: ROOT=$ROOT real=$GUARD_RR tmpbase=${TMPDIR:-/tmp} real=$GUARD_RTMP main_repo=$GUARD_MREPO"
    log "# throwaway: ①②（在 TMPDIR 内 / basename j01-*）对自造 ROOT 恒真, 仅为兜底, 不计作独立判据"
    log "# throwaway: 黑名单条数=${GUARD_NBL}（这一条才是真正在挡事的判据）"
    if [ "$GUARD_VERDICT" != ok ]; then
        rc=1; reason="$GUARD_VERDICT"
    fi
    emit_assert throwaway-outside-protected "$rc" "$reason"
    THROWAWAY_OK=0
    [ "$rc" = 0 ] && THROWAWAY_OK=1
    return 0
}

# teardown_root — 全脚本**唯一**发起删除的地方：只有一行调用
# `safe_rmtree_by_identity`，主流程与 EXIT trap 都按函数名调它（trap 行里不出现
# 删除语句），所以「执行删除的行」恰好 1 条，负控③ 的「删掉那一行、删了几行=1」
# 才成立。
# ⛔ 函数体不能只有那一行：删掉后必须仍是合法函数且能正常返回，否则负控红的
#    原因会变成「语法错/未定义函数」而不是 state-diff（门红在了另一条路径上）。
# ⛔ 删除本身**不走路径**：`safe_rmtree_by_identity` 全程 fd 相对操作，把「检查
#    的对象」与「删除的对象」绑成同一个 inode。上一版按路径递归删除时这里留着
#    一段 TOCTOU 残余窗口（复检通过后路径仍可被改指），审查者指出 Python 有
#    `os.open(dir_fd=)` / `unlink(dir_fd=)` 等原语、「bash 没有」不足以支持不修
#    —— 该意见成立，已改。窗口不再存在，不是被压缩。
# safe_rmtree_by_identity <root> <want_dev:ino> —— 按**对象**而不是按名字删除。
# 全程 fd 相对：先打开父目录 fd，在其中按 basename 核对 (st_dev, st_ino) 与建根时
# 记下的身份一致，再 openat 子目录（O_NOFOLLOW）、fstat 复核，之后所有 unlink/rmdir
# 都走 dir_fd。中途把路径上任何一段改指别处都不会让删除落到另一个对象上。
# rc: 0 删成 / 3 身份不符（拒删）/ 其它 = 出错（拒删）
safe_rmtree_by_identity() {
    py - "$1" "$2" << 'PY'
import os, stat, sys

root = sys.argv[1]
want = sys.argv[2]
parent = os.path.dirname(os.path.abspath(root)) or "/"
base = os.path.basename(os.path.abspath(root))
if not base or base in (".", ".."):
    sys.exit(4)


def ident(st):
    return "%d:%d" % (st.st_dev, st.st_ino)


try:
    pfd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
except OSError:
    sys.exit(5)
try:
    try:
        st = os.stat(base, dir_fd=pfd, follow_symlinks=False)
    except OSError:
        sys.exit(6)
    if not stat.S_ISDIR(st.st_mode) or ident(st) != want:
        sys.exit(3)
    try:
        cfd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
    except OSError:
        sys.exit(7)
    try:
        # 复核：openat 拿到的这个 fd 指的必须还是刚才核过身份的那个对象
        if ident(os.fstat(cfd)) != want:
            sys.exit(3)

        def purge(dfd):
            for name in os.listdir(dfd):
                try:
                    est = os.stat(name, dir_fd=dfd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if stat.S_ISDIR(est.st_mode):
                    sub_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dfd)
                    try:
                        purge(sub_fd)
                    finally:
                        os.close(sub_fd)
                    os.rmdir(name, dir_fd=dfd)
                else:
                    os.unlink(name, dir_fd=dfd)

        purge(cfd)
    finally:
        os.close(cfd)
    os.rmdir(base, dir_fd=pfd)
finally:
    os.close(pfd)
sys.exit(0)
PY
}

teardown_root() {
    if [ -z "${ROOT:-}" ] || [ ! -d "$ROOT" ]; then
        return 0
    fi
    if [ "${THROWAWAY_OK:-0}" != 1 ]; then
        log "# teardown: 跳过 —— throwaway-outside-protected 未过，不敢删 $ROOT"
        return 0
    fi
    if [ "$KEEP_ROOT" = 1 ]; then
        log "# teardown: --keep-root 指定，保留 $ROOT"
        return 0
    fi
    # ⛔ $ROOT 里装着本实例的 .env 与 compose 的 VAULTS_ROOT bind 源。容器还活着
    #    就把它删掉 = 把一个运行中容器的挂载源抽走。
    #    查询失败 ≠ 零容器：`docker ps` 非零且无输出时 `grep -c` 照样给 0，
    #    那是「问不出来」不是「没有」。fail-closed，不删。
    # ⛔ 只有**真的尝试过 up** 才需要查容器。fixture 从头到尾没碰 docker，
    #    却因为「CLI 装了但 daemon 没起」的 docker ps 失败而拒删 ⇒ throwaway 残留
    #    ⇒ state-diff 红。那是拿一个与被测性质无关的条件把门弄红。
    # ⛔ 真 up 过而 docker 客户端又不可用 ⇒ **问不出有没有容器** ⇒ 拒删。
    #    上一轮写成「客户端不在就跳过整个检查」，那是把「问不出来」当成「没有」。
    if [ "$UP_ATTEMPTED" = 1 ] && ! command -v docker > /dev/null 2>&1; then
        log "# teardown: 跳过 —— 真 up 过但 docker 客户端不可用，问不出容器状态就不敢删"
        return 0
    fi
    if [ "$UP_ATTEMPTED" = 1 ] && [ -n "${VAULT_NAME:-}" ] && command -v docker > /dev/null 2>&1; then
        local names="" drc=0 alive=0
        names="$(docker ps -a --format '{{.Names}}' 2> /dev/null)" || drc=$?
        if [ "$drc" != 0 ]; then
            log "# teardown: 跳过 —— docker ps 查询失败(rc=$drc)，问不出有没有容器就不敢删"
            return 0
        fi
        alive="$(printf '%s\n' "$names" | grep -c "^cls-$VAULT_NAME-" || :)"
        if [ "${alive:-0}" != 0 ]; then
            log "# teardown: 跳过 —— 仍有 $alive 个 cls-$VAULT_NAME-* 容器在，不抽走它们的挂载源"
            return 0
        fi
    fi
    # ⛔ 身份复检**紧挨**删除语句：初检（assert_throwaway_safe）到这里隔着整条
    #    部署，路径可能已经不是当初那个对象了。重判一次，不复用旧结论。
    #    这一层是**纵深**：真正把「检查的对象」与「删除的对象」绑死的是
    #    `safe_rmtree_by_identity` 内部的 fd 相对操作 + fstat 复核，不是这里。
    throwaway_guard_verdict
    if [ "$GUARD_VERDICT" != ok ]; then
        log "# teardown: 跳过 —— 删除前复检未过（${GUARD_VERDICT}）"
        return 0
    fi
    local rmrc=0
    safe_rmtree_by_identity "$ROOT" "$ROOT_ID" || rmrc=$?
    if [ "$rmrc" != 0 ]; then
        log "# teardown: 删除未成（safe_rmtree rc=${rmrc}；3=身份不符拒删）——交给 state-diff 判红"
        return 0
    fi
    # ⛔ 报「已删」之前先看一眼（DD-13 名实一致）：删除可能因权限等原因没成，
    #    而这一行是人读日志时的第一手印象。自述不算数，观测才算数
    #    —— 真正的判据仍是 state-diff 的 S1 快照。
    if [ -d "$ROOT" ]; then
        log "# teardown: ⚠️ 删除之后 $ROOT 仍在（未删成, 交给 state-diff 判红）"
    else
        log "# teardown: 已删 $ROOT"
    fi
    return 0
}

# ⛔ up 之后到 down 之间任何一条命令失败，`set -e` 会直接退出 —— 那时容器还开着，
#    而原先的 EXIT trap 只会「因为容器还在」拒删 ROOT，不会去停容器。
#    trap 里补一次**只拆本项目**的 down（必带 -p，去掉它 = 拆光）。
emergency_down() {
    [ "${UP_ATTEMPTED:-0}" = 1 ] || return 0
    [ -n "${VAULT_NAME:-}" ] || return 0
    if ! command -v docker > /dev/null 2>&1; then
        log "# emergency-down: docker 客户端不可用，无法确认/停止容器" || :
        return 0
    fi
    local names="" drc=0 alive=0
    names="$(docker ps -a --format '{{.Names}}' 2> /dev/null)" || drc=$?
    [ "$drc" = 0 ] || return 0
    alive="$(printf '%s\n' "$names" | grep -c "^cls-$VAULT_NAME-" || :)"
    [ "${alive:-0}" != 0 ] || return 0
    # ⛔ 清理动作**不许依赖日志写成功**：磁盘满 / 失去写权限时 `log` 会失败，
    #    `set -e` 会把 trap 本身带走，down 就不执行了。日志一律 `|| :`。
    log "# emergency-down: 退出时仍有 $alive 个 cls-$VAULT_NAME-* 容器，执行只拆本项目的 down" || :
    docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
        -p "cls-$VAULT_NAME" --project-directory "$HARNESS" down > /dev/null 2>&1 || :
}

on_exit() { emergency_down; teardown_root; }

# ── 快照 / state-diff ─────────────────────────────────────────────────────
# S0/S1 各由这些部分构成：
#   ① harness 树 porcelain（排除本卡证据目录）的 sha
#   ② canvas-vault/ 整棵的逐文件 sha —— ⛔ 必须单列：porcelain **按定义不列
#      gitignored 文件**，而 deploy 步 1 在 main.js 缺席时会 `npm run build`
#      并把产物 cp 进 <harness>/canvas-vault/...（gitignored）。只看 porcelain
#      的快照对这次写入是瞎的。
#   ③ $ROOT 是否存在 + 其文件清单 sha
#   ④ deploy 缺省证据目录是否被误用（我们显式传了 --evidence-dir）
#   ⑤ harness .env 家族的 sha（--also-push 会追加 DAILY_REVIEW_VAULTS；
#      本脚本永不传该参数，这一项是**结果侧**的证明）
snapshot() {
    local tag="$1" e
    # ⛔ 采集本身失败时，S0/S1 会「两次同错 ⇒ 哈希相同 ⇒ 零差异」。比较错误标记
    #    相不相同解决不了这个 —— 必须把「这次采集是否可信」单独记下来，
    #    任一侧不可信就禁止 state-diff 判绿。
    SNAPSHOT_OK_N=$((SNAPSHOT_OK_N + 1))
    {
        printf 'porcelain='
        git -C "$HARNESS" --no-pager status --porcelain --no-column -- . ':(exclude)_bmad-output' 2> /dev/null | sha_stdin
        # ⛔ porcelain 只给状态字母，本来就 ` M` 的文件再改一次、状态行一模一样。
        #    补一份**内容**摘要：已跟踪文件的实际 diff。
        printf 'tracked_diff='
        git -C "$HARNESS" --no-pager diff --no-color HEAD -- . ':(exclude)_bmad-output' 2> /dev/null | sha_stdin
        printf 'canvas_vault_tree='
        ( cd "$HARNESS" 2> /dev/null && find canvas-vault -type f -print0 2> /dev/null \
            | xargs -0 shasum -a 256 2> /dev/null | sort || : ) | sha_stdin
        printf 'root_exists=%s\n' "$([ -n "${ROOT:-}" ] && [ -d "$ROOT" ] && echo yes || echo no)"
        printf 'root_tree='
        ( find "$ROOT" 2> /dev/null | sort || : ) | sha_stdin
        printf 'deploy_default_ev='
        # ⛔ 数个数挡不住「目录已存在、内容被写进去了」——个数不变，diff 就看不见。
        #    改为对目录内**每个文件逐个 sha**。并且把 find / shasum 的**失败本身**
        #    也写进被哈希的流：否则「列不了目录」会被 `|| :` 隐去，两侧同样什么都
        #    没记到 ⇒ 哈希相同 ⇒ 未检查到的变化被判成零差异。
        {
            ddrc=0
            find "$HARNESS/_bmad-output/审查" -maxdepth 1 -name 'evidence-deploy-j01tw*' 2> /dev/null | sort || ddrc=$?
            printf 'TOPRC %s\n' "$ddrc"
        } > "$EVDIR/.ddlist.$tag" 2> /dev/null || printf 'TOPRC 99\n' > "$EVDIR/.ddlist.$tag"
        {
            while IFS= read -r dd; do
                case "$dd" in TOPRC*) printf '%s\n' "$dd"; continue ;; esac
                [ -n "$dd" ] || continue
                printf 'DIR %s\n' "$dd"
                lsrc=0
                find "$dd" -type f 2> /dev/null | sort > "$EVDIR/.ddfiles.$tag" || lsrc=$?
                printf 'LSRC %s\n' "$lsrc"
                while IFS= read -r ff; do
                    [ -n "$ff" ] || continue
                    shasum -a 256 "$ff" 2> /dev/null || printf 'SHAFAIL %s\n' "$ff"
                done < "$EVDIR/.ddfiles.$tag"
            done < "$EVDIR/.ddlist.$tag"
        } | sha_stdin
        rm -f "$EVDIR/.ddlist.$tag" "$EVDIR/.ddfiles.$tag"
        # ⛔ 只盯两个固定路径，会漏掉「部署误在 harness 根生成 .env.<vault>」这种情形
        #    （那类文件被 .gitignore 覆盖，porcelain 也不记）。改为枚举 .env 家族。
        for e in "$HARNESS"/.env "$HARNESS"/.env.* "$HARNESS"/backend/.env "$HARNESS"/backend/.env.*; do
            if [ -f "$e" ]; then
                printf 'env:%s=%s\n' "${e#$HARNESS/}" "$(sha_file "$e")"
            fi
        done
        printf 'env_family_count=%s\n' \
            "$(ls -1 "$HARNESS"/.env "$HARNESS"/.env.* "$HARNESS"/backend/.env "$HARNESS"/backend/.env.* 2> /dev/null | wc -l | tr -d ' ')"
    } > "$EVDIR/snapshot-$tag.txt" || SNAPSHOT_BAD_N=$((SNAPSHOT_BAD_N + 1))
    # ⛔ 上一行的 `|| …` 其实**永远不会触发**：大括号组的退出码是它**最后一条**
    #    命令的退出码，而最后一条是 `printf`（恒 0）。靠它当可信度标志是自欺。
    #    真正的判据：逐个核对该有的键都在。缺任何一个 = 这次采集不可信。
    local _k _miss=""
    for _k in porcelain= tracked_diff= canvas_vault_tree= root_exists= root_tree= \
        deploy_default_ev= env_family_count=; do
        grep -q "^$_k" "$EVDIR/snapshot-$tag.txt" 2> /dev/null || _miss="$_miss $_k"
    done
    if [ -n "$_miss" ]; then
        SNAPSHOT_BAD_N=$((SNAPSHOT_BAD_N + 1))
        log "# snapshot $tag: ⚠️ 采集不完整，缺键:${_miss}"
    fi
    log "# snapshot $tag -> snapshot-$tag.txt sha=$(sha_file "$EVDIR/snapshot-$tag.txt")"
}

# ── 隔离预检 ───────────────────────────────────────────────────────────────
# 先证**输入面非空**，再逐条判。五条各自独立求值不短路（短路只报第一条，
# 而台账要登记的是「共享面」这个集合）。
isolation_preflight() {
    local cfg="$1" rc=0 reason=""
    local vals prc=0
    vals="$(py - "$cfg" << 'PY'
import sys, yaml
try:
    d = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
except Exception as exc:
    print("parse_error=%s" % (type(exc).__name__,))
    sys.exit(0)
if not isinstance(d, dict):
    print("parse_error=not-a-mapping")
    sys.exit(0)
s = d.get("services")
s = s if isinstance(s, dict) else {}
n = s.get("neo4j")
n = n if isinstance(n, dict) else None
b = s.get("backend")
b = b if isinstance(b, dict) else None
# 输入面自述：下游那五条判据全是「找到禁止值才红」，没有这几行就无从区分
# 「真的隔离好了」与「这份配置里根本没有 neo4j 可看」。
# ⛔ compose 有长短两种写法：长格式的 ports/volumes 元素是 dict，短格式是字符串
# （"127.0.0.1:7478:7474" / "/Users/x:/data"）。只认 dict 就会把短格式整个过滤成空，
# 于是下游「找到禁止值才红」的判据零次执行 ⇒ 判绿。两种都得解析出来。
def _ports(svc):
    out = []
    for p in (svc or {}).get("ports") or []:
        if isinstance(p, dict):
            out.append(str(p.get("published")))
        elif isinstance(p, str):
            parts = p.split(":")
            out.append(parts[-2] if len(parts) >= 2 else parts[0])
    return out


def _vols(svc):
    out = []
    for v in (svc or {}).get("volumes") or []:
        if isinstance(v, dict):
            out.append(str(v.get("source")))
        elif isinstance(v, str):
            out.append(v.split(":")[0])
    return out


_p = _ports(n)
# ⛔ 卷这一维必须覆盖**会被启动的那个服务**。deploy 跑的是 `up -d backend`，而
#    backend 的 volumes 里挂着 `${VAULTS_ROOT:-.}:/vaults`（compose 还让 shell 环境
#    变量压过 --env-file）。只判 neo4j 的卷 = 判了一个不会被启动的服务。
#    这里把**所有服务**的卷都吐出来，带服务名，下游逐条判。
_v = []
for _svc_name, _svc in sorted(s.items()):
    if not isinstance(_svc, dict):
        continue
    for _src in _vols(_svc):
        _v.append("%s|%s" % (_svc_name, _src))
print("surface.has_services=%s" % (1 if s else 0,))
print("surface.has_neo4j=%s" % (1 if n is not None else 0,))
print("surface.has_backend=%s" % (1 if b is not None else 0,))
# 数的是**解析出来的**条目数，不是原始 list 长度 —— 否则「有 2 个元素但一个都
# 解析不出来」会被读成输入面非空。
print("surface.neo4j_ports=%d" % (len(_p),))
print("surface.all_volumes=%d" % (len(_v),))
print("surface.networks=%d" % (len(d.get("networks") or {}),))
print("neo4j.container_name=%s" % ((n or {}).get("container_name"),))
print("neo4j.published=%s" % (",".join(_p),))
print("all_volume_sources=%s" % (",".join(_v),))
dep = (b or {}).get("depends_on") or {}
try:
    deps = sorted(dep)
except Exception:
    deps = []
print("backend.depends_on=%s" % (",".join(str(x) for x in deps),))
# ⛔ 判据要比的是**实际网络名**，不是 "逻辑键:名字" 拼出来的那个串：
#    子串匹配会把 `canvas-learning-network-j01`（更长、实际独立）误判成共享，
#    也会因为逻辑键恰好叫 `canvas-learning-network` 而误判。两个字段分开吐。
print("networks=%s" % (",".join("%s:%s" % (k, (v or {}).get("name")) for k, v in (d.get("networks") or {}).items()),))
print("network_names=%s" % (",".join(str((v or {}).get("name")) for v in (d.get("networks") or {}).values()),))
lv = (d.get("volumes") or {}).get("canvas-lancedb") or {}
print("lancedb_volume.name=%s" % (lv.get("name"),))
print("lancedb_volume.external=%s" % (lv.get("external"),))
PY
)" || prc=$?
    if [ "$prc" != 0 ]; then
        emit_assert isolation-preflight 1 "compose-config-read-failed(py-rc=$prc)"
        ISOLATION_RC=1
        return 0
    fi

    local l
    while IFS= read -r l; do
        [ -n "$l" ] || continue
        log "# isolation: $l"
    done << EOF
$vals
EOF

    case "$vals" in
        *parse_error=*)
            emit_assert isolation-preflight 1 \
                "compose-config-unparseable:$(printf '%s\n' "$vals" | sed -n 's/^parse_error=//p')"
            ISOLATION_RC=1
            return 0
            ;;
    esac

    # ── ⛔ 输入面非空断言（fail-closed）────────────────────────────────
    # 这是本函数最重要的一段。下面五条判据全是「找到禁止值才红」；若这份
    # 配置里没有 neo4j 服务 / 没有端口 / 没有卷，五条都会「没找到 ⇒ 绿」，
    # 而这个绿正是 `up` 的唯一结构前提。
    # 「命令没跑成」与「结果真为零」是同一个数字 —— 必须先证有东西可看。
    local miss="" k v
    for k in has_services has_neo4j has_backend neo4j_ports all_volumes networks; do
        v="$(printf '%s\n' "$vals" | sed -n "s/^surface\\.$k=//p")"
        case "$v" in
            '' | 0) miss="${miss:+$miss,}$k" ;;
        esac
    done
    if [ -n "$miss" ]; then
        log "# isolation-check: input-surface rc=1 degenerate-missing=$miss"
        emit_assert isolation-preflight 1 "compose-config-degenerate:$miss"
        ISOLATION_RC=1
        return 0
    fi
    log "# isolation-check: input-surface rc=0 ok（六项输入面均非空, 下面五条判据才有意义）"

    local cname pub vsrc dep nets lvname lvext
    cname="$(printf '%s\n' "$vals" | sed -n 's/^neo4j\.container_name=//p')"
    pub="$(printf '%s\n' "$vals" | sed -n 's/^neo4j\.published=//p')"
    vsrc="$(printf '%s\n' "$vals" | sed -n 's/^all_volume_sources=//p')"
    dep="$(printf '%s\n' "$vals" | sed -n 's/^backend\.depends_on=//p')"
    nets="$(printf '%s\n' "$vals" | sed -n 's/^networks=//p')"
    lvname="$(printf '%s\n' "$vals" | sed -n 's/^lancedb_volume\.name=//p')"
    lvext="$(printf '%s\n' "$vals" | sed -n 's/^lancedb_volume\.external=//p')"

    local c1=0 c2=0 c3=0 c4=0 c5=0
    local d1="" d2="" d3="" d4="" d5=""

    # ① neo4j 容器名不得与现网同名
    if [ "$cname" = "$J01_FORBIDDEN_NEO4J_CONTAINER" ]; then
        c1=1; d1="neo4j-container-name-collides:$cname"
    fi
    log "# isolation-check: container-name rc=$c1 ${d1:-ok}"

    # ② neo4j published 端口不得落在拒绝集合里（先十进制归一，`07691` 也要拦）
    local p q pn qn
    while IFS= read -r p; do
        [ -n "$p" ] || continue
        pn="$(num_of "$p")"
        if [ -z "$pn" ]; then
            c2=1; d2="${d2:+$d2,}neo4j-published-port-not-numeric:$p"
            continue
        fi
        for q in $J01_FORBIDDEN_PUBLISHED_PORTS; do
            qn="$(num_of "$q")"
            if [ "$pn" = "$qn" ]; then
                c2=1; d2="${d2:+$d2,}neo4j-published-port-collides:$pn"
            fi
        done
    done << EOF
$(printf '%s' "$pub" | tr ',' '\n')
EOF
    log "# isolation-check: published-ports rc=$c2 ${d2:-ok}"

    # ③ **任何服务**的卷都不得是宿主 bind mount（具名卷才算隔离）。
    #    ⛔ 两次踩过的坑都在这一条上：
    #    (a) 早期只比「是否在 gitroot 之内」—— worktree 里 `--show-toplevel` 回的是
    #        worktree，而 compose 写死的是**主仓**绝对路径，那一半永远匹配不上；
    #    (b) 上一版只看 `services.neo4j.volumes` —— 而 `up -d backend` 真正启动的是
    #        **backend**，它的卷里挂着 `${VAULTS_ROOT:-.}:/vaults`。judge 判了一个
    #        不会被启动的服务，门被一个本卡不拥有的文件的偶然属性顶着。
    #    正向规则：source 不是具名卷形态（`[A-Za-z0-9_.-]+`，不含 `/`）一律红。
    local vv svc src mrepo rhome
    mrepo="$(main_repo_root)"
    rhome="$(real_of "$HOME")"
    while IFS= read -r vv; do
        [ -n "$vv" ] || continue
        svc="${vv%%|*}"
        src="${vv#*|}"
        case "$src" in
            *[!A-Za-z0-9_.-]* | */* | .* | "")
                c3=1
                local mark=""
                case "$src" in
                    /*)
                        if [ -n "$mrepo" ] && is_under "$src" "$mrepo"; then
                            mark="(in-main-repo)"
                        elif [ -n "$rhome" ] && is_under "$src" "$rhome"; then
                            mark="(in-home)"
                        fi
                        ;;
                    *) mark="(relative-bind)" ;;
                esac
                d3="${d3:+$d3,}${svc}-volume-is-host-bind-mount:${src}${mark}"
                ;;
        esac
    done << EOF
$(printf '%s' "$vsrc" | tr ',' '\n')
EOF
    log "# isolation-check: all-service-volumes rc=$c3 ${d3:-ok}"

    # ④ backend 不得 depends_on neo4j（否则 up -d backend 连带起现网 neo4j）
    case ",$dep," in
        *,neo4j,*) c4=1; d4="backend-depends-on-neo4j" ;;
    esac
    log "# isolation-check: backend-depends-on rc=$c4 ${d4:-ok}"

    # ⑤ 网络不得用现网固定名 —— 逐个网络**精确**比名字，不做子串匹配
    local nn nnames
    nnames="$(printf '%s\n' "$vals" | sed -n 's/^network_names=//p')"
    while IFS= read -r nn; do
        [ -n "$nn" ] || continue
        if [ "$nn" = "$J01_FORBIDDEN_NETWORK_NAME" ]; then
            c5=1; d5="network-name-shared:$nn"
        fi
    done << EOF
$(printf '%s' "$nnames" | tr ',' '\n')
EOF
    log "# isolation-check: network-name rc=$c5 ${d5:-ok}"

    # ⑥ LanceDB external 共享卷：**登记项，不阻断**（草案 §五待裁）
    log "# isolation: [登记不阻断] lancedb_volume name=$lvname external=$lvext —— external 共享卷是产品口径待裁项"

    log "# isolation-check: 红条数=$((c1 + c2 + c3 + c4 + c5))/5"
    local d
    for d in "$d1" "$d2" "$d3" "$d4" "$d5"; do
        if [ -n "$d" ]; then
            rc=1
            [ -n "$reason" ] || reason="$d"
        fi
    done

    emit_assert isolation-preflight "$rc" "$reason"
    ISOLATION_RC="$rc"
    return 0
}

# ── evidence 复制（先脱敏复查，命中即拒绝复制）────────────────────────────
# deploy 自己的证据里密钥只 sha（:13-14）、compose-config 已按键名脱敏
# （:176-177）。复制进入库目录前**再查一遍**，而且不能只复述生产者的口径：
#   (a) 按**参照 env 的真实值**逐个 grep —— 这一条与键名无关，YAML 块标量、
#       换了键名、被改写过的行都逃不掉（值只在内存里比，不落盘不进日志）；
#   (b) 键名形态兜底（保留，但去掉原先 `=$` 那个豁免 —— 它只豁免了
#       「非空且以 = 结尾」的值，正是 base64/padding 密钥的形态）。
# evidence_has_ref_plaintext <file> —— 文件里有没有参照 env 的密钥明文。
# 与 stage_deploy_evidence 共用同一实现（两份手抄清单必然漂移）。
# evidence_has_ref_plaintext <file> [额外needle] —— 文件里有没有「不得出现」的明文。
# 集合 = 参照 env 的密钥值 ∪ 本次新生成的实例密钥。⛔ 两者必须走**同一个**函数：
# 上一轮把实例密钥只查了主日志，部署证据那条路径照样会把它原样复制进库。
# ⛔ 本函数只回「有没有命中」，**不负责**证明 needle 集合非空 —— 集合为空时它
#    恒回 1（没命中），调用方若直接据此判绿就是空洞通过。非空由
#    `evidence_needle_count` 单独证，见 emit_evidence_redacted 的 fail-closed 分支。
evidence_has_ref_plaintext() {
    local f="$1" extra="${2:-}" rf kv kk vv
    if [ -n "$extra" ] && grep -qF -- "$extra" "$f" 2> /dev/null; then
        return 0
    fi
    while IFS= read -r rf; do
        [ -n "$rf" ] || continue
        [ -f "$rf" ] || continue
        while IFS= read -r kv; do
            [ -n "$kv" ] || continue
            kk="${kv%%=*}"
            vv="${kv#*=}"
            [ -n "$vv" ] || continue
            if is_sensitive_key "$kk"; then
                :
            elif ! looks_like_secret "$vv"; then
                continue
            fi
            if grep -qF -- "$vv" "$f" 2> /dev/null; then
                return 0
            fi
        done << EOFV2
$(env_kv_of "$rf")
EOFV2
    done << EOFR2
$SCAN_REF_ENVS
EOFR2
    return 1
}

# evidence_needle_count —— 「不得出现」的值集合有多大。0 ⇒ 这道判据没有内容。
evidence_needle_count() {
    local extra="${1:-}" rf kv kk vv cnt=0
    [ -z "$extra" ] || cnt=$((cnt + 1))
    while IFS= read -r rf; do
        [ -n "$rf" ] || continue
        [ -f "$rf" ] || continue
        while IFS= read -r kv; do
            [ -n "$kv" ] || continue
            kk="${kv%%=*}"
            vv="${kv#*=}"
            [ -n "$vv" ] || continue
            if is_sensitive_key "$kk"; then
                cnt=$((cnt + 1))
            elif looks_like_secret "$vv"; then
                cnt=$((cnt + 1))
            fi
        done << EOFN
$(env_kv_of "$rf")
EOFN
    done << EOFNR
$SCAN_REF_ENVS
EOFNR
    printf '%s' "$cnt"
}

# stage_deploy_evidence —— ⛔ **必须在拆除之前**跑：$DEPLOY_EV 与 $ENV_FILE 都在
# $ROOT 里面，拆除之后它们就没了。结果累进 EV_* 全局，供最后的
# emit_evidence_redacted 合并判定。
stage_deploy_evidence() {
    local f deplist hit
    EV_BAD=0
    EV_INSPECTED=0
    EV_DEP_N=0
    EV_DEP_RC=0
    EV_INST_KEY=""
    EV_STAGED=1
    mkdir -p "$EVDIR/deploy-evidence"
    # 本实例新密钥也在「不得出现」集合里 —— 趁 $ENV_FILE 还在把它取出来
    if [ -f "$ENV_FILE" ]; then
        EV_INST_KEY="$(sed -n 's/^INTERNAL_API_KEY=//p' "$ENV_FILE" | tail -1 | tr -d '\r\n')"
    fi
    if [ ! -d "$DEPLOY_EV" ]; then
        EV_DEP_RC=99
        log "# evidence(stage): 部署证据目录不存在: $DEPLOY_EV"
        return 0
    fi
    deplist="$(mktemp "${TMPDIR:-/tmp}/j01dep-XXXXXX")"
    find "$DEPLOY_EV" -maxdepth 1 -type f 2> /dev/null | sort > "$deplist" || EV_DEP_RC=$?
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        [ -f "$f" ] || continue
        EV_INSPECTED=$((EV_INSPECTED + 1))
        hit=0
        # (a) 「不得出现」的明文（参照 env 密钥 ∪ 本实例新密钥）—— 与主日志同一函数
        if evidence_has_ref_plaintext "$f" "$EV_INST_KEY"; then
            hit=$((hit + 1))
            log "# evidence: ${f##*/} 内出现不得出现的密钥明文（值不打印）"
        fi
        # (b) 键名形态兜底
        if grep -nE '^[[:space:]]*-?[[:space:]]*[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|CREDENTIAL)[A-Za-z0-9_]*[:=][[:space:]]*.+' "$f" 2> /dev/null \
            | grep -vE '(<redacted>|[:=][[:space:]]*$)' > /dev/null 2>&1; then
            hit=$((hit + 1))
            log "# evidence: ${f##*/} 有敏感键名且值非 <redacted> 的行"
        fi
        if [ "$hit" != 0 ]; then
            EV_BAD=$((EV_BAD + 1))
            log "# evidence: 拒绝复制（疑似未脱敏明文）: ${f##*/}"
            continue
        fi
        cp "$f" "$EVDIR/deploy-evidence/${f##*/}"
    done < "$deplist"
    # ⛔ `grep -c` 零命中时**既把 0 打到 stdout 又退 1**，`|| printf 0` 会再补一个，
    #    命令替换只吃尾部换行 ⇒ 得到三字节的 "0\n0"，等值判断永假、日志行被撑断。
    #    改用只有一个输出通道的取法。
    EV_DEP_N="$(grep -c '[^[:space:]]' "$deplist" 2> /dev/null | head -n 1 || true)"
    case "$EV_DEP_N" in
        '' | *[!0-9]*) EV_DEP_N=0 ;;
    esac
    rm -f "$deplist"
    log "# evidence(stage): 部署证据文件数=${EV_DEP_N}（枚举 rc=${EV_DEP_RC}）已查=${EV_INSPECTED} 拒绝复制=${EV_BAD}"
    return 0
}

# emit_evidence_redacted —— ⛔ **最后**跑：它要扫的 $LOG 就是本次主日志，早扫只看到
# 一个**前缀**，而入库并被 SHA256SUMS 登记的是完整文件 —— 判据看的和存档的必须是
# 同一份东西。此刻 $LOG 只差 summary/rc 两行，两行都由本脚本生成、不含任何密钥。
emit_evidence_redacted() {
    local rc=0 reason="" loghit=0 needles
    if [ "${EV_STAGED:-0}" != 1 ]; then
        emit_assert evidence-redacted 1 "stage-never-ran(no-input-surface)"
        return 0
    fi
    if [ -n "$LOG" ] && [ -f "$LOG" ]; then
        if evidence_has_ref_plaintext "$LOG" "$EV_INST_KEY"; then
            loghit=$((loghit + 1))
            log "# evidence: 主日志里出现了不得出现的密钥明文（值不打印）"
        fi
    fi
    needles="$(evidence_needle_count "$EV_INST_KEY")"
    log "# evidence: 部署证据文件数=${EV_DEP_N}（枚举 rc=${EV_DEP_RC}）复查文件数=${EV_INSPECTED} 拒绝复制=${EV_BAD} 主日志命中=${loghit} needle 数=${needles}"
    if [ "${needles:-0}" = 0 ]; then
        # ⛔ 没有任何「不得出现」的值 ⇒ 「没查到明文」这句话没有内容。
        rc=1; reason="empty-needle-set(nothing-to-look-for)"
    elif [ "$EV_DEP_RC" != 0 ]; then
        # 枚举失败 ≠ 没有文件。
        rc=1; reason="deploy-evidence-enumeration-failed(rc=${EV_DEP_RC})"
    elif [ "$EV_DEP_N" = 0 ]; then
        # ⛔ 部署证据**一份都没有**时不许绿：主日志也算一份会把它盖住，两面分别判。
        rc=1; reason="no-deploy-evidence-file(empty-input-surface)"
    elif [ "$EV_INSPECTED" = 0 ]; then
        rc=1; reason="no-evidence-file-inspected(empty-input-surface)"
    elif [ "$loghit" != 0 ]; then
        rc=1; reason="secret-plaintext-in-main-log=${loghit}"
    elif [ "$EV_BAD" != 0 ]; then
        rc=1; reason="unredacted-lines-in-deploy-evidence=${EV_BAD}"
    fi
    emit_assert evidence-redacted "$rc" "$reason"
    return 0
}

# ── 收尾自检 ───────────────────────────────────────────────────────────────
verify_assert_completeness() {
    local id miss="" extra="" got
    for id in $ASSERT_ORDER; do
        case " $EMITTED " in
            *" $id "*) : ;;
            *) miss="$miss $id" ;;
        esac
    done
    for got in $EMITTED; do
        case " $ASSERT_ORDER " in
            *" $got "*) : ;;
            *) extra="$extra $got" ;;
        esac
    done
    log "# completeness: emitted=$EMITTED_N expected=$ASSERT_EXPECTED_N missing=[${miss# }] extra=[${extra# }]"
    if [ -n "$miss" ] || [ -n "$extra" ] || [ "$EMITTED_N" != "$ASSERT_EXPECTED_N" ]; then
        FAILED_N=$((FAILED_N + 1))
        return 1
    fi
    return 0
}

write_sha256sums() {
    # ⛔ 必须在**日志写完之后**跑：$LOG 也在 $EVDIR 里，先算 sha 再往日志里
    #    追加 summary/rc 两行，记下的就是追加之前那一版 ⇒ `shasum -c` 每跑必错。
    # SHA256SUMS 自己不进自己（否则永远对不上）。
    (
        cd "$EVDIR" || exit 1
        find . -type f ! -name 'SHA256SUMS' | sort | while IFS= read -r f; do
            shasum -a 256 "$f"
        done
    ) > "$EVDIR/SHA256SUMS"
}

# ── 日志头（自绑 HEAD + 被测件 sha）────────────────────────────────────────
write_header() {
    local head f
    head="$(git -C "$HARNESS" rev-parse HEAD 2> /dev/null || printf 'unknown')"
    log "# j01_e2e.sh — J01 新 vault bootstrap 黑盒 E2E harness [CARD-G2-11]"
    log "# ts=$TS mode=$MODE allow_up_flag=$ALLOW_UP allow_up_env=$USER_ALLOW_UP_ENV port=$PORT keep_root=$KEEP_ROOT"
    log "# head=$head"
    log "# harness=$HARNESS"
    log "# evidence_dir=$EVDIR"
    log "# rc 约定: 0=通过 1=失败(红) 2=跳过(不红, 必带 reason=)"
    for f in scripts/deploy-vault.sh scripts/install-vault.sh scripts/verify_vault_install.py docker-compose.yml scripts/j01_e2e.sh; do
        if [ -f "$HARNESS/$f" ]; then
            log "# sha256 $(sha_file "$HARNESS/$f")  $f"
        else
            log "# sha256 <absent>  $f"
        fi
    done
}

# docker compose 项目名集合（排序后的逗号串）。取不到时回哨兵串而不是空串 ——
# 空串与「真的一个项目都没有」不能是同一个值。
docker_project_set() {
    if ! command -v docker > /dev/null 2>&1; then
        printf '<docker-cli-absent>'
        return 0
    fi
    # ⛔ 先捕获再判，不要「python 打一次 + 管道失败再打一次」——那会得到**两行**
    #    `<unreadable>`，而下游是按单个值做哨兵匹配的，双行就谁也匹配不上。
    local out="" orc=0
    out="$(docker compose ls --format json 2> /dev/null | py -c 'import sys,json
try:
    d = json.load(sys.stdin)
except Exception:
    print("<unreadable>"); raise SystemExit(0)
if not isinstance(d, list):
    print("<unreadable>"); raise SystemExit(0)
print(",".join(sorted(str(x.get("Name","")) for x in d if isinstance(x, dict))))' 2> /dev/null)" || orc=$?
    if [ "$orc" != 0 ]; then
        printf '<unreadable>'
        return 0
    fi
    # 多行 = 内部不止一个分支输出过 ⇒ 取值不可信
    if [ "$(printf '%s' "$out" | wc -l | tr -d ' ')" != 0 ]; then
        printf '<unreadable>'
        return 0
    fi
    case "$out" in
        *'<unreadable>'*) printf '<unreadable>'; return 0 ;;
    esac
    printf '%s' "$out"
}

# stats_key_of <base> <hdr> <vault> —— 回 "null"（无该键）/ JSON 片段（有该键）/
# "<unreadable>"（请求或解析失败）。三者必须可区分：后两者塌成一个值就会让
# 「服务没答上来」被读成「表已经删干净了」。
stats_key_of() {
    local b="$1" h="$2" v="$3" body="" tmp code
    # ⛔ 必须先看 HTTP 状态码：503 的 `{"detail":"Service Unavailable"}` 也是合法
    #    JSON，取不到本 vault 的键 ⇒ 打印 null ⇒ 被读成「表已经删干净了」。
    #    「服务没答上来」和「真的没有表」必须是两个不同的值。
    tmp="$(mktemp "${TMPDIR:-/tmp}/j01stats-XXXXXX")"
    code="$(curl -sS --max-time 30 -o "$tmp" -w '%{http_code}' "$b/api/v1/index/stats" -H "$h" 2> /dev/null || printf '000')"
    if [ "$code" != 200 ]; then
        rm -f "$tmp"
        printf '<unreadable:http=%s>' "$code"
        return 0
    fi
    body="$(cat "$tmp" 2> /dev/null || printf '')"
    rm -f "$tmp"
    [ -n "$body" ] || { printf '<unreadable:empty-body>'; return 0; }
    printf '%s' "$body" | py -c 'import sys,json
try:
    d = json.load(sys.stdin)
except Exception:
    print("<unreadable>"); raise SystemExit(0)
if not isinstance(d, dict):
    print("<unreadable>"); raise SystemExit(0)
# ⛔ 整个响应是空 dict ⇒ 上游 client 不可用（index.py:85 在那种情况下回 200 {}）。
#    那是「问不出来」，不是「没有表」。标成不可确认，不许被读成删除成功。
if not d:
    print("<unconfirmable:empty-stats>"); raise SystemExit(0)
key = sys.argv[1]
val = d.get(key)
if val is None:
    sub = d.get("vaults")
    if isinstance(sub, dict):
        val = sub.get(key)
print(json.dumps(val))' "$v" 2> /dev/null || printf '<unreadable>'
}

# up 未发生的证明：**两个合取项都要真判** ——
#   ① docker compose 项目名集合与跑前**同**（跑前那次在 do_run 里取，
#      取不到时是哨兵串而不是空串）；
#   ② 没有 cls-<vault>-backend 容器。
# 原先只判了 ②，却在 reason 里写「no-up-happened」这个更宽的主张（名实不符）。
live_assert_no_up_happened() {
    local rc=0 reason="" after b
    if ! command -v docker > /dev/null 2>&1; then
        emit_assert rollback-down 2 "docker-cli-absent"
        return 0
    fi
    after="$(docker_project_set)"
    local pnames="" prc=0
    pnames="$(docker ps -a --format '{{.Names}}' 2> /dev/null)" || prc=$?
    if [ "$prc" != 0 ]; then
        emit_assert rollback-down 1 "docker-ps-unreadable(rc=$prc)"
        return 0
    fi
    b="$(printf '%s\n' "$pnames" | grep -c "^cls-$VAULT_NAME-backend\$" || :)"
    log "# rollback: compose_projects_before=[$DOCKER_PROJECTS_BEFORE] after=[$after] our_container_count=$b"
    case "$DOCKER_PROJECTS_BEFORE" in
        '<not-captured>' | '<unreadable>' | '<docker-cli-absent>')
            rc=1; reason="project-set-before-unavailable:$DOCKER_PROJECTS_BEFORE"
            ;;
        *)
            if [ "$after" != "$DOCKER_PROJECTS_BEFORE" ]; then
                rc=1; reason="compose-project-set-changed"
            fi
            ;;
    esac
    if [ "$rc" = 0 ] && [ "${b:-0}" != 0 ]; then
        rc=1; reason="container-cls-$VAULT_NAME-backend-exists"
    fi
    if [ "$rc" = 0 ]; then
        emit_assert rollback-down 0 "no-up-happened(project-set-identical+no-container)"
    else
        emit_assert rollback-down 1 "$reason"
    fi
    return 0
}

# 授权态：真 up → 首索引 → 写探针笔记 → refresh-changed → search_notes 检回
#         → /index/stats → DELETE /index/<vault> → 再 stats → down
# ⛔ 所有 curl 都带 --max-time：后端起不来时无超时的 curl 会把整条链吊死，
#    而吊死既不是绿也不是红，它是「没有结论」。
live_up_and_probe() {
    local key base hdr
    key="$(cat "$VAULT/.obsidian/cls-internal-key.txt" 2> /dev/null || printf '')"
    base="http://127.0.0.1:$PORT"
    hdr="X-CLS-Internal-Key: $key"

    # ⛔ 不再调第二趟 `deploy-vault.sh --activate`：`install-vault.sh:66` 对已存在
    #    的目标一律 `exit 66`（防误伤学习数据），deploy 随之退 72 —— 同一个 vault
    #    上跑第二趟部署**必然失败**，那条授权路径按原设计永远走不通（实测 rc=72）。
    #    deploy 没有跳过 install 的开关，而本卡不得改 deploy。
    #    ⇒ up 由 harness 自己发起（**必带 `-p cls-<vault>`**），健康与首索引改为
    #      **直接观测 HTTP 端点**，而不是读 deploy 的自述阶段行 —— 观测比自述强。
    local urc=0
    UP_ATTEMPTED=1
    docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
        -p "cls-$VAULT_NAME" --project-directory "$HARNESS" up -d backend >> "$LOG" 2>&1 || urc=$?
    step up-instance "$urc"

    # backend-ready：轮询 /api/v1/vault/current，要求它自报的 vault 名**就是本实例**。
    # ⛔ 不接受「200 就算好」：别的实例也会 200。
    local bdl bnow brem bct brc=1 breason="vault-current-never-reported-our-vault"
    if [ "$urc" != 0 ]; then
        breason="compose-up-exit=$urc"
    else
        bdl=$(( $(date +%s) + LANCE_TIMEOUT ))
        while :; do
            bnow=$(date +%s); brem=$((bdl - bnow))
            [ "$brem" -gt 0 ] || break
            bct=10; [ "$bct" -le "$brem" ] || bct="$brem"
            if curl -sS --fail --max-time "$bct" "$base/api/v1/vault/current" -H "$hdr" 2> /dev/null \
                | py -c 'import sys,json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
if not isinstance(d, dict):
    sys.exit(1)
want = sys.argv[1]
for k in ("vault_name", "vault", "active_vault", "name"):
    if str(d.get(k) or "") == want:
        print("OK %s=%s" % (k, want)); sys.exit(0)
sys.exit(1)' "$VAULT_NAME" >> "$LOG" 2>&1; then
                brc=0; breason=""
                break
            fi
            bnow=$(date +%s); brem=$((bdl - bnow))
            [ "$brem" -gt 0 ] || break
            bct=3; [ "$bct" -le "$brem" ] || bct="$brem"
            sleep "$bct"
        done
    fi
    emit_assert backend-ready "$brc" "$breason"

    # first-index：轮询 /api/v1/health/lancedb，要求顶层 status 就绪且 table_count 可读。
    local fdl fnow frem fct frc=1 freason="lancedb-health-never-ready"
    if [ "$brc" != 0 ]; then
        frc=2; freason="backend-not-ready"
    else
        fdl=$(( $(date +%s) + LANCE_TIMEOUT ))
        while :; do
            fnow=$(date +%s); frem=$((fdl - fnow))
            [ "$frem" -gt 0 ] || break
            fct=10; [ "$fct" -le "$frem" ] || fct="$frem"
            if curl -sS --fail --max-time "$fct" "$base/api/v1/health/lancedb" -H "$hdr" 2> /dev/null \
                | py -c 'import sys,json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
if not isinstance(d, dict):
    sys.exit(1)
st = str(d.get("status") or "").lower()
if st in ("error", "failed", "degraded", ""):
    sys.exit(1)
if "table_count" not in d:
    sys.exit(1)
print("OK status=%s table_count=%s" % (st, d.get("table_count")))
sys.exit(0)' >> "$LOG" 2>&1; then
                frc=0; freason=""
                break
            fi
            fnow=$(date +%s); frem=$((fdl - fnow))
            [ "$frem" -gt 0 ] || break
            fct=3; [ "$fct" -le "$frem" ] || fct="$frem"
            sleep "$fct"
        done
    fi
    emit_assert first-index "$frc" "$freason"

    # 探针笔记 + 唯一 token
    local token note
    token="J01TOKEN$TS"
    note="节点/j01-probe-$TS.md"
    mkdir -p "$VAULT/节点"
    printf '# j01 probe\n\n%s\n' "$token" > "$VAULT/$note"
    curl -sS --max-time 30 -X POST "$base/api/v1/index/refresh-changed" -H "$hdr" \
        -H 'Content-Type: application/json' \
        -d "$(py -c 'import json,sys;print(json.dumps({"paths":[sys.argv[1]]}))' "$note")" \
        >> "$LOG" 2>&1 || :

    # 轮询检回：逐字段判（file_path 结尾 + source_status 非 error），
    # ⛔ 不用「results 非空」—— 那会把「搜到了别的笔记」也算成通过。
    # ⛔ 每一跳的 curl 超时与 sleep 都要**夹在剩余时间之内**，否则
    #    CLS_DEPLOY_LANCE_READY_TIMEOUT=1 也能跑掉 33 秒 —— 那条上限就是摆设。
    local deadline now remain ct st hit=1 hreason="search-notes-no-matching-field"
    deadline=$(( $(date +%s) + LANCE_TIMEOUT ))
    while :; do
        now=$(date +%s)
        remain=$((deadline - now))
        [ "$remain" -gt 0 ] || break
        ct=30
        [ "$ct" -le "$remain" ] || ct="$remain"
        # ⛔ `--fail` 必须加：HTTP 503 的正文里照样能挂着一条 file_path 对得上的结果，
        #    只解析正文就会把「服务挂了」读成「搜到了」。
        if curl -sS --fail --max-time "$ct" -X POST "$base/mcp/tools/search_notes" -H "$hdr" \
            -H 'Content-Type: application/json' \
            -d "$(py -c 'import json,sys;print(json.dumps({"query":sys.argv[1],"max_results":5}))' "$token")" 2> /dev/null \
            | py -c 'import sys,json
needle = sys.argv[1]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
# ⛔ 顶层的错误状态必须先看：一个 `source_status: "error"` 的响应里照样能挂着
#    一条 file_path 对得上的结果项，只读 item 的状态就会把它当成命中。
if isinstance(d, dict):
    # ⛔ 两个顶层字段**各自**判，不用 `or` 串起来：`source_status="ok"` 会把
    #    `status="error"` 整个短路掉。
    for k in ("source_status", "status", "state"):
        if str(d.get(k) or "").lower() in ("error", "failed", "degraded"):
            sys.exit(1)
    if d.get("error") or d.get("detail"):
        sys.exit(1)
items = d.get("results") or d.get("items") or (d if isinstance(d, list) else [])
for it in items:
    if not isinstance(it, dict):
        continue
    fp = str(it.get("file_path") or "")
    # ⛔ 缺字段 ≠ 没问题：`or ""` 会把「没有这个字段」变成「状态是空串」从而放行。
    if "source_status" not in it:
        continue
    raw = it.get("source_status")
    # 缺字段、None、空串都不算「状态正常」——它们是「没说」，不是「没问题」。
    if raw is None or str(raw).strip() == "":
        continue
    st = str(raw)
    if fp.endswith(needle) and st.lower() not in ("error", "failed"):
        print("HIT %s %s" % (fp, st))
        sys.exit(0)
sys.exit(1)' "j01-probe-$TS.md" >> "$LOG" 2>&1; then
            hit=0; hreason=""
            break
        fi
        now=$(date +%s)
        remain=$((deadline - now))
        [ "$remain" -gt 0 ] || break
        st=3
        [ "$st" -le "$remain" ] || st="$remain"
        sleep "$st"
    done
    emit_assert search-hit "$hit" "$hreason"

    # table-diff：三态齐（**删之前有键** → DELETE 200 → 删之后无键），只看本 vault 的
    # stats 键。⛔ 不声称「首索引前无键」—— 部署的 activate 步之前后端根本没起，
    # 没有 /index/stats 可查，那个状态结构上采集不到（已登记）。
    # （canvas-lancedb 是 external 共享卷，全库表集合不归本 vault 管 ——
    #  草案 §五待裁，这是产品口径不是偷懒）。
    # ⛔ before / after 两侧用**同一个**取值函数，且两侧都要分清「取不到」与
    #    「取到了但是 null」：原先 after 取空会静默落到 else 判绿。
    local before after drop trc=0 treason=""
    before="$(stats_key_of "$base" "$hdr" "$VAULT_NAME")"
    # ⛔ curl 在连接失败时**既**把 `%{http_code}`（000）打到 stdout **又**非零退出，
    #    `|| printf '000'` 于是再追加一个 ⇒ 捕获到 "000000" 这种不可能的值。
    #    先捕获、再单独判 rc。
    local dcrc=0
    drop="$(curl -sS --max-time 60 -o /dev/null -w '%{http_code}' -X DELETE "$base/api/v1/index/$VAULT_NAME" -H "$hdr" 2> /dev/null)" || dcrc=$?
    case "$drop" in
        '' | *[!0-9]*) drop="000" ;;
    esac
    [ "$dcrc" = 0 ] || log "# table-diff: DELETE 的 curl 非零退出 rc=${dcrc}（http_code=${drop}）"
    after="$(stats_key_of "$base" "$hdr" "$VAULT_NAME")"
    log "# table-diff: vault=$VAULT_NAME before=$before delete_http=$drop after=$after"
    case "$before$after" in
        *'<unreadable'* | *'<unconfirmable'*)
            trc=1; treason="stats-unreadable-or-unconfirmable(before=$before,after=$after)" ;;
    esac
    if [ "$trc" = 1 ]; then
        :
    elif [ "$before" = "null" ]; then
        trc=1; treason="no-stats-key-before-delete"
    elif [ "$drop" = 404 ]; then
        trc=1; treason="delete-404-see-P1-B"
    elif [ "$drop" != 200 ]; then
        trc=1; treason="delete-http=$drop"
    elif [ "$after" != "null" ]; then
        trc=1; treason="stats-key-survives-delete"
    fi
    emit_assert table-diff "$trc" "$treason"

    # ⛔ 先记下「容器确实起来过」：否则 `rollback-down` 在 up 根本没成功时也会绿
    #    —— 它判的是「拆干净了」，而「从来没起」与「起了又拆干净」在事后是同一个
    #    观测结果。把「起过」这一半单独记下来，判据才等于它的名字。
    local seen_up=0 snames="" src2=0
    snames="$(docker ps -a --format '{{.Names}}' 2> /dev/null)" || src2=$?
    if [ "$src2" = 0 ]; then
        seen_up="$(printf '%s\n' "$snames" | grep -c "^cls-$VAULT_NAME-" || :)"
    else
        seen_up="<unreadable>"
    fi
    log "# rollback: down 之前本项目容器数=$seen_up"

    # 回滚：逐字同 deploy-vault.sh:3132-3133 形态，**必带 -p**（去掉它 = 拆光）
    local dnrc=0 left after_set
    docker compose -f "$HARNESS/docker-compose.yml" --env-file "$ENV_FILE" \
        -p "cls-$VAULT_NAME" --project-directory "$HARNESS" down >> "$LOG" 2>&1 || dnrc=$?
    # 同 teardown：查询失败 ≠ 零容器。问不出来就不许判绿。
    local lnames="" lrc2=0
    lnames="$(docker ps -a --format '{{.Names}}' 2> /dev/null)" || lrc2=$?
    if [ "$lrc2" != 0 ]; then
        left="<unreadable>"
    else
        left="$(printf '%s\n' "$lnames" | grep -c "^cls-$VAULT_NAME-backend\$" || :)"
    fi
    after_set="$(docker_project_set)"
    log "# rollback: down_rc=$dnrc leftover_container=$left projects_before=[$DOCKER_PROJECTS_BEFORE] projects_after=[$after_set]"
    # 授权态这条路径也要做与未授权分支同样的哨兵检查：两次都取不到项目集合时
    # `before == after` 恒成立，那不是「恢复了」，那是「两次都没问出来」。
    local pset_bad=0
    case "$DOCKER_PROJECTS_BEFORE$after_set" in
        *'<not-captured>'* | *'<unreadable>'* | *'<docker-cli-absent>'*) pset_bad=1 ;;
    esac
    if [ "$left" = "<unreadable>" ] || [ "$seen_up" = "<unreadable>" ]; then
        emit_assert rollback-down 1 "docker-ps-unreadable(rc=$lrc2,before=$seen_up)"
    elif [ "${seen_up:-0}" = 0 ]; then
        # 没起来过就没什么可拆的 —— 这时候判绿等于用「没发生」冒充「拆干净了」。
        emit_assert rollback-down 1 "no-container-was-ever-up(before=$seen_up)"
    elif [ "$pset_bad" = 1 ]; then
        emit_assert rollback-down 1 "project-set-unreadable(before=$DOCKER_PROJECTS_BEFORE after=$after_set)"
    elif [ "$dnrc" != 0 ]; then
        emit_assert rollback-down 1 "down-rc=$dnrc"
    elif [ "${left:-0}" != 0 ]; then
        emit_assert rollback-down 1 "container-survives-down"
    elif [ "$after_set" != "$DOCKER_PROJECTS_BEFORE" ]; then
        emit_assert rollback-down 1 "compose-project-set-not-restored"
    else
        emit_assert rollback-down 0 "project-set-restored+no-container"
    fi
    return 0
}

# ── run ───────────────────────────────────────────────────────────────────
do_run() {
    TS="$(date +%Y%m%dT%H%M%S)"
    [ -n "$HARNESS" ] || HARNESS="$(pwd)"
    # ⛔ 裸赋值 `X="$(cd … && pwd)"` 在 cd 失败时把非 0 传给赋值本身，
    #    `set -e` 当场杀脚本 —— 用户只看到 bash 自己的 cd 报错，看不到 rc=64。
    HARNESS="$(cd "$HARNESS" 2> /dev/null && pwd)" || die "--harness 不是可进入的目录"
    [ -f "$HARNESS/scripts/deploy-vault.sh" ] || die "--harness 不含 scripts/deploy-vault.sh: $HARNESS"
    [ -x "$HARNESS/backend/.venv/bin/python" ] || die "harness venv 缺: $HARNESS/backend/.venv/bin/python"

    # --port：先证它是数字，再按**数值**比黑名单（`07691` 字符串不等但同口）
    local pn q
    pn="$(num_of "$PORT")"
    [ -n "$pn" ] || die "--port 必须是十进制数字（给的是 '$PORT'）"
    [ "$pn" -ge 1 ] && [ "$pn" -le 65535 ] || die "--port 越界: $pn"
    PORT="$pn"
    for q in $J01_FORBIDDEN_API_PORTS; do
        if [ "$PORT" = "$(num_of "$q")" ]; then
            die "--port $PORT 在黑名单内（与既有服务冲突）"
        fi
    done
    # lsof 三态：出错**不当空闲**（仿 deploy-vault.sh:822-826）
    if command -v lsof > /dev/null 2>&1; then
        local lrc=0
        lsof -nP -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1 || lrc=$?
        case "$lrc" in
            0) die "--port $PORT 已被占用" ;;
            1) : ;;
            *) die "lsof 探测 --port $PORT 出错(rc=$lrc)，不敢断言空闲" ;;
        esac
    fi
    # Lance 轮询上限：非数字会让 $(( )) 在 set -e 下炸掉整条 live 链
    LANCE_TIMEOUT="$(num_of "${CLS_DEPLOY_LANCE_READY_TIMEOUT:-120}")"
    if [ -z "$LANCE_TIMEOUT" ] || [ "$LANCE_TIMEOUT" = 0 ]; then
        printf 'j01_e2e: WARN CLS_DEPLOY_LANCE_READY_TIMEOUT 不是正整数, 回落 120\n' >&2
        LANCE_TIMEOUT=120
    fi

    # ⛔ 缺省证据目录也要每跑唯一：同秒起两跑会共享 LOG / 快照 / SHA256SUMS 并
    #    互相截断覆盖，而进程内的断言计数看不见这种混写。
    RUN_ID="$(py -c 'import random,string
print("".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6)))')"
    [ -n "$EVDIR" ] || EVDIR="$HARNESS/_bmad-output/审查/evidence-g211-j01/run-$TS-$MODE-$RUN_ID"
    mkdir -p "$EVDIR" || die "建 --evidence-dir 失败: $EVDIR"
    EVDIR="$(cd "$EVDIR" 2> /dev/null && pwd)" || die "--evidence-dir 不是可进入的目录"
    LOG="$EVDIR/j01-$TS.txt"
    : > "$LOG"

    write_header

    # ⛔ S0 必须在 mktemp **之前**拍：S0 的含义是「我们动手之前的世界」。
    #    拍在 mktemp 之后，$ROOT 已经存在，而 S1 是拆除之后拍的 ⇒ 两边
    #    root_exists 必然 yes→no、恒 diff，判据永远红在自己身上而不是被测对象
    #    上（实测过一轮）。此刻 ROOT="" ⇒ root_exists=no、root_tree=sha(空)，
    #    与「拆干净之后」完全同值；拆不干净则 S1 的 root_tree 非空 ⇒ 判红。
    snapshot S0

    if [ "$MODE" = live ]; then
        DOCKER_PROJECTS_BEFORE="$(docker_project_set)"
        log "# docker: 跑前 compose 项目集合=[$DOCKER_PROJECTS_BEFORE]"
    fi

    ROOT="$(mktemp -d "${TMPDIR:-/tmp}/j01-XXXXXX")"
    ROOT_ID="$(path_identity "$ROOT")"
    trap on_exit EXIT
    # ⛔ 只用秒级时间戳 ⇒ 同一秒起的两个 live 会拿到**同一个** VAULT_NAME，于是共用
    #    `cls-<name>` 项目、容器名与 stats 分桶：任一跑的 DELETE / down 都会清掉另一跑。
    #    追加 6 位小写字母数字随机后缀（名字必须是 sanitize_vault_id 的不动点 ⇒
    #    只能小写字母 + 数字，不能有 `-` / `_` / 大写）。
    # ⛔ 不用 `tr -dc … < /dev/urandom | head -c 6`：`head` 取够就退出，上游 `tr`
    #    收到 SIGPIPE，`set -o pipefail` 把整条命令替换的 rc 变成 141，`set -e`
    #    当场杀掉脚本（实测：13 条断言一条都没打出来就死了）。改成不经管道的取法。
    VAULT_NAME="j01tw$(date +%Y%m%d%H%M%S)$(py -c 'import random,string
print("".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6)))')"
    VAULT="$ROOT/vaults/$VAULT_NAME"
    ENV_FILE="$ROOT/env/.env.$VAULT_NAME"
    DEPLOY_EV="$ROOT/ev"
    log "# vault_name=$VAULT_NAME root=$ROOT"

    # ── 断言 1：throwaway 保护（拆除的前置）
    assert_throwaway_safe

    # ── 步 1-6：真跑 deploy-vault.sh
    # fixture：--apply（无 --activate）；live：--apply --activate（产出 compose-config）
    # ⛔ 一律 `env -u CLS_DEPLOY_ALLOW_DOCKER_UP`：这一趟**绝不允许** up。
    local dargs drc=0
    if [ "$MODE" = live ]; then
        dargs="--apply --activate"
    else
        dargs="--apply"
    fi
    log "# deploy: $HARNESS/scripts/deploy-vault.sh --vault $VAULT --harness $HARNESS --port $PORT --env-dir $ROOT/env --evidence-dir $DEPLOY_EV $dargs"
    env -u CLS_DEPLOY_ALLOW_DOCKER_UP "$HARNESS/scripts/deploy-vault.sh" \
        --vault "$VAULT" --harness "$HARNESS" --port "$PORT" \
        --env-dir "$ROOT/env" --evidence-dir "$DEPLOY_EV" $dargs >> "$LOG" 2>&1 || drc=$?
    step deploy "$drc"
    # deploy 的原始退出码是 0/64/71..76，不是本脚本的三态 —— 归一后把原值进 reason。
    if [ "$drc" = 0 ]; then
        emit_assert deploy-rc 0 ""
    else
        emit_assert deploy-rc 1 "deploy-vault-exit=$drc"
    fi

    # ── 断言 3：verify（步 4 的校验器真跑过且 rc 0）
    # ⛔ 命令替换的裸赋值必须带 `|| x=""`：$DEPLOY_EV 不存在时 find 非 0，
    #    再叠 pipefail，`set -e` 会在这一行**直接终止整个脚本** —— 日志里只会
    #    有 2 条 assert 而不是 13，而「少一条即作废」的自检自己都跑不到。
    local vrc=0 vreason="" dfile="" vfile=""
    dfile="$(find "$DEPLOY_EV" -maxdepth 1 -name 'deploy-*.txt' 2> /dev/null | sort | tail -1)" || dfile=""
    vfile="$(find "$DEPLOY_EV" -maxdepth 1 -name 'verify-*.txt' 2> /dev/null | sort | tail -1)" || vfile=""
    if [ -z "$dfile" ] || [ ! -f "$dfile" ]; then
        vrc=1; vreason="deploy-evidence-missing"
    elif [ -z "$vfile" ] || [ ! -f "$vfile" ]; then
        vrc=1; vreason="verify-report-missing"
    elif ! grep -q '\[4/6\] verify: OK' "$dfile"; then
        vrc=1; vreason="verify-step-not-OK"
    elif ! grep -q '校验器 rc 0' "$dfile"; then
        vrc=1; vreason="verifier-rc-not-0"
    fi
    emit_assert verify-rc "$vrc" "$vreason"

    # ── 断言 4/5：no-old-secret / no-abs-path
    SCAN_REF_ENVS="$(printf '%s\n%s\n' "$HARNESS/.env" "$HARNESS/backend/.env")"
    SCAN_BASELINE="$HARNESS/canvas-vault"
    scan_tree "$ROOT" "$VAULT"
    # 三处同值（deploy :2476-2479 的契约）+ 0600：作为 no-old-secret 的补充证据行
    if [ -f "$ENV_FILE" ] && [ -f "$VAULT/.obsidian/cls-internal-key.txt" ]; then
        local k1 k2 m1 m2
        k1="$(sed -n 's/^INTERNAL_API_KEY=//p' "$ENV_FILE" | tail -1 | tr -d '\n' | sha_stdin)"
        k2="$(tr -d '\n' < "$VAULT/.obsidian/cls-internal-key.txt" | sha_stdin)"
        m1="$(py -c 'import os,sys;print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$ENV_FILE" 2> /dev/null || printf '?')"
        m2="$(py -c 'import os,sys;print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$VAULT/.obsidian/cls-internal-key.txt" 2> /dev/null || printf '?')"
        log "# secret: env_key_sha=$k1 keyfile_sha=$k2 same=$([ "$k1" = "$k2" ] && echo yes || echo no) mode_env=$m1 mode_keyfile=$m2"
    fi

    # ── 断言 6：隔离预检
    ISOLATION_RC=1
    if [ "$MODE" = live ]; then
        local cfg=""
        cfg="$(find "$DEPLOY_EV" -maxdepth 1 -name 'compose-config-*.txt' 2> /dev/null | sort | tail -1)" || cfg=""
        if [ -n "$cfg" ] && [ -f "$cfg" ]; then
            isolation_preflight "$cfg"
        else
            emit_assert isolation-preflight 1 "compose-config-missing"
            ISOLATION_RC=1
        fi
    else
        emit_assert isolation-preflight 2 "no-compose-config-in-fixture"
        ISOLATION_RC=2
    fi

    # ── 断言 7-11：live 半边
    if [ "$MODE" != live ]; then
        emit_assert backend-ready 2 "fixture-mode"
        emit_assert first-index 2 "fixture-mode"
        emit_assert search-hit 2 "fixture-mode"
        emit_assert table-diff 2 "fixture-mode"
        emit_assert rollback-down 2 "no-up-attempted-in-fixture"
    elif [ "$ISOLATION_RC" != 0 ]; then
        # ⛔ 预检红 ⇒ 结构上到不了 up：真 up 的唯一调用点在下面的
        #    `else` 分支里，本分支根本不含 docker compose up。
        emit_assert backend-ready 2 "isolation-preflight-red"
        emit_assert first-index 2 "isolation-preflight-red"
        emit_assert search-hit 2 "isolation-preflight-red"
        emit_assert table-diff 2 "isolation-preflight-red"
        live_assert_no_up_happened
    elif [ "$ALLOW_UP" != 1 ] || [ "$USER_ALLOW_UP_ENV" != 1 ]; then
        local why="missing:"
        [ "$ALLOW_UP" = 1 ] || why="$why--allow-up"
        [ "$USER_ALLOW_UP_ENV" = 1 ] || why="${why}+CLS_DEPLOY_ALLOW_DOCKER_UP=1"
        emit_assert backend-ready 2 "not-authorized($why)"
        emit_assert first-index 2 "not-authorized($why)"
        emit_assert search-hit 2 "not-authorized($why)"
        emit_assert table-diff 2 "not-authorized($why)"
        live_assert_no_up_happened
    else
        live_up_and_probe
    fi

    # ── ⛔ 部署证据必须在**拆除之前**扫 + 复制（$DEPLOY_EV 在 $ROOT 里面）
    stage_deploy_evidence

    # ── 拆除 → S1 → 断言 12
    teardown_root
    snapshot S1
    local srcd=0 sreason="" l
    if [ "$SNAPSHOT_BAD_N" != 0 ] || [ "$SNAPSHOT_OK_N" != 2 ]; then
        # 采集不可信 ⇒ 「零差异」这句话没有内容。
        srcd=1; sreason="snapshot-collection-unreliable(bad=$SNAPSHOT_BAD_N taken=$SNAPSHOT_OK_N)"
    elif [ "$KEEP_ROOT" = 1 ]; then
        # --keep-root 是调试开关；保留了 $ROOT 就必然 S0≠S1。这时候判红会让
        # 红的原因与被测性质无关（门红在自己身上）。如实 SKIP 并点名该开关。
        srcd=2; sreason="keep-root-flag-retains-throwaway-root"
        log "# state-diff: --keep-root 指定 ⇒ 不做 S0/S1 比较"
    elif ! diff "$EVDIR/snapshot-S0.txt" "$EVDIR/snapshot-S1.txt" > "$EVDIR/state-diff.txt" 2>&1; then
        srcd=1
        sreason="snapshot-differs(see state-diff.txt)"
        log "# state-diff 非空:"
        while IFS= read -r l; do log "#   $l"; done < "$EVDIR/state-diff.txt"
    fi
    emit_assert state-diff "$srcd" "$sreason"

    # ── 断言 13：主日志复查 + 合并部署证据的暂存结果后 emit
    emit_evidence_redacted

    # ── 收尾
    local crc=0
    verify_assert_completeness || crc=1
    local final=0
    if [ "$FAILED_N" != 0 ] || [ "$crc" != 0 ]; then
        final=1
    fi
    log "# summary failed=$FAILED_N skipped=$SKIPPED_N completeness_rc=$crc"
    log "rc=$final"
    # SHA256SUMS 最后写：此刻 $LOG 已经完整（含上面两行）。
    write_sha256sums
    # ⛔ 封盘：此后 EXIT trap 里的 teardown 还会 log（--keep-root 时必然如此），
    #    再往 $LOG 追加就会让刚算出来的校验和对不上。封盘后 log 只走 stdout。
    LOG=""
    return "$final"
}

# ── scan 子命令 ───────────────────────────────────────────────────────────
do_scan() {
    local dir="$1"
    [ -d "$dir" ] || die "scan: 目录不存在: $dir"
    [ -n "$HARNESS" ] || HARNESS="$(pwd)"
    HARNESS="$(cd "$HARNESS" 2> /dev/null && pwd)" || die "--harness 不是可进入的目录"
    [ -x "$HARNESS/backend/.venv/bin/python" ] || die "harness venv 缺: $HARNESS/backend/.venv/bin/python"
    TS="$(date +%Y%m%dT%H%M%S)"
    LOG=""
    log "# j01_e2e.sh scan dir=$dir ts=$TS"
    log "# rc 约定: 0=通过 1=失败(红) 2=跳过(不红, 必带 reason=)"
    scan_tree "$dir" "$dir"
    log "rc=$SCAN_LAST_RC"
    return "$SCAN_LAST_RC"
}

# ── 参数 ──────────────────────────────────────────────────────────────────
usage() {
    cat << 'USAGE'
用法:
  j01_e2e.sh run  [--mode fixture|live] [--allow-up] [--harness DIR] [--port N]
                  [--evidence-dir DIR] [--keep-root]
  j01_e2e.sh scan <DIR> [--ref-env FILE]... [--source-baseline DIR] [--harness DIR]
  j01_e2e.sh isolation-check <compose-config.yml> [--harness DIR]
                  对任意一份 compose config 跑隔离预检（与 run --mode live
                  走的是**同一个函数**）。存在的理由是验伪锚：门必须能在
                  「已隔离」的配置上变绿、在现网配置上变红, 且在输入面为空时
                  fail-closed（「没东西可看就放行」和恒红一样没用）。
USAGE
}

[ $# -ge 1 ] || { usage >&2; exit 64; }
SUB="$1"; shift

case "$SUB" in
    run)
        while [ $# -gt 0 ]; do
            case "$1" in
                --mode) need_val "$1" $#; MODE="$2"; shift 2 ;;
                --allow-up) ALLOW_UP=1; shift ;;
                --harness) need_val "$1" $#; HARNESS="$2"; shift 2 ;;
                --port) need_val "$1" $#; PORT="$2"; shift 2 ;;
                --evidence-dir) need_val "$1" $#; EVDIR="$2"; shift 2 ;;
                --keep-root) KEEP_ROOT=1; shift ;;
                -h | --help) usage; exit 0 ;;
                *) die "未知参数: $1" ;;
            esac
        done
        case "$MODE" in
            fixture | live) : ;;
            *) die "--mode 只能是 fixture 或 live（给的是 '$MODE'）" ;;
        esac
        if [ "$ALLOW_UP" = 1 ] && [ "$MODE" != live ]; then
            die "--allow-up 只在 --mode live 下有意义"
        fi
        do_run
        ;;
    scan)
        [ $# -ge 1 ] || die "scan 需要一个目录参数"
        SCAN_DIR="$1"; shift
        while [ $# -gt 0 ]; do
            case "$1" in
                --ref-env) need_val "$1" $#; SCAN_REF_ENVS="$(printf '%s\n%s' "$SCAN_REF_ENVS" "$2")"; shift 2 ;;
                --source-baseline) need_val "$1" $#; SCAN_BASELINE="$2"; shift 2 ;;
                --harness) need_val "$1" $#; HARNESS="$2"; shift 2 ;;
                -h | --help) usage; exit 0 ;;
                *) die "未知参数: $1" ;;
            esac
        done
        do_scan "$SCAN_DIR"
        ;;
    isolation-check)
        [ $# -ge 1 ] || die "isolation-check 需要一个 compose config 文件参数"
        IC_FILE="$1"; shift
        while [ $# -gt 0 ]; do
            case "$1" in
                --harness) need_val "$1" $#; HARNESS="$2"; shift 2 ;;
                -h | --help) usage; exit 0 ;;
                *) die "未知参数: $1" ;;
            esac
        done
        [ -f "$IC_FILE" ] || die "isolation-check: 文件不存在: $IC_FILE"
        [ -n "$HARNESS" ] || HARNESS="$(pwd)"
        HARNESS="$(cd "$HARNESS" 2> /dev/null && pwd)" || die "--harness 不是可进入的目录"
        [ -x "$HARNESS/backend/.venv/bin/python" ] || die "harness venv 缺: $HARNESS/backend/.venv/bin/python"
        LOG=""
        log "# j01_e2e.sh isolation-check file=$IC_FILE"
        log "# rc 约定: 0=通过 1=失败(红) 2=跳过(不红, 必带 reason=)"
        ISOLATION_RC=1
        isolation_preflight "$IC_FILE"
        log "rc=$ISOLATION_RC"
        exit "$ISOLATION_RC"
        ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; exit 64 ;;
esac
