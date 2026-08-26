#!/usr/bin/env bash
# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29, CARD-C1a per-vault 化)。
# 只做两件事: per-vault 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
set -uo pipefail

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"

PY="$WT/backend/.venv/bin/python"
[ -x "$PY" ] || PY="/usr/bin/python3"   # venv 缺失兜底 (runner 仅 stdlib)

# 参数解析: 只认全称 --vault / --vault=; runner argparse 已设
# allow_abbrev=False 与此同源 (Codex-C1a F1: argparse 缩写 --v 曾让锁
# 与 runner 指向不同 vault)。取最后一次出现, 与 argparse 语义一致。
VAULT_ARG=""
prev=""
for a in "$@"; do
    [ "$prev" = "--vault" ] && VAULT_ARG="$a"
    case "$a" in --vault=*) VAULT_ARG="${a#--vault=}";; esac
    prev="$a"
done
VAULT_ARG="${VAULT_ARG:-$REPO/canvas-vault}"

# 锁 key 与 runner state 同源 (send_bark.vault_key + symlink resolve)。
# 用 -c 免 heredoc 的 TMPDIR 依赖; 算不出 key 即整体不跑 (fail hard, 78)
# — runner 用同一解释器, key 都算不出 runner 也必跑不了; 回退 basename
# 会造成中文/长名锁分域 (Codex-C1a F1)。
KEY=$("$PY" -c '
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[2])
import send_bark
p = Path(sys.argv[1])
print(send_bark.vault_key((p.resolve() if p.exists() else p).name))
' "$VAULT_ARG" "$WT/scripts" 2>/dev/null) && [ -n "$KEY" ] || {
    echo "PREFLIGHT-FAIL: lock key derivation failed (python/send_bark unavailable)" >&2
    exit 78
}
LOCK="$REPO/backups/.daily-review.$KEY.lock"

mkdir -p "$REPO/backups"

# 锁 ownership token = "pid + 进程启动时刻" (Codex-C1a B5/round3): 光靠
# pid, 被系统重用给长寿命无关进程时锁会被永久误判为活。lstart 是本地化
# 文本 — TZ 与 locale 都必须钉死 (round4/5: 混合 TZ 或 wrapper 的 zh_CN
# vs 手工 C locale 会让同一活进程 token 漂移而被误判死锁), LC_ALL=C
# 优先级最高。/bin/ps 绝对路径 + 空输出/失败即报错 (round6: 裸 ps 依赖
# PATH, printf 又掩盖失败 — PATH 异常侧会产出 "<pid> " 残缺 token,
# 与正常侧不等而误回收活锁)。
# 有界超时 (round7/8): /bin/ps 挂死不得无限阻塞 — perl alarm(5) 跨 exec
# 保留 (POSIX), 5s 后 SIGALRM 终止 ps → 替换失败 → return 1 (fail-closed,
# 与 migrate 侧 subprocess timeout=5 对称)。exec 直通 ps 的 stdout, 输出
# 字节与直接调用完全一致。⚠ 继承环境加固 (round8): 父环境把 ALRM 置
# SIG_IGN 或阻塞时两者都跨 exec 继承 — 先 UNBLOCK 解除阻塞, 再把 ALRM
# 置为 caught (POSIX: caught 信号经 exec 重置为 SIG_DFL, ignore 才保持)
# → exec 后 ALRM 必为可杀的默认处置。
owner_token() {
    local ls
    ls=$(LC_ALL=C TZ=UTC /usr/bin/perl -e '
        use POSIX ();
        POSIX::sigprocmask(POSIX::SIG_UNBLOCK, POSIX::SigSet->new(POSIX::SIGALRM));
        $SIG{ALRM} = sub {};
        alarm 5;
        exec "/bin/ps", "-o", "lstart=", "-p", $ARGV[0] or exit 1;
    ' "$1" 2>/dev/null) || return 1
    [ -n "$ls" ] || return 1
    printf '%s %s' "$1" "$ls"
}

# 自身 token 先行推导, 失败整体不跑 (fail-closed, 与 KEY 推导同门):
# token 都算不出的环境写出的锁只会污染后续判定
MY_TOKEN=$(owner_token $$) || {
    echo "PREFLIGHT-FAIL: owner token derivation failed (/bin/ps)" >&2
    exit 78
}

acquire_lock() {
    mkdir "$LOCK" 2>/dev/null || return 1
    if ! printf '%s' "$MY_TOKEN" > "$LOCK/pid" 2>/dev/null; then
        # token 写不进 (磁盘满等): 连半成品 pid 一起清, 不留无主锁
        rm -f "$LOCK/pid"
        rmdir "$LOCK" 2>/dev/null || true
        return 1
    fi
    return 0
}
release_lock() {
    [ "$(cat "$LOCK/pid" 2>/dev/null)" = "$MY_TOKEN" ] || return 0
    rm -f "$LOCK/pid"
    rmdir "$LOCK" 2>/dev/null || true
}

if ! acquire_lock; then
    owner=$(cat "$LOCK/pid" 2>/dev/null || true)
    owner_pid=${owner%% *}
    if [ -n "$owner_pid" ] && kill -0 "$owner_pid" 2>/dev/null; then
        # pid 活: token 匹配 = 同一进程 → 永不夺; token 当场算不出
        # (ps 瞬时失败) 也 fail-closed 当活 — 查询失败绝不构成回收理由
        cur_token=$(owner_token "$owner_pid") || cur_token=""
        if [ -z "$cur_token" ] || [ "$cur_token" = "$owner" ]; then
            echo "skip: already running (pid $owner_pid)" >&2
            exit 0
        fi
        # token 不匹配 = pid 已被无关进程复用, 按死持有者走陈旧窗口
    fi
    if [ -z "$(find "$LOCK" -maxdepth 0 -mmin +360 2>/dev/null)" ]; then
        # 死持有者但锁还年轻 (<6h, Code-Review M5 死锁门): 等陈旧窗口,
        # 防误夺刚建到一半 (token 未落) 的锁
        echo "skip: recent lock (owner ${owner_pid:-unknown} not alive), inside stale window" >&2
        exit 0
    fi
    # 陈旧死锁回收 (Codex-C1a F2 round3 定稿): 主锁永不被 mv/整体搬动 —
    # 回收者先抢唯一「回收权」(mkdir 原子), 持权下重读代际: 仍是判定时
    # 那把死锁才拆。此后无人能改该锁 (acquire 需 mkdir 必失败, 回收需
    # 抢权必失败), 拆除绝无误伤; 锁名空缺后新 acquire 者与我们的
    # acquire 公平竞争, 输家 skip。
    RECLAIM="$LOCK.reclaim"
    if ! mkdir "$RECLAIM" 2>/dev/null; then
        # 回收权被占即退让, 权柄不代清 (round4: 无 ownership 的代清会删掉
        # 后来者刚建的新柄, 重现双 runner)。权柄生命周期毫秒级, 死留属
        # 极端事故 — 每小时档位都会走到这里有声报出, memory-health 生成:❌
        # 同步示警; 人工恢复: rmdir 该 .reclaim 目录。
        echo "skip: reclaim handle held ($RECLAIM) — if it stays for hours, remove it manually" >&2
        exit 0
    fi
    now_owner=$(cat "$LOCK/pid" 2>/dev/null || true)
    if [ "$now_owner" != "$owner" ]; then
        rmdir "$RECLAIM" 2>/dev/null || true
        echo "skip: lock rebuilt by newer runner" >&2
        exit 0
    fi
    echo "stale lock (>6h, owner ${owner_pid:-unknown} not alive) reclaimed" >&2
    rm -f "$LOCK/pid"
    rmdir "$LOCK" 2>/dev/null || true
    rmdir "$RECLAIM" 2>/dev/null || true
    if ! acquire_lock; then
        echo "skip: already running" >&2
        exit 0
    fi
fi
# EXIT 常规释放; INT/TERM 释放后必须显式退出 (Codex-C1a F2: 非退出型
# 信号 trap 会放脚本继续往下跑, runner 在无锁状态启动)。不用 exec —
# exec 会替换进程使 trap 失效, 锁永不释放。
trap 'release_lock' EXIT
trap 'release_lock; trap - EXIT; exit 130' INT TERM

"$PY" "$WT/scripts/daily_review_run.py" "$@"
