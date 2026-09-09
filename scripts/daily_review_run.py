#!/usr/bin/env python3
"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。

顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
(可 --now 注入时间跑 12 场景验收矩阵)。

终审修正落点:
  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
      · osascript 走 argv (板名注入免疫) · 损坏 state 隔离重建不炸
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import errno
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, time as dtime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_tz  # noqa: E402  — 单一时区来源 (CARD-G6-9c)
import send_bark  # noqa: E402

REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
# VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
# ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
VAULT = REPO / "canvas-vault"
# CARD-C1a: state 按 vault 命名空间化 (state_path), log 单文件加 vault= 标签
# — 多 vault 并存时 last_push_accepted_date / first_gen / next_due_utc 缓存门
# 互不踩踏。测试 fixture 只需 monkeypatch BACKUPS 一处即可全隔离。
BACKUPS = REPO / "backups"

PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))

APPLESCRIPT = "on run argv\n    display notification (item 2 of argv) with title (item 1 of argv)\nend run\n"


def _now(arg: str | None) -> datetime:
    if arg:
        dt = datetime.fromisoformat(arg.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.astimezone()
    return datetime.now(timezone.utc)


#: state 文件 schema 版本。v2 (CARD-G6-7): 加性新增 board_done —— 板级
#: 「今天做完了」账 {board: "YYYY-MM-DD"}。加性升级不配迁移器: 旧文件缺该
#: 键即视同 {} (load_state 兜底), 声明版本在下一次落盘时随形态一起前进。
#: 升版行为门 (CARD-G6-7-R, 落盘面而非内存面):
#: test_g67r_v1_state_load_save_lands_as_v2_with_values_intact 等三条。
STATE_SCHEMA_VERSION = 2


def _vault_key(vault: Path | None = None) -> str:
    """当前 VAULT 的命名空间 key (规则唯一定义点在 send_bark.vault_key)。

    CARD-G6-7 加性可选参数: Web 侧 (review_overview 的完成反馈端点) 要为
    **任意一个库**算 state 路径, 它与 runner 不同进程, 没有 VAULT 全局可设。
    给参数而不是让调用方临时改模块全局 —— 后端同步端点跑在线程池里, 改全局
    是竞态 (A 库的请求改了它, B 库的请求读到)。缺省仍取全局, runner 零变化。
    """
    return send_bark.vault_key((vault or VAULT).resolve().name)


def state_path(vault: Path | None = None) -> Path:
    """per-vault state 文件 (CARD-C1a)。旧全局 daily-review.state.json 由
    migrate_daily_review_state.py 一次性迁入, 此处不做隐式回退 — 隐式读旧
    文件会让双 vault 各自以为「今天推过了」, 恰是本卡要消灭的踩踏。"""
    return BACKUPS / f"daily-review.{_vault_key(vault)}.state.json"


def load_state(vault: Path | None = None) -> dict:
    """读回 state（缺文件给默认账，损坏则隔离留档后重建）。

    ⚠ Codex round-2 H1: 读取 / 损坏判断 / 隔离改名必须在**同一把锁**内。
    分开的话会拿过期的判断去移走文件: runner 读到坏 JSON、还没来得及隔离,
    这时 Web 取到锁、把那个坏文件隔离掉、写进完成账并返回 200; runner 随后
    按它那份早已过期的「坏」判断执行 os.replace, 把**此刻已经有效、含那笔
    账**的文件移进 .corrupt-*, 再整写一份空账 —— 一次成功的点击就没了。
    锁可重入, Web 侧在自己的 with 里调到这里时复用同一把, 不重复 open。
    """
    with state_locked(vault):
        return _load_state_locked(vault)


def _fresh_state() -> dict:
    return {"schema_version": STATE_SCHEMA_VERSION, "board_last_recommended": {}, "board_done": {}}


def _parse_state_file(state: Path) -> dict | None:
    """读并校验 state; 读不出 / 语法坏 / 结构错型一律 None (不写盘、不隔离)。

    Codex-D2b M1: 合法 JSON 但结构错型 (顶层非 dict / 账本非 dict) 与语法损坏
    同等对待 —— 不让 setdefault/.values() 半路炸。
    CARD-G6-7: board_done 与 board_last_recommended 同等对待。少这一条的话,
    一个 "board_done": [] 会让写侧的 dict 下标炸成 500, 而不是像本文件其余
    部分那样诚实地隔离重建。
    """
    try:
        st = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    if not isinstance(st, dict) or not isinstance(st.get("board_last_recommended", {}), dict):
        return None
    if not isinstance(st.get("board_done", {}), dict):
        return None
    return st


def _normalize_state(st: dict) -> dict:
    """补齐 v2 形态并把声明版本单调推到当前值 (就地改, 返回同一个 dict)。

    这不是迁移器: 没有独立的迁移入口, 也不改任何既有键的值。
    """
    st.setdefault("board_last_recommended", {})
    st.setdefault("board_done", {})
    declared = st.get("schema_version")
    if not isinstance(declared, int) or declared < STATE_SCHEMA_VERSION:
        st["schema_version"] = STATE_SCHEMA_VERSION
    return st


def _load_state_locked(vault: Path | None = None) -> dict:
    state = state_path(vault)
    if not state.exists():
        fresh = _fresh_state()
        # ⚠ Codex round-1 H2: base 记这份**默认值本身**而不是 None。文件当时不
        # 存在, 我手上这几个键全是构造出来的默认值 —— 不是我改的。窗口内别人
        # 新建了文件并写进真账时, 那些账必须以磁盘为准; 记 None 会让 save_state
        # 走整写分支, 把别人刚建的账连读都不读就抹掉。
        _remember_base(state, fresh)
        return fresh

    st = _parse_state_file(state)
    if st is None:
        # ⚠ Codex round-2 H1 的残余: 隔离之前**再读一次**。整段已经在锁里, 走锁
        # 的写者插不进来; 但不经锁的写者 (手工编辑、别的工具、还没接入这把锁的
        # 未来调用点) 仍可能在"判断"与"改名"之间把文件换成好的 —— 那时按旧判断
        # os.replace 就把一份**有效**的 state 移进 .corrupt-*, 随后整写空账,
        # 里面的完成账一起没了。重读一次是纯收益: 好了就用, 没好就照常隔离。
        st = _parse_state_file(state)

    if st is not None:
        _normalize_state(st)
        # ⚠ Codex round-1 H1: 快照取在**归一化之后**。初版取在之前, 于是
        # setdefault 补出来的空 board_done 算成"本进程改过", 一个 v1 文件下
        # runner 的空账就有权覆盖窗口内 Web 刚写成功的完成记录 —— 加性升版
        # 反倒删掉了一次用户操作。补出来的默认值不是"我的修改"。
        # (schema_version 因此也成了"我没改过", 由合并末尾的单调取大兜住。)
        _remember_base(state, st)
        return st

    quarantine = state.with_name(state.name + ".corrupt-" + datetime.now().strftime("%Y%m%dT%H%M%S"))
    try:
        os.replace(state, quarantine)
    except OSError:
        pass
    print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
    fresh = _fresh_state()
    _remember_base(state, fresh)  # 同缺文件分支 (round-1 H2): 重建出来的默认值不是"我改的"
    return fresh


#: state 的跨进程写锁 (CARD-G6-7-R)。**文件**锁, 与 push.sh 的 mkdir **目录**
#: 锁 `.daily-review.<key>.lock` 既不同名也不同形 —— 那把锁覆盖 runner 整轮,
#: 但浏览器点「这板做完了」的那个进程根本不经过 push.sh, 拿不到它。
#:
#: ⛔ POSIX 记录锁按「进程 × 文件」释放: 持锁期间对同一路径**再 open 一次
#: 再 close**, 整把锁会被一起丢掉, 而本进程完全察觉不到。所以锁 fd 专用,
#: 由下面的登记表持有; 重入只加计数, 不重复 open。
_STATE_LOCK_GUARD = threading.Lock()
#: resolve 后的锁路径 → per-path 可重入线程锁 (同线程嵌套不阻塞, 跨线程串行)
_STATE_LOCK_TLOCKS: dict[str, threading.RLock] = {}
#: resolve 后的锁路径 → [fd, depth]。depth 归零才 LOCK_UN + close。
_STATE_LOCK_FDS: dict[str, list] = {}
#: 本线程当前持有哪些锁 (键同上, 值 = 重入深度)。
#: ⚠ 必须按**线程**记而不是只看 _STATE_LOCK_FDS 有没有那个键: 另一个线程
#: 持锁时登记表里同样有键, 只查表会让本线程误以为"我已经持锁了"而无锁直写。
_STATE_LOCK_LOCAL = threading.local()

#: state 的「读到手时磁盘长什么样」快照 —— 三方合并的 base。
#: 值 = **归一化之后**的 dict (Codex round-1 H1: setdefault 补出来的默认值不是
#: 本进程的修改), 文件当时不存在或损坏隔离时则是那份默认账本身 (round-1 H2)。
#: 深拷贝存: 浅拷贝与调用方共享嵌套 dict, mine 一改 base 跟着变,
#: 「我到底改没改过这个键」就永远答 False。
#: ⚠ 键是 **state 路径**, 不是"哪个 dict 对象" (Codex round-2 L2)。所以它记的
#: 是「这条路径上一次被本进程读成什么样」, 而不是「这个 st 从哪来」—— 同一路径
#: 读过之后再传进来一份**另外构造**的 dict, 也会走合并而不是整写。生产上够用
#: (Web 侧同库 load→save 全程在锁内串行, runner 在另一个进程), 但契约就这么窄,
#: 别按"绑定到返回对象"去理解。
_STATE_BASE_SNAPSHOTS: dict[str, dict | None] = {}
_NO_SNAPSHOT = object()


def state_lock_path(vault: Path | None = None) -> Path:
    """per-vault state 的写锁文件 (与 state_path 同目录同命名规则)。"""
    return BACKUPS / f"daily-review.{_vault_key(vault)}.state.lock"


def _state_lock_key(vault: Path | None = None) -> str:
    """登记表的键 —— **resolve 之后**的路径。

    同一个文件的两种写法 (软链 / 相对路径) 不 resolve 就会各拿一把锁,
    于是"锁住了"只是因为两边在动不同的键。
    """
    return str(state_lock_path(vault).resolve())


def _held_locks() -> dict:
    d = getattr(_STATE_LOCK_LOCAL, "keys", None)
    if d is None:
        d = {}
        _STATE_LOCK_LOCAL.keys = d
    return d


def _state_lock_held(vault: Path | None = None) -> bool:
    """本线程此刻是否已经持有这个 vault 的 state 锁。"""
    return _held_locks().get(_state_lock_key(vault), 0) > 0


@contextlib.contextmanager
def state_locked(vault: Path | None = None):
    """持有该 vault 的 state 跨进程写锁; 可重入。

    读改写要整段在锁内才有意义 —— 只锁"写"那一下, load 与 save 之间照样
    是别人的窗口。Web 侧的完成账写点就是这么用的:
        with runner.state_locked(vault):
            st = runner.load_state(vault); ...; runner.save_state(st, vault)
    内层的 save_state 会检测到本线程已持锁而**复用**它 (不 open 也不 close),
    见 save_state 的第一段。
    """
    key = _state_lock_key(vault)
    with _STATE_LOCK_GUARD:
        tlock = _STATE_LOCK_TLOCKS.setdefault(key, threading.RLock())
    tlock.acquire()
    held = _held_locks()
    try:
        if held.get(key):
            held[key] += 1
            with _STATE_LOCK_GUARD:
                _STATE_LOCK_FDS[key][1] += 1
        else:
            lock = state_lock_path(vault)
            lock.parent.mkdir(parents=True, exist_ok=True)
            # ⚠ Codex round-1 H3: O_NOFOLLOW 与 save_state 的 tmp 同款理由。
            # 不加的话, 事先把 <state>.lock 摆成一条软链就能同时做到两件事:
            # ① 指向 state.json 本身 ⇒ 锁 fd 与 state 同 inode, load_state 的
            #    读盘 close 会把整个进程在该 inode 上的记录锁一起释放 (POSIX
            #    记录锁按进程×文件), 而登记表还以为锁在;
            # ② 指向库内一个尚不存在的节点路径 ⇒ O_CREAT 会在库里创建文件,
            #    破掉"完成账不写 vault"这条写面承诺。
            fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o644)
            try:
                # ⚠ Codex round-2 H2: O_NOFOLLOW 只拒**符号**链接, 对硬链接无效。
                # 事先把 <state>.lock 做成 <state>.json 的硬链接, 两者就是同一个
                # inode: 取锁成功之后 load_state 的一次读盘 close 会释放本进程在
                # 该 inode 上的全部记录锁 (POSIX 记录锁按进程 × 文件), 而登记表
                # 还报告持锁 —— 互斥凭空消失且无人察觉。
                # nlink != 1 一律拒: 锁文件由本模块自建自用, 正常永远只有一条
                # 链接; 多出来的那条无论指向什么都不该信。
                info = os.fstat(fd)
                if info.st_nlink != 1:
                    raise OSError(
                        errno.EMLINK,
                        f"锁文件有 {info.st_nlink} 条硬链接 —— 可能与 state 或库内文件共用 inode",
                        str(lock),
                    )
                # ⚠ Codex round-3 H1: 直接比 inode —— 前面几层都是**形态**判断
                # (O_NOFOLLOW 拒锁路径是软链、nlink 拒硬链接), 而危险的是**结果**:
                # 锁与 state 落到同一个 inode。反方向的软链 (state.json → state.lock)
                # 让锁路径本身是普通文件、nlink 也是 1, 三层形态判断全过, 但
                # load_state 的读盘跟随 state 的软链打开并关闭锁 inode, 本进程在
                # 该文件上的记录锁**整个**被释放, 而登记表还报告持锁。
                # 比 inode 是本质判据, 上面两条是它的早期、可给出更准确报文的补充。
                try:
                    st_state = os.stat(state_path(vault))  # 跟随软链: 要的就是最终落点
                except OSError:
                    st_state = None
                if st_state is not None and (st_state.st_dev, st_state.st_ino) == (info.st_dev, info.st_ino):
                    raise OSError(
                        errno.EMLINK,
                        "锁与 state 落在同一个 inode —— 读 state 的一次 close 会把锁一起释放",
                        str(lock),
                    )
                fcntl.lockf(fd, fcntl.LOCK_EX)
            except BaseException:
                os.close(fd)
                raise
            with _STATE_LOCK_GUARD:
                _STATE_LOCK_FDS[key] = [fd, 1]
            held[key] = 1
        yield
    finally:
        # ⛔ 递减必须在 finally: 异常路径不减的话, 这个键在本线程里永远"已持锁",
        # 之后每一次 save_state 都会走无锁的复用分支。
        release_fd = None
        if held.get(key):
            held[key] -= 1
            if held[key] <= 0:
                del held[key]
                with _STATE_LOCK_GUARD:
                    entry = _STATE_LOCK_FDS.pop(key, None)
                if entry is not None:
                    release_fd = entry[0]
            else:
                with _STATE_LOCK_GUARD:
                    if key in _STATE_LOCK_FDS:
                        _STATE_LOCK_FDS[key][1] -= 1
        if release_fd is not None:
            try:
                fcntl.lockf(release_fd, fcntl.LOCK_UN)
            finally:
                os.close(release_fd)
        tlock.release()


def _base_key(state: Path) -> str:
    """base 快照的键 = **逻辑路径**, 刻意不 resolve。

    ⚠ Codex round-3 H2: 用 resolve 的话, state 是软链时键落在链的目标 T 上;
    而 save_state 的 os.replace 会把软链**换成一个普通文件** S —— 同一轮里
    第二次保存按 S 查就查不到 base 了, 于是走整写分支, 把这中间别人守规矩
    写进去的完成账整个覆盖掉 (所有写者都正确取了锁, 照样丢)。
    state_path() 对同一个 vault 恒定, 逻辑路径因此是稳定的键;
    「同一文件的两条不同写法」这件事归**锁**的登记表管 (那边必须 resolve),
    快照记的本来就是"我这条路径上次读到什么"。
    """
    return str(state)


def _remember_base(state: Path, raw: dict | None) -> None:
    _STATE_BASE_SNAPSHOTS[_base_key(state)] = copy.deepcopy(raw) if raw is not None else None


def _merge_state_with_disk(mine: dict, state: Path) -> dict:
    """锁内三方合并: **我没改过的键, 不许被我覆盖**。

    窄窗有两个方向 —— runner 的 load(main) → 扫描(秒级) → save 之间, 浏览器
    可能把 board_done 落了盘; 反过来 Web 的 load → save 之间, runner 的 :05
    档可能把推送账落了盘。谁整写谁就把对方那次写静默抹掉 (last-writer-wins)。

    三方 = base (我读到手时的磁盘) / mine (我手上这份) / theirs (此刻的磁盘):
      · mine[k] 与 base[k] 不同 (含**删掉了这个键**) ⇒ 这个键我动过, 写 mine;
        ⚠ load_state 的归一化 (schema_version 升版、board_done setdefault)
        **不算**"我动过" —— base 就记在归一化之后 (round-1 H1)。初版把它算
        进来, 于是 v1 文件下补出的空账有权压过磁盘, 加性升版反倒删掉一次
        用户操作。schema_version 因此另走单调取大, 见本函数末尾。
      · 相同 ⇒ 我没动过, 以磁盘为准 (别人可能刚改过);
      · theirs 里没有而 mine 里有 ⇒ 写 mine (不替别人接受"删除")。
    base 缺席 (这条路径本进程从没 load 过) 或 theirs 读不出 (缺文件 / 损坏)
    ⇒ **不合并, 整写 mine** = 本卡之前的行为, 既有的「改了就写」语义逐字节
    不变。⚠ 「文件当时不存在」**不再**走这条 (round-1 H2): 那时 base 记的是
    默认账本身, 窗口内别人新建并写进去的账因此保得住。

    合并**不写死键归属** —— 运行期确实是 board_done 归 Web、其余归 runner,
    但那是当下的分工不是不变量; 靶子始终是"我没改的键"。

    ⚠ 键序按 mine 优先、theirs 补尾: 用 set 遍历会让落盘 JSON 的键序随机,
    「二次 load→save 字节幂等」那道门就会随机红。
    """
    base = _STATE_BASE_SNAPSHOTS.get(_base_key(state), _NO_SNAPSHOT)
    if base is _NO_SNAPSHOT or base is None:
        return mine
    try:
        theirs = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return mine
    if not isinstance(theirs, dict):
        return mine
    merged: dict = {}
    for k in list(mine) + [k for k in theirs if k not in mine]:
        in_mine, in_base = k in mine, k in base
        mine_changed = (in_mine != in_base) or (in_mine and mine[k] != base[k])
        if mine_changed:
            if in_mine:
                merged[k] = mine[k]
            continue  # 我把它删了 ⇒ 合并结果里也不该有
        if k in theirs:
            merged[k] = theirs[k]
        elif in_mine:
            merged[k] = mine[k]
    # schema_version 单调不回退 (与 load_state 同一条规则)。它是**形态声明**不是
    # 业务数据, "谁动过谁说了算"对它不适用: base 记的是归一化之后的值 (H1 修法),
    # 于是升版本身成了"我没改过", 不特判就会被磁盘上更旧的声明拉回去。取两侧较大者。
    versions = [v for v in (mine.get("schema_version"), theirs.get("schema_version")) if isinstance(v, int)]
    if versions:
        merged["schema_version"] = max(versions)
    return merged


def _state_tmp_path(state: Path) -> Path:
    """state 的临时件路径 (唯一名, 与 daily_review_pick.atomic_write 同形)。

    单独抽成一个名字, 是为了让门能把它钉死: 「名字猜不中」与「路径被占也写不进去」
    是**两层**防御, 要验后一层就得先让前一层失效。测试补丁打在本函数上 (模块级、
    可替换), 而不是去改 os.getpid / uuid.uuid4 —— 那两个是解释器全局, 打上去会
    连累同进程里任何别的调用方 (实测: 会把 bug_tracker 的 BUG-id 生成一起弄坏)。
    """
    return state.with_name(f"{state.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")


def save_state(st: dict, vault: Path | None = None):
    """同目录 tmp → os.replace 原子发布。

    ⚠ CARD-G6-7 (Codex round-1 HIGH): 原实现是
    `tmp = state.with_suffix(".tmp"); tmp.write_text(...)` —— **固定名 + 跟随
    符号链接**。于是事先在那个可预测的路径上摆一条指向库内节点的软链, 这次
    保存就把 state JSON 写进那个节点, 把它的 fsrs_* frontmatter 整个覆盖掉
    (os.replace 那一步不跟随软链, 所以问题一直在 tmp 写这一侧, 不在 state 侧)。

    这条缺陷的**同款修法在姊妹函数上早就有了** —— `daily_review_pick.atomic_write`
    (CARD-G6-1 round-3) 就是唯一名 + O_EXCL|O_NOFOLLOW; 本函数当时漏了。
    从前它只有本机 runner 每小时走一次, 于是没人注意; CARD-G6-7 起浏览器点一下
    就能走到这里 —— **可达性变了, 原来只在纸面上的前提必须变成代码里的判据**。

    两处刻意与 atomic_write 同形而不是 import 它: 两个脚本在模块级互不依赖
    (runner 只在 ensure_payload 里惰性 import picker), 为一个 8 行原语建立
    模块级耦合不划算。同形处如实登记, 改一处要记得改另一处。

    ⚠ CARD-G6-7-R: 落盘现在整段在 state_locked 内, 且先与磁盘做一次三方
    合并 (见 _merge_state_with_disk)。未持锁时**先取锁再自调一次**, 而不是
    把下面整段包进一个 with —— 上面那两行 (O_EXCL|O_NOFOLLOW 的 os.open 与
    os.replace) 是 Y2-B Codex round-1 HIGH 的修复面, 卡文把它们钉成"逐字节
    不动", 换个缩进就是动了。递归至多一层: state_locked 成功即登记, 登记后
    _state_lock_held 恒真。
    """
    if not _state_lock_held(vault):
        with state_locked(vault):
            return save_state(st, vault)
    # 本线程已持锁 ⇒ 复用那把锁: 读盘 / 合并 / replace 直接跑, 对锁文件
    # 既不 open 也不 close (POSIX 记录锁按进程×文件释放, 内层一次 close
    # 会把外层的锁一起丢掉)。
    state = state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    st = _merge_state_with_disk(st, state)
    tmp = _state_tmp_path(state)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(st, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, state)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def log_line(msg: str):
    log = BACKUPS / "daily-review.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%F %T")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] vault={_vault_key()} {msg}\n")


def _nodes_max_mtime(vault: Path) -> float:
    """节点池最新改动时间 (CARD-A3 缓存失效判据)。

    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
    增删改名 (不留文件 mtime); 误报代价只是一次幂等重扫。保 mtime 的
    还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内。
    """
    pool = vault / "节点"
    latest = 0.0
    for p in pool.glob("*.md"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue  # 迭代间隙被删: 殿后的目录 stat 捕获该变动
    try:
        # 目录 stat 殿后取样 — 迭代期间发生的删除也已反映在目录 mtime 里
        latest = max(latest, pool.stat().st_mtime)
    except OSError:
        return 0.0  # 节点池不存在: 不因 mtime 失效, 保持旧缓存语义
    return latest


def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。

    CARD-A3 (BATCH-2026-08-24-复习闭环): 复用多两道门 — ①节点池比 payload
    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫; ②当前时间越过
    生成时记录的最早未来到期点 (next_due_utc) 也重扫 (Codex-A3 BLOCKER:
    09:59 落 fsrs_due=10:09 → 10:05 重扫时未到期 → 11:05 若只看 mtime 会
    整天 cached, 当天到期卡丢失 — 卡片 :89 警告的缺陷位移)。push 去重
    不在此处: last_push_accepted_date + last_push_kind 门保证同日至多
    rest→due 两推 (CARD-D2b; state 持久化成立前提, 见推送门注释)。
    """
    payload_path = VAULT / "outputs" / "今日复习.json"
    # CARD-G6-7 (Codex round-1 MEDIUM): 完成账变了也算缓存失效。少这一条 ——
    # 当天投影已生成之后再标完成、节点没动、也没跨到期点 —— 缓存分支直接返回
    # 旧榜, 「让出榜首」整天不生效 (真文件实测: how="cached", 榜首与通知不变)。
    # 签名用 sort_keys 的 JSON 而不是 dict 本身: 只认内容变化, 不认键序抖动。
    #
    # ⚠ 签名**缺席**不等于变化: 本卡之前落盘的 state 都没有这个键, 一律当"变了"
    # 会把「当天已缓存的 legacy payload 照常复用」这条既有契约打掉
    # (test_legacy_cached_payload_without_top_boards_records_due 当场变红)。
    # 只有"没签名**且**账非空"才是真的没对过账 —— 那正是升级当天先标了完成、
    # 又还没重新生成过的那一格, 必须重扫。
    done_sig = json.dumps(st.get("board_done") or {}, ensure_ascii=False, sort_keys=True)
    cached_sig = st.get("board_done_sig")
    done_unchanged = cached_sig == done_sig or (cached_sig is None and not st.get("board_done"))
    first_gen_today = st.get("last_generate_date") != today
    if not first_gen_today and payload_path.exists() and done_unchanged:
        try:
            raw = payload_path.read_text(encoding="utf-8")
            # sha 校验 (Code-Review L3): 外部改动/半写的 payload 不复用, 重新生成
            if hashlib.sha256(raw.encode("utf-8")).hexdigest() == st.get("payload_sha256"):
                now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                due_crossed = bool(st.get("next_due_utc")) and st["next_due_utc"] <= now_z
                if not due_crossed and _nodes_max_mtime(VAULT) <= payload_path.stat().st_mtime:
                    return json.loads(raw), "cached"
        except (json.JSONDecodeError, OSError):
            pass  # 落盘 payload 损坏 → 重新生成

    import daily_review_pick as picker

    scan_started = time.time()
    # CARD-G6-7 加性: board_done 只影响「今天谁占榜首」, 不改分不改排序律
    # (见 daily_review_pick.build_payload 的 board_done 分区块)。缺键的旧
    # state 传 None = 与本卡之前逐字节同行为。
    payload, ranked = picker.build_payload(
        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT), board_done=st.get("board_done")
    )
    out = VAULT / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    picker.atomic_write(payload_path, raw)
    # mtime 门基准回拨到扫描起点: 扫描-落盘窗口内落地的写侧更新, 其 mtime
    # 必然 > 基准, 下一轮触发重扫捞回 (否则该更新当天静默丢失, 无日志可查)
    os.utime(payload_path, (scan_started, scan_started))

    st["last_generate_date"] = today
    st["board_done_sig"] = done_sig  # CARD-G6-7: 与上面的缓存门同源
    st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    # 最早未来到期点: ranked 是全量榜 (payload.top_boards 才截断), 每行
    # next_due 已是板内未来最小值; upcoming 按 next_due 升序, [0] 即全局
    # 最小, [:3] 截断不丢它。未归板节点不参与推荐, 其到期转场不改变输出。
    nexts = [r["next_due"] for r in ranked if r.get("next_due")]
    if payload.get("upcoming"):
        nexts.append(payload["upcoming"][0]["next_due"])
    st["next_due_utc"] = min(nexts, default="")
    credited_today = (
        st.get("last_recommend_credit_date") == today
        # Codex-D2a H1: 升级当天旧 state 自然缺 marker, 但旧门若已落账其值
        # 必是 today — 只认 marker 会给第二个板补账, 突破每日一次上界
        or today in st["board_last_recommended"].values()
    )
    if ranked and not credited_today:
        # CARD-A3/D2a: 每天只给第一个「非空」榜首落账一次 — 重扫换榜也补写
        # 会把第二个板标成「今天推荐过」, 污染 tie-break 天级轮转; 但门不能
        # 绑 first_gen_today: 空首扫日 (休息日/纯空) 会把当天唯一一次落账
        # 机会白白烧掉, board_last_recommended 永远空置
        st["board_last_recommended"][ranked[0]["board"]] = today
        st["last_recommend_credit_date"] = today
    save_state(st)
    return payload, "new"


def osascript_fallback(noti: dict) -> bool:
    try:
        r = subprocess.run(
            ["/usr/bin/osascript", "-", noti["title"], noti["body"]],
            input=APPLESCRIPT,
            text=True,
            capture_output=True,
            timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main() -> int:
    global VAULT
    # allow_abbrev=False: push.sh 锁解析只认全称 --vault, argparse 缩写
    # (--v) 会让锁与 runner 指向不同 vault (Codex-C1a F1) — 两侧必须同源
    ap = argparse.ArgumentParser(description="每日复习推送编排", allow_abbrev=False)
    ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
    ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
    args = ap.parse_args()

    if args.vault:
        VAULT = Path(args.vault)

    now = _now(args.now)
    # CARD-G6-9c / D-18: 归日走单一来源。只要机器本地时 astimezone(机器本地
    # tzinfo) ≡ astimezone(), 行为逐字节不变; 但本卡引入的 CANVAS_TZ 覆盖若
    # 不在这里读, 它自己就成了第三套时钟 (显示侧/pick 读它而 runner 不读)。
    local = now.astimezone(local_tz.display_tz())
    today = local.date().isoformat()
    st = load_state()

    try:
        payload, gen = ensure_payload(st, now, today)
    except Exception as e:  # 生成失败 = 无保底, 唯一的非 0 退出
        log_line(f"generate:FAILED err={type(e).__name__}:{str(e)[:120]}")
        print(f"[runner] 生成失败: {e}", file=sys.stderr)
        return 1

    noti = (payload or {}).get("notification")
    push, fallback = "-", "-"
    if not noti:
        push = "skip-empty"  # 无板可推 (全占位/空 vault): md 已如实落盘
    elif st.get("last_push_accepted_date") == today and not (
        st.get("last_push_kind") == "rest" and payload.get("top_boards")
    ):
        # CARD-D2b 方案甲: 当日已推但语义从 rest 反转为 due (休息推送后盘中
        # 转出到期) 时放行一次二推 — 同 id 服务端覆盖 (A4 契约, 通知中心
        # 不堆叠), due 落账后恒 skip-done → state 持久化成立时每日至多
        # 2 次 accepted (accepted 后崩溃窗/损坏重建的 at-least-once 残余
        # 与 A4/A7 既有语义同级, Codex-D2b H1/H2 如实入档)。旧 state 缺
        # last_push_kind → 条件恒真 → 保守一日一推 (向后兼容)
        push = "skip-done"
    elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
        push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
    else:
        # vault_id 取 payload 顶层 (C1a 加性字段); 当日缓存若是迁移前生成的
        # 旧 payload (无该字段), 回退当前 vault 目录名 — 两者必然同库
        rc = send_bark.send(noti, payload.get("vault_id") or VAULT.resolve().name)
        if rc == 0:
            st["last_push_accepted_date"] = today
            # CARD-D2b: 语义账只在 accepted 时落 — 失败保持原 kind, 反转门
            # 敞开, 次小时 launchd 触发自然幂等重试。缺 top_boards 键的
            # legacy 缓存 payload 语义未知 → 保守记 due (关反转门, Codex M2)
            st["last_push_kind"] = "due" if payload.get("top_boards", True) else "rest"
            st["last_result"], st["last_error"] = "pushed", ""
            save_state(st)
            push = "accepted"
        else:
            push = "skip-nokey" if rc == 2 else "failed"
            if rc != 2:
                st["last_result"] = "generated_push_failed"
                st["last_error"] = "bark-send"
            # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
            # (Code-Review H1: key 配好前不能一切静默)
            if st.get("last_local_notify_date") != today:
                local_noti = (
                    noti
                    if rc != 2
                    else {
                        "title": "📚 今日复习已生成",
                        "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
                    }
                )
                fallback = "ok" if osascript_fallback(local_noti) else "fail"
                if fallback == "ok":
                    st["last_local_notify_date"] = today
            save_state(st)

    log_line(f"generate:{gen} push:{push} fallback:{fallback}")
    print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
