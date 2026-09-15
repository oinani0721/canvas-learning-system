#!/usr/bin/env python3
"""CARD-G6-10 — 双 vault **交互面**隔离 canary（A 库的 snooze/done 对 B 库零影响）。

> 批次: BATCH-2026-09-11-第十四批 / CARD-G6-10
> 姊妹件: ``backend/tests/integration/test_g610_dual_vault_isolation.py``（Neo4j 真库维）

G2-9 的 canary（``g29_dual_vault_canary.py``）证的是**数据面**：两个 vault 各写各的，
三存储互不可见。本脚本证的是它证不到的另一半——**交互面**：用户在 A 库点了「今天先
不做」和「做完了」之后，B 库的复习进度**一个字节都不动**。

两者的区别不是措辞。数据面隔离靠 group_id / 表名前缀；交互面的 snooze/done 账根本
不落 Neo4j 也不落 LanceDB，它落在 ``backups/daily-review.<vault_key>.state.json``
这**一个文件**上。那个文件的隔离只由一条规则保证::

    state_path(vault) = BACKUPS / f"daily-review.{_vault_key(vault)}.state.json"
    _vault_key(vault) = send_bark.vault_key(vault.resolve().name)

⇒ 两库的 state 文件是否互不干扰，**完全取决于 ``vault_key`` 会不会把它们算成同一个
key**。本脚本就是把这条单点机制放到真实写路径下跑一遍。

为什么不走 HTTP 端点
--------------------
生产的 snooze/done 写点是 ``review_overview`` 的四个写辅助函数，POST 路由只是它们的
壳（``review_overview_board_done:2999`` → ``:3040`` 调 ``_write_board_done``）。本卡
**直接 import 那两个辅助函数**：拿到的是与生产逐字节相同的读改写 + 同一把跨进程锁，
而不需要起 FastAPI、不需要鉴权、不需要端口。代价如实声明：端点层自己的鉴权与并发
不在本 canary 的覆盖面内（验收单「本卡未证明什么」①）。

两态（先红后绿的那一对）
------------------------
``--isolated``（默认，正例）  A/B 两个 vault 目录名不同 ⇒ 两个 vault_key ⇒ 两个 state 文件。
``--share-state``（负控）    **只把 B 的目录名改成与 A 相同**，其余一切不变。

负控的选型是本脚本最要紧的一处设计，理由写在这里以免后人改坏：

  ✗ monkeypatch ``_vault_key`` 让它返回常量 —— 那是把被测机制本身拆了再宣布它会红，
    等于「先把检查关掉，再证明检查关掉之后不报警」；
  ✗ 两次都传同一个 vault Path —— 那不是两个库，是同一个库调了两次；
  ✓ **两个 vault 目录同 basename、不同父目录** —— 碰撞是生产 ``vault_key`` 自己算出来
    的，一行生产代码都不改。

且 ``--share-state`` 与 ``--isolated`` 之间**只差 B 的目录名一个变量**：A 的路径、两库
的资产、对 A 做的操作、断言本身、执行断言的那个函数，全部逐字相同。所以「负控红了」
只能归因于那一个变量，不能归因于「你换了套写法」。

这条碰撞不是假设性场景：``vault_key`` 只取 basename（``send_bark.py:61``
``raw = str(vault_id).rstrip("/").rsplit("/", 1)[-1]``），所以现实里
``~/courses/CS61B/vault`` 与 ``~/archive/CS61B/vault`` 就会共用同一个 state 文件。

同名攻击用例集（总账 :983）
---------------------------
两库用的资产标识**不是本文件新发明的**，而是从 G2-9 的 canary ``import`` 过来的同一
组常量（同 canvas 路径 / 同 node ID / 同 concept / 同 user）。用 import 而不是抄一份，
是因为两份手抄清单必然漂移——G2-9 改了名字，本脚本会跟着改，不会静默失配。
退出码常量（``EXIT_OK`` / ``EXIT_ISOLATION_FAILED`` / ``EXIT_PRECONDITION_REJECTED``）
同样直接复用 G2-9 的定义，两个 canary 的 rc 口径因此恒等。

判据分三层，层与层之间**不许互相顶替**
--------------------------------------
1. 前置（不成立即 rc=2，一个字节都不写）：落盘面全在 tmp 下；补丁在生产调用路径上
   确实生效；本态该有的 state 路径关系（isolated 必不等 / share 必相等）确实成立。
2. 正向对照（不成立即 rc=2）：A 的 state 文件**变了**、变的内容**正是这次写的**、
   生产函数自报的落盘路径**就是 A 的那个文件**。没有这一层，「B 没变」可以是因为
   「两库都没写」——那是假绿，不是隔离。
3. 隔离判据（不成立即 rc=1）：B 的 state 文件 sha256 **逐字节**不变，且 B 的 vault
   目录树内容指纹不变。

⛔ 本脚本**不预期任何一态会红**。它只如实报告隔离是否成立；「isolated 必 0 /
   share-state 必非 0」是**调用方（裁判命令）**的断言，不是脚本自己的。脚本自己
   翻转结论 = 负控在自证。

用法
----
    cd backend && .venv/bin/python scripts/g610_dual_vault_interaction_canary.py --isolated
    cd backend && .venv/bin/python scripts/g610_dual_vault_interaction_canary.py --share-state

退出码（复用 G2-9 定义）
    0 = 隔离判据成立
    1 = 隔离被破坏（B 的 state 被 A 的操作改动）
    2 = 前置或正向对照被拒（含「负控根本没造出碰撞」——此时报 2 而不是 1，
        因为那说明实验没做成，不是隔离失败）
    3 = 端口门最终总账强制退出（``live_port_guard._final_accounting``）

落点：只有 ``tempfile.mkdtemp()`` 派生的临时目录。真 ``backups/`` 与 live vault
都不在写面内，且由 :func:`_assert_write_surface_is_tmp` 在任何写之前挡住。
本脚本**不连接任何数据库**（Neo4j 维在姊妹门文件里跑 7692 容器）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

# ⛔ Codex r2 MEDIUM-1: 字节码禁写必须是**进程级、从第一个 import 起**。原版只在
# runner 的 exec_module 前后开关，于是 `live_port_guard` / `g29_dual_vault_canary` /
# `app.*` 这些 import 照样往**真仓库**的 `__pycache__` 写 .pyc —— 那是 tmp 白名单
# 管不到的落盘点。本脚本是一次性 canary，全程关缓存的代价只是 import 慢一点。
sys.dont_write_bytecode = True

# ═══════════════════════════════════════════════════════════════════════════
# 装门 —— 第一段可执行代码，必须早于任何业务 import
#
# 顺序是契约不是风格（抄 g29_dual_vault_canary 的作业）: live_port_guard 只依赖
# stdlib, 装门时进程里还没有 neo4j / app.*, 所以 uvloop 毒化与 audit hook 覆盖得到
# 后续**全部**出站连接。本脚本按设计一个数据库都不连, 装门就是把这句"按设计"变成
# 可执行证据: 真连了任何一个 live 端口, _final_accounting 会以 rc=3 把跑作废。
# ═══════════════════════════════════════════════════════════════════════════

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND / "tests" / "support"))

import live_port_guard  # noqa: E402  # pyright: ignore[reportMissingImports]

#   ^ sys.path 是上面两行动态插进去的，静态分析器看不到 tests/support/

live_port_guard.install()
live_port_guard.register_final_accounting()

sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_BACKEND / "scripts"))

import g29_dual_vault_canary as g29  # noqa: E402  # pyright: ignore[reportMissingImports]

#   ^ 同名攻击用例集与退出码的**唯一定义点**。import 而不抄, 见模块 docstring。

# ═══════════════════════════════════════════════════════════════════════════
# 契约常量
# ═══════════════════════════════════════════════════════════════════════════

EXIT_OK = g29.EXIT_OK
EXIT_ISOLATION_FAILED = g29.EXIT_ISOLATION_FAILED
EXIT_PRECONDITION_REJECTED = g29.EXIT_PRECONDITION_REJECTED

#: 两库共用的同名资产（G2-9 同名攻击用例集，逐个 import）
SHARED_BOARD = g29.SHARED_CANVAS_PATH  # 同名白板 —— state 里 snooze/done 的键
SHARED_NODE_ID = g29.SHARED_NODE_ID
SHARED_CONCEPT = g29.SHARED_CONCEPT
SHARED_USER_ID = g29.SHARED_USER_ID

#: 两库的 vault 目录名。isolated 态各用各的; share-state 态**只把 B 换成 A 的那个**
#: —— 单变量负控, 见模块 docstring。名字取自 G2-9 的逻辑 group_id 末段, 与数据面
#: 用的是同一套身份, 不另起炉灶。
VAULT_DIR_A = g29.VAULT_A.split(":")[-1]  # g29canary_a
VAULT_DIR_B = g29.VAULT_B.split(":")[-1]  # g29canary_b

#: 对 A 做的那两次写。固定值而非墙钟: 同参数重跑的存档要能 diff。
SNOOZE_UNTIL_ISO = "2026-01-01T21:00:00+08:00"
DONE_DAY = "2026-01-01"
#: seed 进两库 state 的同一条「上次推荐」记录 —— 两库 seed 完必须逐字节相同,
#: 否则"A 变了 B 没变"可能只是因为两个文件本来就不一样。
SEED_DAY = "2025-12-31"


#: rc → 一词判词。存档末行写的是判词而不只是数字：读存档的人不必回头查退出码表，
#: 也不会把 REJECTED（实验没做成）误读成 BREACHED（隔离失败）。
_VERDICT = {
    EXIT_OK: "ISOLATED",
    EXIT_ISOLATION_FAILED: "BREACHED",
    EXIT_PRECONDITION_REJECTED: "REJECTED",
}


class PreconditionRejected(RuntimeError):
    """前置或正向对照不成立 —— 实验没做成，不是隔离失败（rc=2）。"""


class IsolationFailed(RuntimeError):
    """隔离判据不成立 —— A 的操作改到了 B（rc=1）。"""


# ═══════════════════════════════════════════════════════════════════════════
# 指纹工具
# ═══════════════════════════════════════════════════════════════════════════


def _sha256_file(path: pathlib.Path) -> str:
    """单文件内容 sha256。文件不存在是硬错误：本 canary 的每个取样点都必须有实体。"""
    if not path.is_file():
        raise PreconditionRejected(f"取 sha256 的目标不存在或不是文件: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_digest(root: pathlib.Path) -> str:
    """目录树的内容指纹（相对路径 + 每个文件内容 sha，排序后再 sha）。

    比"文件数没少"强的地方: 改名、改内容、删一个补一个, 三种都会让指纹变。
    用相对路径而不是绝对路径, 于是 A/B 两棵内容相同的树指纹相同 —— 这正是
    同名攻击用例集要的形状。
    """
    parts: list[str] = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_dir():
            parts.append(f"d {rel}")
        else:
            parts.append(f"f {rel} {hashlib.sha256(p.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# 运行时装配
# ═══════════════════════════════════════════════════════════════════════════


def _load_runner():
    """加载生产 runner 模块，返回 ``(模块, 受保护位置)``。**此时还不打补丁。**

    分成加载与改指向两步，是因为「受保护位置」只能从**打补丁之前**的 runner 读出来，
    而它又必须早于 :func:`tempfile.mkdtemp` 被用上（见 :func:`_assert_tempdir_anchor`）。

    ⚠ 必须与 ``review_overview._load_runner`` 装载的是**同一个模块对象**, 否则补丁
    打在 A 副本、被测代码读 B 副本 = 假绿。手段是照它的契约来: 同一份文件路径 +
    模块名 ``daily_review_run`` + **先注册 sys.modules 再 exec_module**。它在
    ``_load_runner`` 里按 ``__file__`` resolve 相等复用缓存, 于是我们这份就是它那份。
    (先注册再 exec 还有第二个理由: 模块内的自引用/dataclass 自省要拿得到自己的
    命名空间 —— Python 3.14 的 dataclass 走 sys.modules[cls.__module__]。)

    ``REPO`` / ``BACKUPS`` / ``VAULT`` 三个模块级常量在 import 时求值, 改它们是
    runner 自己 docstring 写明的隔离手段:「测试 fixture 只需 monkeypatch BACKUPS
    一处即可全隔离」(daily_review_run.py:42-44)。

    ⚠ Codex r1 MEDIUM-2: ``exec_module`` 期间必须关字节码缓存。生产 loader 这么做过
    （``review_overview._load_runner`` 有同款保护），自建 loader 漏掉就会往**真仓库**的
    ``scripts/__pycache__`` 写 ``.pyc`` —— 那是 tmp 白名单管不到的落盘点，与本脚本
    「只往 tmp 写」的承诺直接冲突。解释器级全局，窗口限于这一次加载且无条件恢复。
    """
    import importlib.util

    script = _BACKEND.parent / "scripts" / "daily_review_run.py"
    if not script.is_file():
        raise PreconditionRejected(f"找不到生产 runner: {script}")
    spec = importlib.util.spec_from_file_location("daily_review_run", script)
    if spec is None or spec.loader is None:
        raise PreconditionRejected(f"无法为 {script} 建立 import spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["daily_review_run"] = mod
    # 字节码禁写在模块顶部已置为进程级常开（Codex r2 MEDIUM-1）—— 这里**不再**保存并
    # 恢复旧值：恢复之后随后的 `import app.*` 就又开始写 .pyc 了，正是 r2 抓到的漏面。
    if not sys.dont_write_bytecode:  # pragma: no cover — 顶部已置 True，此处是回归哨兵
        raise PreconditionRejected("sys.dont_write_bytecode 被谁改回了 False —— 会往真仓库写 .pyc，拒绝开跑")
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop("daily_review_run", None)  # 半加载的壳不留在表里
        raise

    # ⛔ 先记下 runner **打补丁之前**自己算出来的落盘位置 —— 那就是「生产本来会写
    # 到哪里」。受保护位置由此派生而不是抄一份路径字面量: 抄的那份会与
    # daily_review_run.py 的默认值漂移, 而漂移之后守卫会安静地少保护一个地方。
    protected = {
        "runner.REPO(生产)": mod.REPO,
        "runner.BACKUPS(生产)": mod.BACKUPS,
        "runner.VAULT(生产 live vault)": mod.VAULT,
        "worktree(开发树)": _BACKEND.parent,
    }
    return mod, protected


#: tempfile 依次认的环境变量（``tempfile._candidate_tempdir_list`` 的前三个来源）。
_TMPDIR_ENV_VARS = ("TMPDIR", "TEMP", "TMP")


def _reject_if_protected(path: pathlib.Path, label: str, protected: dict[str, pathlib.Path], why: str) -> list[str]:
    """``path`` 与任何受保护位置互相包含即拒。返回逐条通过记录。"""
    rp = path.resolve()
    lines: list[str] = []
    for plabel, ppath in protected.items():
        pr = ppath.resolve()
        if rp == pr or pr in rp.parents or rp in pr.parents:
            raise PreconditionRejected(
                f"{label} 落在受保护位置 {plabel} 之内/之上: {label} = {rp}, {plabel} = {pr}（{why}）"
            )
        lines.append(f"anchor: {label} 与 {plabel} 互不包含 ✓")
    return lines


def _assert_tempdir_anchor(protected: dict[str, pathlib.Path]) -> list[str]:
    """在 tempfile **写出第一个字节之前**验临时目录落在哪里。

    ⛔ Codex r1 HIGH-1 + r2 HIGH 的收口，两步都是实测出来的：

    ① ``mkdtemp()`` 认 ``TMPDIR``，而它**自己就会建目录** —— 等拿到返回值再检查已经晚了。
    ② 更早一步：``tempfile.gettempdir()`` 首次调用会走 ``_get_default_tempdir()``，
       它**逐个候选目录建一个探针文件、``_os.write(fd, b'blat')``、再 unlink**
       （CPython 源码实测）。所以连 ``gettempdir()`` 都不能先调 —— 它本身就是一次写。
       目录列表看不见那个探针，是因为它在同一次调用里被删掉了，**不是因为没写**。

    所以判定只能从**环境变量原文**读起：先看 ``TMPDIR``/``TEMP``/``TMP`` 的字面值，
    全部安全了，才允许 tempfile 去碰盘；之后再把 ``gettempdir()`` 的实际结果复验一遍
    （覆盖"环境变量没设、落到平台默认或 cwd"这一支）。
    """
    lines: list[str] = []
    for var in _TMPDIR_ENV_VARS:
        raw = os.environ.get(var)
        if not raw:
            lines.append(f"anchor(pre-tempfile): ${var} 未设置")
            continue
        lines.extend(
            _reject_if_protected(
                pathlib.Path(raw),
                f"${var}",
                protected,
                "tempfile 会在那里建探针文件并写入 —— 在它碰盘之前拒绝",
            )
        )

    # 环境变量已安全 ⇒ 现在才允许 tempfile 碰盘；结果再复验一遍（平台默认 / cwd 兜底支）
    base = pathlib.Path(tempfile.gettempdir())
    lines.append(f"tempfile.gettempdir() = {base.resolve()}")
    lines.extend(_reject_if_protected(base, "gettempdir()", protected, "mkdtemp 会在那里建目录"))
    return lines


def _point_runner_at(mod, tmp_repo: pathlib.Path) -> None:
    """把 runner 的三个落盘根改到 tmp（加载与改指向分成两步，见 :func:`_load_runner`）。"""
    mod.REPO = tmp_repo
    mod.BACKUPS = tmp_repo / "backups"
    mod.VAULT = tmp_repo / "canvas-vault"


def _materialize_vault(vault_dir: pathlib.Path) -> None:
    """在库里落下同名资产（同白板路径 / 同 node ID / 同 concept / 同 user）。

    state 的键只是板名字符串, 不校验文件存在。但本 canary 的主张是「两个**长得
    一模一样**的库互不干扰」, 所以库里得真有那块同名白板 —— 否则"同名"只存在于
    一个字符串常量里, 断言的对象就不是用户会遇到的那个场景。
    """
    board = vault_dir / SHARED_BOARD
    board.parent.mkdir(parents=True, exist_ok=True)
    board.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": SHARED_NODE_ID,
                        "type": "text",
                        "text": SHARED_CONCEPT,
                        "user": SHARED_USER_ID,
                    }
                ],
                "edges": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _plan_vault_pair(tmp_root: pathlib.Path, share_state: bool) -> tuple[pathlib.Path, pathlib.Path]:
    """**只算路径，不建目录**。两态只差 B 的 basename 一个变量（见模块 docstring）。

    ⚠ Codex r1 MEDIUM-1: 算路径与落盘必须分成两步。合成一步的话，落盘面守卫拿到的
    是"已经建好、已经写过白板"的目录 —— 「任何写之前检查」就成了一句自述。现在顺序
    是: 算路径 → 守卫（含白板文件路径）→ 才动盘。
    """
    a = tmp_root / "lane_a" / VAULT_DIR_A
    b_name = VAULT_DIR_A if share_state else VAULT_DIR_B
    b = tmp_root / "lane_b" / b_name
    return a, b


# ═══════════════════════════════════════════════════════════════════════════
# 第 1 层 —— 前置（不成立即 rc=2，一个字节都不写）
# ═══════════════════════════════════════════════════════════════════════════


def _assert_write_surface_is_tmp(
    runner,
    tmp_root: pathlib.Path,
    vaults: tuple[pathlib.Path, ...],
    protected: dict[str, pathlib.Path],
) -> list[str]:
    """把「补丁应该生效了」变成「跑之前证明落盘路径确实在 tmp 下」。

    白名单而不是黑名单: 判据是「每一条落盘路径都在 tmp_root 之下」, 不是「不在真
    backups 下」。黑名单要求我把所有不该写的地方列全, 列漏一个就是假绿; 白名单只
    要求我把该写的地方列全, 列漏一个是假红（会当场炸, 不会静默放行）。

    落盘点枚举（源自实测的生产代码, 不是推断）:
      · ``state_path(v)``      = BACKUPS/daily-review.<key>.state.json   ← save_state 目标
      · ``state_lock_path(v)`` = BACKUPS/daily-review.<key>.state.lock   ← state_locked 的 O_CREAT
      · save_state 的 tmp 件    同目录 → os.replace                       ← 同在 BACKUPS 下
      · vault 目录本身          写辅助明写「不写 vault 内任何路径」         ← 仍逐库校验
      · ``v / SHARED_BOARD``   本脚本自己落的同名白板（Codex r1 MEDIUM-1）

    ⛔ **白名单的锚点自己也要被验**（Codex r1 HIGH-1）。原版只问「落盘路径在不在
    ``tmp_root`` 下」，而 ``tmp_root`` 来自 :func:`tempfile.mkdtemp`，它认 ``TMPDIR``。
    把 ``TMPDIR`` 指到真 ``backups/`` 或 live vault，mkdtemp 就在**那里面**建目录，
    于是每一条落盘路径都「在 tmp_root 下」——白名单全绿，字节却写进了现网。
    判据是自指的：锚点没被验，白名单证明不了任何事。所以先用一条黑名单验锚点
    （这是黑名单唯一正确的用法：受保护的位置是有限且已知的），再用白名单验落盘点。
    """
    checked: list[str] = []
    tmp_resolved = tmp_root.resolve()

    # ---- 锚点自证: tmp_root 本身不得落在任何受保护位置之内/之上 ----
    for label, protected_path in protected.items():
        pr = protected_path.resolve()
        if tmp_resolved == pr or pr in tmp_resolved.parents:
            raise PreconditionRejected(
                f"tmp_root 落在受保护位置 {label} 之内: tmp_root = {tmp_resolved}, {label} = {pr}"
                "（TMPDIR 被指到了不该写的地方 —— 白名单的锚点失效, 拒绝开跑）"
            )
        if tmp_resolved in pr.parents:
            raise PreconditionRejected(
                f"tmp_root 是受保护位置 {label} 的祖先: tmp_root = {tmp_resolved}, {label} = {pr} —— 拒绝开跑"
            )
        checked.append(f"anchor: tmp_root 与 {label} 互不包含 ✓")

    def _under_tmp(p: pathlib.Path, label: str) -> None:
        rp = p.resolve()
        if rp != tmp_resolved and tmp_resolved not in rp.parents:
            raise PreconditionRejected(f"落盘面逃出 tmp: {label} = {rp}（tmp_root = {tmp_resolved}）")
        checked.append(f"{label} = {rp}")

    _under_tmp(runner.REPO, "runner.REPO")
    _under_tmp(runner.BACKUPS, "runner.BACKUPS")
    for tag, v in zip(("A", "B"), vaults):
        _under_tmp(v, f"vault_{tag}")
        _under_tmp(v / SHARED_BOARD, f"board_{tag}")
        _under_tmp(runner.state_path(v), f"state_path({tag})")
        _under_tmp(runner.state_lock_path(v), f"state_lock_path({tag})")
    return checked


def _assert_patch_live_on_production_path(vaults_root: pathlib.Path, runner) -> str:
    """证明生产写路径拿到的就是我们打过补丁的那个 runner 模块对象。

    ``_write_board_*`` 内部走 ``_require_runner(vaults_root)`` 取 runner。若它解析到
    另一份文件/另一个模块对象, 我们改的 BACKUPS 就白改了 —— 而这种失配**不会报错**,
    只会安静地写到真 backups 去。所以这里主动调一次同一个入口做身份核对。
    """
    from app.api.v1.endpoints.review_overview import _require_runner

    got = _require_runner(vaults_root)
    if got is not runner:
        raise PreconditionRejected(
            "生产写路径解析到的 runner 不是被打补丁的那个模块对象 "
            f"(got.__file__={getattr(got, '__file__', '?')}, "
            f"patched.__file__={getattr(runner, '__file__', '?')}) —— 补丁未生效, 拒绝开跑"
        )
    return f"_require_runner(...) is patched runner  →  {got.__file__}"


def _assert_mode_shape(runner, va: pathlib.Path, vb: pathlib.Path, share_state: bool) -> list[str]:
    """本态该有的 state 路径关系确实成立 —— 负控「碰撞真的造出来了」的自证。

    少了这一条, ``--share-state`` 跑出非 0 也可能是因为**根本没碰撞**、红在别处。
    碰撞没造出来报 rc=2（实验没做成）而不是 rc=1（隔离失败）, 两者不许混。
    """
    key_a, key_b = runner._vault_key(va), runner._vault_key(vb)
    sp_a, sp_b = runner.state_path(va), runner.state_path(vb)
    lines = [
        f"vault_key(A) = {key_a}",
        f"vault_key(B) = {key_b}",
        f"state_path(A) = {sp_a}",
        f"state_path(B) = {sp_b}",
    ]
    if share_state:
        if sp_a != sp_b:
            raise PreconditionRejected(
                f"--share-state 未能把两库逼到同一个 state 文件（{sp_a} != {sp_b}）—— 负控没造成, 拒绝把它读成隔离失败"
            )
        lines.append("mode=share-state: state_path(A) == state_path(B) ✓（碰撞已造出）")
    else:
        if sp_a == sp_b:
            raise PreconditionRejected(f"--isolated 下两库却共用 state 文件（{sp_a}）—— 前置形态不对, 拒绝开跑")
        lines.append("mode=isolated: state_path(A) != state_path(B) ✓")
    return lines


def _group_dimension(va: pathlib.Path, vb: pathlib.Path, share_state: bool) -> list[str]:
    """Neo4j group 维的**静态只读**断言（本脚本一个库都不连）。

    group_id 的生产派生链末端与 state 键锚在同一个东西上——vault 的目录名
    (``config.Settings.vault_id`` 在无 ``.canvas-config.yaml`` 时取
    ``sanitize_vault_id(ACTIVE_VAULT)``)。所以同名碰撞在两个维度上同时发生,
    不是巧合而是同一个锚点。真库行为交给姊妹门文件在 7692 上跑。
    """
    from app.config import sanitize_vault_id
    from app.core.subject_config import build_vault_group_id
    from app.graphiti.group_id_compat import to_physical_group_id

    gid_a = to_physical_group_id(build_vault_group_id(sanitize_vault_id(va.name)))
    gid_b = to_physical_group_id(build_vault_group_id(sanitize_vault_id(vb.name)))
    lines = [f"physical group A = {gid_a}", f"physical group B = {gid_b}"]
    if share_state:
        if gid_a != gid_b:
            raise PreconditionRejected(f"--share-state 下两库 group 却不同（{gid_a} != {gid_b}）—— 与 state 维不同步")
        lines.append("mode=share-state: group A == group B ✓（同一个锚点, 同时碰撞）")
    else:
        if gid_a == gid_b:
            raise IsolationFailed(f"两库物理 group 相同（{gid_a}）—— Neo4j 维隔离不成立")
        if gid_a.startswith(gid_b + "__") or gid_b.startswith(gid_a + "__"):
            raise IsolationFailed(f"两库 group 互为前缀（{gid_a} / {gid_b}）—— R4 前缀语义下 A 的 scope 会吃到 B")
        lines.append("mode=isolated: group A != group B 且互不为前缀 ✓")
    return lines


# ═══════════════════════════════════════════════════════════════════════════
# 第 2 层 —— 正向对照（A 确有本次写入）
# ═══════════════════════════════════════════════════════════════════════════


def _assert_a_really_written(
    runner, va: pathlib.Path, sha_before: str, sha_after: str, reported: list[pathlib.Path]
) -> list[str]:
    """没有这一层，「B 没变」可以是「两库都没写」。三条缺一不可。"""
    lines: list[str] = []

    # P1 —— A 的 state 文件确实变了
    if sha_before == sha_after:
        raise PreconditionRejected(
            f"A 的 state 文件 sha 未变（{sha_before}）—— snooze/done 根本没落盘, 「B 没变」不构成隔离证据"
        )
    lines.append(f"P1 A state sha  {sha_before[:16]}… → {sha_after[:16]}…（已变）")

    # P2 —— 变的内容正是这次写的
    st = json.loads(runner.state_path(va).read_text(encoding="utf-8"))
    got_snooze = st.get("snoozed", {}).get(SHARED_BOARD)
    got_done = st.get("board_done", {}).get(SHARED_BOARD)
    if got_snooze != SNOOZE_UNTIL_ISO or got_done != DONE_DAY:
        raise PreconditionRejected(
            "A 的 state 内容不是本次写入的值 "
            f"(snoozed[{SHARED_BOARD}]={got_snooze!r} 期望 {SNOOZE_UNTIL_ISO!r}; "
            f"board_done[{SHARED_BOARD}]={got_done!r} 期望 {DONE_DAY!r})"
        )
    lines.append(f"P2 A snoozed[{SHARED_BOARD}] = {got_snooze}")
    lines.append(f"P2 A board_done[{SHARED_BOARD}] = {got_done}")

    # P3 —— 生产函数自报的落盘路径 == A 的 state 文件
    expected = runner.state_path(va).resolve()
    for path in reported:
        if path.resolve() != expected:
            raise PreconditionRejected(f"生产写辅助自报落盘于 {path.resolve()}, 与 state_path(A) {expected} 不符")
    lines.append(f"P3 写辅助自报落盘路径 == state_path(A) = {expected}")
    return lines


# ═══════════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════════


def run(share_state: bool) -> tuple[int, list[str]]:
    """跑一态，返回 (rc, 报告行)。脚本**不预期**任何一态会红，只如实报告。

    两态都**走完整条报告**再退出: 负控的价值恰恰在于存档里能同时看到「正向对照
    P1/P2/P3 全绿」与「隔离判据红」—— 只打一行异常的话, 读存档的人无法区分
    「隔离被破坏」与「整个流程崩了」。
    """
    report: list[str] = []
    mode = "share-state" if share_state else "isolated"
    report.append(f"== CARD-G6-10 双 vault 交互隔离 canary · mode={mode} ==")
    try:
        return _run_inner(share_state, report), report
    except IsolationFailed as exc:
        report.append(f"*** ISOLATION FAILED *** {exc}")
        return EXIT_ISOLATION_FAILED, report
    except PreconditionRejected as exc:
        report.append(f"*** PRECONDITION REJECTED *** {exc}")
        return EXIT_PRECONDITION_REJECTED, report
    except Exception as exc:  # noqa: BLE001
        # ⚠ Codex r1 MEDIUM-3: 任何**别的**异常都不许走成 rc=1。rc=1 只能有一个含义
        # ——「隔离被破坏」。让崩溃与负控命中共用一个退出码，等于让读存档的人无法
        # 区分「门抓到了串台」与「跑挂了」，负控从此不可信。
        report.append(f"*** UNEXPECTED ERROR *** {type(exc).__name__}: {exc}")
        report.append(traceback.format_exc())
        return EXIT_PRECONDITION_REJECTED, report


def _run_inner(share_state: bool, report: list[str]) -> int:
    # ⛔ 顺序是契约，且这一段的次序本身是实测出来的教训（Codex r1 HIGH-1 的收口）：
    #   ① 加载 runner（只拉 stdlib + send_bark + local_tz，不碰第三方重依赖）
    #   ② 由它派生受保护位置
    #   ③ **验 TMPDIR**
    #   ④ 才 import app.*（这一步会拉起 jieba / torch 等，它们会往 TMPDIR 写缓存）
    #   ⑤ 才 mkdtemp（它自己就会建目录）
    # ④ 排在 ③ 之后是承重的：本卡实测把 TMPDIR 指到真 backups/ 时，即使守卫在
    # mkdtemp 之前就拒了跑，**import 链已经先往那里写了 jieba.cache 与
    # torchinductor 目录** —— 守卫挡住了自己的写面，却没挡住它自己的 import 副作用。
    runner, protected = _load_runner()
    report.append("-- 前置（import app.* 与 mkdtemp 之前）--")
    report.extend(_assert_tempdir_anchor(protected))

    from app.api.v1.endpoints.review_overview import _write_board_done, _write_board_snooze

    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix="g610-canary-"))
    try:
        tmp_repo = tmp_root / "repo"
        tmp_repo.mkdir(parents=True)
        _point_runner_at(runner, tmp_repo)
        vaults_root = _BACKEND.parent
        va, vb = _plan_vault_pair(tmp_root, share_state)

        # ---- 第 1 层：前置（⛔ 在 _materialize_vault 落任何字节**之前**）----
        report.append("-- 前置 --")
        report.extend(_assert_write_surface_is_tmp(runner, tmp_root, (va, vb), protected))
        for v in (va, vb):
            v.mkdir(parents=True, exist_ok=True)
            _materialize_vault(v)
        report.append(_assert_patch_live_on_production_path(vaults_root, runner))
        report.extend(_assert_mode_shape(runner, va, vb, share_state))
        report.extend(_group_dimension(va, vb, share_state))

        # ---- seed：两库落同一条「上次推荐」，seed 完必须逐字节相同 ----
        for v in (va, vb):
            with runner.state_locked(v):
                st = runner.load_state(v)
                st.setdefault("board_last_recommended", {})[SHARED_BOARD] = SEED_DAY
                runner.save_state(st, v)
        sha_a_seed = _sha256_file(runner.state_path(va))
        sha_b_seed = _sha256_file(runner.state_path(vb))
        report.append("-- seed --")
        report.append(f"seed sha A = {sha_a_seed}")
        report.append(f"seed sha B = {sha_b_seed}")
        if sha_a_seed != sha_b_seed:
            raise PreconditionRejected(
                "两库 seed 后 state 不逐字节相同 —— 「A 变了 B 没变」会因为两文件本来就不同而失去意义"
            )
        report.append("seed sha A == seed sha B ✓（同名攻击形状：两库起点逐字节相同）")

        # ---- 取样 before ----
        sha_b_before = _sha256_file(runner.state_path(vb))
        tree_b_before = _tree_digest(vb)

        # ---- 对 A 做一次 snooze + 一次 board-done（复用生产写路径）----
        reported = [
            _write_board_snooze(va, vaults_root, SHARED_BOARD, SNOOZE_UNTIL_ISO),
            _write_board_done(va, vaults_root, SHARED_BOARD, DONE_DAY),
        ]
        report.append("-- 对 A 的操作（复用生产写辅助，不经 HTTP）--")
        report.append(f"_write_board_snooze(A, …, {SHARED_BOARD!r}, {SNOOZE_UNTIL_ISO!r})")
        report.append(f"_write_board_done(A, …, {SHARED_BOARD!r}, {DONE_DAY!r})")

        # ---- 第 2 层：正向对照 ----
        sha_a_after = _sha256_file(runner.state_path(va))
        report.append("-- 正向对照（证明 A 确有本次写入）--")
        report.extend(_assert_a_really_written(runner, va, sha_a_seed, sha_a_after, reported))

        # ---- 第 3 层：隔离判据 ----
        sha_b_after = _sha256_file(runner.state_path(vb))
        tree_b_after = _tree_digest(vb)
        report.append("-- 隔离判据（B 库逐字节不变）--")
        report.append(f"B state file   = {runner.state_path(vb)}")
        report.append(f"B state before = {sha_b_before}")
        report.append(f"B state after  = {sha_b_after}")
        report.append(f"B vault tree before = {tree_b_before}")
        report.append(f"B vault tree after  = {tree_b_after}")

        breaches: list[str] = []
        if sha_b_before != sha_b_after:
            breaches.append(
                f"A 的 snooze/done 改到了 B 的 state 文件: {runner.state_path(vb)} "
                f"before={sha_b_before} after={sha_b_after}"
            )
        if tree_b_before != tree_b_after:
            breaches.append(f"A 的操作改动了 B 的 vault 目录树: before={tree_b_before} after={tree_b_after}")
        if breaches:
            raise IsolationFailed("; ".join(breaches))

        report.append("ISOLATION OK —— B 的 state 与 vault 树逐字节不变，A 确有本次写入")
        return EXIT_OK
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="CARD-G6-10 双 vault 交互隔离 canary（state 文件 per-vault）")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--isolated", action="store_true", help="正例（默认）：两库目录名不同 ⇒ 两个 state 文件")
    grp.add_argument(
        "--share-state",
        action="store_true",
        help="负控：只把 B 的目录名改成与 A 相同 ⇒ 生产 vault_key 把两库算成同一个 state 文件",
    )
    args = ap.parse_args()

    rc, report = run(share_state=args.share_state)
    # ⛔ Codex r2 MEDIUM-2: 输出本身也必须在异常边界内。原版把 print 放在 run() 之外，
    # 于是一次 UnicodeEncodeError（报告全是中文，PYTHONIOENCODING=ascii 就会炸）也会让
    # 进程以 rc=1 退出 —— 与「隔离被破坏」撞码。rc=1 只能有一个含义。
    try:
        print("\n".join(report))
        print(live_port_guard.STATE.summary_line())
        print(f"verdict={_VERDICT.get(rc, 'UNKNOWN')} rc={rc}")
    except Exception as exc:  # noqa: BLE001
        # 报告打不出来 ⇒ 这一跑的结论无从查验 ⇒ 按「实验没做成」收场，不是隔离结论。
        # 这里只写 ASCII，避免在处理编码错误时再触发一次编码错误。
        sys.stderr.write(f"G610 PRECONDITION REJECTED: report output failed: {type(exc).__name__}\n")
        sys.exit(EXIT_PRECONDITION_REJECTED)
    sys.exit(rc)


if __name__ == "__main__":
    main()
