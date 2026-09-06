#!/usr/bin/env python3
"""CARD-G2-9 — 双 vault 数据隔离 canary（三存储端到端，非单点测试）。

主 goal 的定语是「跨 vault」。在本脚本之前，隔离只有单点单测
（``tests/unit/test_lancedb_vault_isolation.py`` 的表名前缀契约、
``tests/regression/test_write_side_group_guard.py`` 的写侧不回落），
**没有任何一处把三个存储串起来跑过一遍**。本脚本补的就是这一段：
两个 vault 用**完全相同**的资产标识（同 canvas 路径 / 同 node ID /
同 concept 名 / 同 user ID / 同 doc_id）各写各的，然后逐存储对账。

判据（全部成立才 rc=0）：
  1. A 计数 == B 计数 > 0（三存储各自成立）
  2. 以 A 的 scope 查 B 的键 = 0 命中；反向同（**交叉 0 命中**）
  3. 删 A 全部后 A 计数 = 0、B 计数 == **删之前记下的那个数**
     （删前先记数，不是删后拿"现在的 B"跟"现在的 B"比 —— 那是自证）

⛔ blocked=0 **不单独构成**隔离成立的证据。门只证明"没打到现网库"，
   隔离要靠上面三条 + 负控（同一脚本换 ``NEO4J_TEST_URI`` / ``LANCEDB_DATA_PATH``
   重跑，必须 rc=2）+ ``--verify-judges``（每条判据都被证明能翻红）一起说话。
   本脚本**没有** ``--negctl`` 开关，负控靠的是换环境变量重跑。

装门（(e)，裸脚本的必修课）：
  pytest 侧的端口门由 ``tests/conftest.py::pytest_configure`` 装。**裸脚本
  不经 pytest ⇒ 不装门则 blocked 恒 0 = 假绿**。所以本脚本的第一段可执行
  代码（stdlib import 之后、任何 ``app.`` / ``lib.`` / ``neo4j`` /
  ``lancedb`` / ``graphiti_core`` import 之前）就装门：
  ``live_port_guard.install()`` + ``register_final_accounting()``，
  收尾 ``write_ledger()``。
  ``install()`` 在 uvloop 已被提前 import 时会 raise —— 那是门在说话，
  **不得**把装门挪到 import 之后换取跑通。

用法：
  NEO4J_TEST_URI=bolt://localhost:7692 \\
  LANCEDB_DATA_PATH=$(mktemp -d) \\
  backend/.venv/bin/python backend/scripts/g29_dual_vault_canary.py \\
      --evidence-dir _bmad-output/审查/evidence-g29

  负控（判据 4）：
  NEO4J_TEST_URI=bolt://localhost:7691 … （同上）→ 必须 rc≠0

退出码：
  0 = 三存储隔离判据全部成立
  1 = 隔离判据失败（本脚本自己的断言）
  2 = 前置/配置被拒（含负控命中：URI 不指向测试容器、LanceDB 路径未显式指 tmp）
  3 = 端口门的最终总账强制退出（``live_port_guard._final_accounting``）

数据落点：只有 7692 测试容器与显式传入的 tmp LanceDB 目录。默认
``data/lancedb`` 被**显式拒绝**（见 :func:`_preflight_lancedb_path`）——
现网 LanceDB 就在那个默认路径下。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
import tempfile
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

# ═══════════════════════════════════════════════════════════════════════════
# (e) 装门 —— 第一段可执行代码，必须早于任何业务 import
#
# 这几行的顺序是契约，不是风格：live_port_guard 只依赖 stdlib，装门时进程里
# 还没有 neo4j / lancedb / graphiti_core / app.*，所以 uvloop 毒化与 audit
# hook 覆盖得到后续**全部**出站连接。把任何业务 import 提到这一段之前，
# install() 的 uvloop 检查就可能已经晚了。
# ═══════════════════════════════════════════════════════════════════════════

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND / "tests" / "support"))

import live_port_guard  # noqa: E402  # pyright: ignore[reportMissingImports]
#   ^ sys.path 是上面两行动态插进去的，静态分析器看不到 tests/support/

live_port_guard.install()
live_port_guard.register_final_accounting()

sys.path.insert(0, str(_BACKEND))


# ═══════════════════════════════════════════════════════════════════════════
# 契约常量：A/B 两个 vault 用**完全相同**的资产标识
#
# 相同标识是本 canary 的全部要害。任何一层隔离失效都会当场表现为
# 「计数翻倍 / 交叉命中 / 删 A 带走 B」——如果 A/B 用不同的名字，
# 三条判据会因为"名字本来就不一样"而恒真，canary 变成一场自证。
# ═══════════════════════════════════════════════════════════════════════════

#: 两个 vault 的 D16 逻辑 group_id（物理化后 `vault__g29canary_a` / `..._b`，
#: 互不为前缀 —— R4 的前缀语义命中条件是 `scope + "__"`，两者隔着不同的
#: 末段，A 的 scope 吃不到 B）。固定值而非随机值：(a) 要求连跑两次的报告
#: 剥掉时间戳后 diff 为空，随机 group 名会让报告每次都不同。幂等靠
#: 每次跑的头尾 purge 保证。
VAULT_A = "vault:g29canary_a"
VAULT_B = "vault:g29canary_b"

#: 两 vault 共用的资产标识（(a) 的「同路径/同 node ID/同 concept/同 user ID」）
SHARED_CANVAS_PATH = "双vault验证/同名白板.canvas"
SHARED_NODE_ID = "g29-node-0001"
SHARED_CONCEPT = "同名概念"
SHARED_USER_ID = "g29-canary-user"
SHARED_DOC_ID = "g29-doc-0001"
SHARED_ENTITY_NAME = "同名实体"
SHARED_EPISODE_NAME = "同名情节"

#: LanceDB 逻辑表名（经 ``resolve_table_name`` 前缀化成 `<vault_id>_canvas_nodes`）
LANCE_TABLE = "canvas_nodes"

#: canary 用的向量维度。刻意用小维度：本卡证的是**隔离**，不是检索质量，
#: 8 维既不碰 embedding 服务也让写入是确定性的（(a) 的可重复执行）。
CANARY_VECTOR_DIM = 8


def _physical_of(logical_group_id: str) -> str:
    """逻辑 group_id → Neo4j/Graphiti 物理格式（M8 变异定位兄弟组时用）。"""
    from app.graphiti.group_id_compat import to_physical_group_id

    return to_physical_group_id(logical_group_id)


#: 固定 created_at —— 报告要能 diff，节点属性里就不能有墙钟。
FIXED_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


#: LanceDB 路径的**正面白名单**：只允许落在这些临时目录根下。
#:
#: ⛔ 为什么是白名单而不是「拒绝 data/lancedb」的黑名单 —— 这是抄
#: :data:`live_port_guard.ALLOWED_TEST_PORTS` 的作业（那条注释里写着黑名单
#: 判据被两轮独立终审判为 BLOCKER 的经过）：现网 LanceDB 的落点不止一个
#: （2026-09-05 实测同时存在 ``<repo>/data/lancedb``、``backend/data/lancedb``、
#: 各 worktree 下的同名目录，compose 里还有容器内的 ``/lancedb``），要靠黑名单
#: 挡住就得枚举全部现网落点 —— 漏一个就是往现网库里写。反过来「只允许 tmp」
#: 只有一个正确答案，默认拒绝一切其它值。
#:
#: macOS 上 ``tempfile.gettempdir()`` 给的是 ``/var/folders/…``，而 ``/tmp``
#: 是指向 ``/private/tmp`` 的 symlink —— 三个根都要列，且比较前一律 resolve()。
def _tmp_roots() -> tuple[pathlib.Path, ...]:
    roots = []
    for raw in (tempfile.gettempdir(), "/tmp", "/private/tmp"):
        try:
            roots.append(pathlib.Path(raw).resolve())
        except OSError:
            continue
    return tuple(dict.fromkeys(roots))


#: 即便开了 ``--allow-path-outside-tmp`` 也绝不放行的落点（纵深，非主判据）。
#: 不写裸 ``lancedb``：那会误伤 ``/tmp/lancedb`` 这类合法的临时目录。
FORBIDDEN_LANCEDB_SUFFIXES = ("data/lancedb",)

EXIT_OK = 0
EXIT_ISOLATION_FAILED = 1
EXIT_PRECONDITION_REJECTED = 2


class PreconditionRejected(RuntimeError):
    """前置/配置被拒（负控命中也走这里）。携带「被哪一层拒的」。"""

    def __init__(self, message: str, *, rejected_by: str, source: str) -> None:
        super().__init__(message)
        #: 拒因来源的**函数身份**（负控判据绑定它，不是只看 rc≠0）
        self.rejected_by = rejected_by
        #: 拒因来源的**文件:行**（人读的锚点）
        self.source = source


class IsolationFailed(AssertionError):
    """隔离判据不成立。``report`` 带上跑到一半的报告，验伪模式要读它。"""

    def __init__(self, message: str, *, report: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.report = report or {}


# ═══════════════════════════════════════════════════════════════════════════
# 验伪锚：让每条判据都被证明**能翻红**
#
# ⛔ 「全部判据 PASS」本身不构成任何证据 —— 恒真的判据也会全 PASS。
#    ``--verify-judges`` 逐条注入一个已知会破坏隔离的变异，要求**指定的那条
#    判据**当场变红。判据不是"有东西红了"，而是"红的正好是它"：一条变异让
#    别的判据红而目标判据仍绿，算 SURVIVED，脚本 rc≠0。
#
#    每条变异都先自证**生效**（打印注入后的实际取值），否则"没红"分不清是
#    "门够硬"还是"变异压根没打进去"。
# ═══════════════════════════════════════════════════════════════════════════

#: 当前注入的变异（None = 正常运行）。只由 ``--verify-judges`` 设置。
_MUTATION: str | None = None

MUTATION_SPECS: dict[str, dict[str, Any]] = {
    "M1_same_identity": {
        "what": "B 的三存储身份被改成与 A 逐字相同 —— 隔离彻底不存在",
        "breaks": "整个 vault 命名空间",
        "expect_red": [
            "identities_distinct",
            "shared_concept_split_per_group",
            "A_cannot_see_B",
            "B_unchanged_after_deleting_A",
        ],
    },
    "M2_no_scope_filter": {
        "what": "Neo4j 读侧的 group 过滤片段替换成 true —— R4「静默退化为全库读」",
        "breaks": "cypher-read-contract R4 / R1",
        # A_unaffected_by_B_write 挂在这里而不是 M10：作用域过滤失效后，A 的计数
        # 会把 B 的同名 Concept 一起数进来（1 → 2），这才是这条判据真正的敏感面。
        "expect_red": ["A_cannot_see_B", "B_cannot_see_A", "A_unaffected_by_B_write"],
    },
    "M3_unscoped_delete": {
        "what": "删 A 时按 name/path 删而不带 group scope —— W2「scoped delete」失效",
        "breaks": "cypher-write-contract W2",
        "expect_red": ["B_unchanged_after_deleting_A"],
    },
    "M4_empty_count_shape": {
        "what": "Neo4j 计数返回空 dict —— 首跑实测到的那个 all() 恒真假绿面",
        "breaks": "判据的形状前提",
        "expect_raises": "键集",
    },
    "M5_lancedb_bare_table": {
        "what": "LanceDB 绕开 resolve_table_name 直接开表 —— G2-4 删掉的裸表回退",
        "breaks": "LanceDB 表名命名空间（G2-4）",
        "expect_red": ["A_cannot_see_B", "B_cannot_see_A"],
    },
    # ── round-1 整改新增（Codex MEDIUM-2：原 5 条去重后只点名 4/12 个判据）──
    "M6_skip_write_A": {
        "what": "A 的 LanceDB 写入被跳过 —— 资产没真正落盘",
        "breaks": "「写进去了」这个前提本身",
        "expect_red": ["A_counts_positive", "A_equals_B"],
    },
    "M7_skip_write_B": {
        "what": "B 的 LanceDB 写入被跳过（A/B 对称面，不能只验一侧）",
        "breaks": "同上，反向",
        "expect_red": ["B_counts_positive", "A_equals_B"],
    },
    "M8_sentinel_scope_divergence": {
        "what": "graphiti 的读真的变宽（多带一个兄弟组）—— 系统侧制造口径分叉，不是改判据参数",
        "breaks": "两套读口径的等价性（graphiti 精确等值 vs 生产 vault_scope）",
        "expect_red": ["read_scope_sentinels_clean"],
    },
    "M9_no_delete": {
        "what": "三个面的删除全部 no-op（计数照实数，拆的是删除本身不是计数器）",
        "breaks": "删除路径本身",
        "expect_red": [
            "A_gone_after_delete",
            "graphiti_delete_is_load_bearing",
            "lancedb_delete_is_load_bearing",
        ],
    },
    "M12_graphiti_delete_only_broken": {
        # ⛔ 这条是 round-2 复核的产物，也是最锋利的一条：**只**坏 graphiti 删除，
        #    业务扫荡照跑。第一版的判据在它面前会全绿（计数器仍 > 0、A_after_delete
        #    仍是 0，因为扫荡替它把活干了）——那正是"修复只是移位"的形态。
        #    现在靠 residual 的就地取证抓住它。
        "what": "只坏 graphiti 删除，业务扫荡照跑 —— 专打「修复是否只是移位」",
        "breaks": "graphiti 删除路径（单独一面）",
        "expect_red": ["graphiti_delete_is_load_bearing"],
    },
    "M11_purge_leaves_residue": {
        "what": "清理跑完仍留下 A 的业务节点 —— 起点不干净",
        "breaks": "报告的起点前提（计数是本轮写的，不是上轮遗留）",
        "expect_red": ["purge_left_nothing"],
    },
    "M10_b_writes_into_a": {
        "what": "B 的业务写入落进 A 的 group —— 跨 vault 写污染",
        "breaks": "写侧 vault 归属（W1）",
        # ⚠️ 只点名 shared_concept_split_per_group。初版还点了
        # A_unaffected_by_B_write，实测 SURVIVED —— 根因值得留着：
        # create_learning_relationship 用的是 `MERGE (c:Concept {name, group_id})`，
        # B 拿 A 的 group 写同名概念时**幂等地并到了 A 已有的那个节点上**，
        # A 的计数纹丝不动。所以「计数不受对方影响」这条判据对**这种形状**的
        # 跨 vault 污染天生失明；抓住它的是「同名概念被拆成几个 group」那条
        # （B 从此不再有自己的节点，分布从 {A:1,B:1} 塌成 {A:1}）。
        # 判据各有盲区，靠的是**判据集合**互补，不是任何单独一条。
        "expect_red": ["shared_concept_split_per_group"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# scope 串行化：(a) 的「顺序切换 scope，禁同一时刻混跑两套 scope」
#
# 这不是口头声明 —— ``scope_session`` 在进入时断言当前没有别的活跃 scope，
# 存储层的每个调用都先过 :func:`_require_scope`。真要有人写出并发混跑，
# 会当场 raise 而不是给出一份看起来正常的报告。
# ═══════════════════════════════════════════════════════════════════════════

_ACTIVE_SCOPE: str | None = None


@contextmanager
def scope_session(vault_id: str) -> Iterator[str]:
    """独占式 scope 会话。嵌套/并发进入即 raise。"""
    global _ACTIVE_SCOPE
    if _ACTIVE_SCOPE is not None:
        raise IsolationFailed(
            f"scope 混跑：{_ACTIVE_SCOPE!r} 还活着就要进 {vault_id!r}。(a) 要求顺序切换 scope，同一时刻只允许一套。"
        )
    _ACTIVE_SCOPE = vault_id
    try:
        yield vault_id
    finally:
        _ACTIVE_SCOPE = None


def _require_scope(vault_id: str) -> None:
    if _ACTIVE_SCOPE != vault_id:
        raise IsolationFailed(f"存储调用的 scope 是 {vault_id!r}，但当前活跃 scope 是 {_ACTIVE_SCOPE!r}。")


# ═══════════════════════════════════════════════════════════════════════════
# 前置检查（(d)：只用 7692 与 tmp LanceDB）
# ═══════════════════════════════════════════════════════════════════════════


def _raise_site(exc: BaseException) -> str:
    """异常**实际**抛出的位置（最内层帧），形如 ``live_port_guard.py:912 (函数名)``。

    负控的判据是「被哪一层拒的」。把来源写成固定字符串，等于对同一函数里的
    其它 raise 分支错归因——本脚本调的 ``assert_test_uri_not_blocked`` 就有三条
    互不相同的 raise 分支。这里从 traceback 的最后一帧实取：谁抛的就报谁。
    """
    tb = traceback.extract_tb(exc.__traceback__)
    if not tb:
        return "<无 traceback>"
    frame = tb[-1]
    return f"{pathlib.Path(frame.filename).name}:{frame.lineno} ({frame.name})"


def _preflight_neo4j_uri() -> str:
    """``NEO4J_TEST_URI`` 必须显式配置且经门的白名单（(d) / (f)）。

    ⛔ 这里**不自己解析端口**：门的 :func:`live_port_guard.assert_test_uri_not_blocked`
    走的是 neo4j 驱动自己的解析链（``canonical_target_ports``），而"另写一个
    解析器"正是 W4-3a 删掉 ``_port_of_uri`` 的原因 —— 两个解析器必然分叉，
    每次分叉都是一个洞（``bolt://127.0.0.1:0`` 被自写解析器读成 0，驱动读成
    7687 = 现网默认端口）。负控靠的就是这一层，它必须是**门的**那一层。
    """
    uri = os.environ.get("NEO4J_TEST_URI")
    if not uri:
        raise PreconditionRejected(
            "NEO4J_TEST_URI 未设置。本 canary 拒绝猜测目标库 —— 必须显式写 "
            "bolt://localhost:7692（测试容器），绝不落到 7691/7687 现网库。",
            rejected_by="g29_dual_vault_canary._preflight_neo4j_uri",
            source="g29_dual_vault_canary.py::_preflight_neo4j_uri（本脚本前置检查）",
        )
    try:
        live_port_guard.assert_test_uri_not_blocked()
    except RuntimeError as exc:
        raise PreconditionRejected(
            f"端口门拒绝了 NEO4J_TEST_URI={uri!r}：{exc}",
            rejected_by="live_port_guard.assert_test_uri_not_blocked",
            # ⛔ 来源**实取**，不是写死的标签（Codex round-1 LOW-5）：
            #    assert_test_uri_not_blocked 有三条互不相同的 raise 分支——白名单
            #    与受拦集合相交(:893)、驱动口径解析不出端口(:903)、端口不在白名单
            #    (:912)。写死其中一条等于对另外两条错归因，而"判据绑定被哪一层
            #    拒的"正是本卡负控的立足点，归因错了负控就白做。
            source=_raise_site(exc),
        ) from exc
    return uri


def _preflight_lancedb_path(cli_path: str | None, *, allow_outside_tmp: bool) -> str:
    """LanceDB 路径必须显式指定**且落在临时目录下**（(d)）。

    三道判据，顺序即优先级：

    1. **必须显式** —— 不配就会落到 ``LanceDBClient`` 的默认值 ``data/lancedb``，
       那是现网库（2026-09-05 实测该目录在主仓与 backend/ 下各有一份实数据）。
    2. **必须在 tmp 根下**（正面白名单，见 :func:`_tmp_roots` 的说明）。
       ``--allow-path-outside-tmp`` 是显式逃生阀，用了会在报告里留痕。
    3. **纵深**：即便开了逃生阀，命中 :data:`FORBIDDEN_LANCEDB_SUFFIXES` 仍拒。

    ⛔ 判据全部在 ``mkdir`` **之前**：拒绝一条路径的同时把它建出来，等于
    canary 自己在现网位置留下了痕迹。
    """
    raw = cli_path or os.environ.get("LANCEDB_DATA_PATH")
    if not raw:
        raise PreconditionRejected(
            "LanceDB 路径未显式指定（--lancedb-path 或 LANCEDB_DATA_PATH 均为空）。"
            "不指定就会落到 LanceDBClient 的默认值 data/lancedb —— 那是现网库。",
            rejected_by="g29_dual_vault_canary._preflight_lancedb_path",
            source="g29_dual_vault_canary.py::_preflight_lancedb_path（本脚本前置检查）",
        )
    resolved = pathlib.Path(os.path.expanduser(raw)).resolve()
    norm = str(resolved).replace("\\", "/")
    for bad in FORBIDDEN_LANCEDB_SUFFIXES:
        if norm.endswith(bad):
            raise PreconditionRejected(
                f"LanceDB 路径 {resolved} 指向现网默认库（*/{bad}）。canary 只许写 tmp。",
                rejected_by="g29_dual_vault_canary._preflight_lancedb_path",
                source="g29_dual_vault_canary.py::_preflight_lancedb_path（本脚本前置检查）",
            )
    roots = _tmp_roots()
    if not allow_outside_tmp and not any(resolved == r or r in resolved.parents for r in roots):
        raise PreconditionRejected(
            f"LanceDB 路径 {resolved} 不在任何临时目录根下（允许的根：{list(map(str, roots))}）。"
            "canary 只往 tmp 写；确需别处请显式加 --allow-path-outside-tmp。",
            rejected_by="g29_dual_vault_canary._preflight_lancedb_path",
            source="g29_dual_vault_canary.py::_preflight_lancedb_path（本脚本前置检查）",
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return str(resolved)


# ═══════════════════════════════════════════════════════════════════════════
# 存储层适配（三个存储各一组 写 / 计数 / 交叉查 / 删）
#
# 一律走**生产写路径**，不自己拼等价 Cypher：
#   * Neo4j  → Neo4jClient.create_learning_relationship / create_canvas_node_relationship
#              （W1 复合键 MERGE 就在它们里面，绕开就等于没验生产行为）
#   * Graphiti → graphiti_core 的 EpisodicNode / EntityNode.save（add_episode 的落库产物，
#              但不经 LLM —— 本卡证隔离不证抽取质量）
#   * LanceDB → LanceDBClient.add_documents（第一行就是 resolve_table_name）
# ═══════════════════════════════════════════════════════════════════════════


class Neo4jFacet:
    """Neo4j 业务节点面（Concept/LEARNED/Canvas/Node/CONTAINS_NODE）。"""

    name = "neo4j"

    def __init__(self, client: Any, physical_group_id: str, vault_id: str) -> None:
        self._c = client
        self.gid = physical_group_id
        self._vault = vault_id

    async def write(self) -> None:
        _require_scope(self._vault)
        gid = self.gid
        if _MUTATION == "M10_b_writes_into_a" and self._vault == VAULT_B:
            # 验伪：B 的业务写入落进 A 的 group（跨 vault 写污染）
            from app.graphiti.group_id_compat import to_physical_group_id

            gid = to_physical_group_id(VAULT_A)
        ok1 = await self._c.create_learning_relationship(
            user_id=SHARED_USER_ID,
            concept=SHARED_CONCEPT,
            score=3,
            group_id=gid,
        )
        ok2 = await self._c.create_canvas_node_relationship(
            canvas_path=SHARED_CANVAS_PATH,
            node_id=SHARED_NODE_ID,
            node_text="双 vault canary 节点",
            group_id=gid,
        )
        if not (ok1 and ok2):
            raise IsolationFailed(
                f"Neo4j 写入未成功（learning={ok1}, canvas_node={ok2}）；"
                "写侧 fail-closed 拒写时也会返回 False，先查 group_id 解析。"
            )

    #: 固定键集。⛔ 计数**必须**按这个集合补齐：Cypher 的分组聚合在**空输入**
    #: 下返回 **0 行**（``RETURN 'concept' AS kind, count(c) AS n`` 里的字面量
    #: 是分组键，没有输入行就没有分组），于是"什么都没查到"会得到 ``{}`` 而不是
    #: 全 0 —— 而 ``all(x > 0 for x in {}.values())`` 与 ``all(x == 0 …)``
    #: **同时为 True**。2026-09-05 首跑实测：删 A 之后 neo4j 计数就是 ``{}``，
    #: "A 已清空"和"A 计数为正"两条判据会一起假通过。
    KINDS = ("concept", "learned", "canvas", "node", "contains_node")

    async def count(self, scope_gid: str, only_group: str | None = None) -> dict[str, int]:
        """在 ``scope_gid`` 的**生产读作用域**下计数；``only_group`` 叠加归属条件。

        作用域过滤用的是生产读侧的 :func:`app.core.vault_scope.read_group_filter`
        （等值 OR ``scope + "__"`` 前缀，R4 语义），**不是**本脚本自写的 WHERE ——
        canary 要验的是生产读侧排他，自己另写一套等价条件等于验自己。

        每个 alias（含关系 ``r`` / ``e``）逐一过滤，满足 R1 全覆盖；不依赖
        「关系与端点必同组」这个在存量图上不可证的前提。

        ``only_group`` 是**交叉查询**的那一半：以 A 的作用域去数"归属为 B"的
        数据。隔离成立时它恒 0；若谁把作用域过滤写成了会吃掉兄弟组的前缀
        （例如 scope 退化成 ``vault__g29canary``），它会立刻变成 1。
        """
        from app.core.vault_scope import read_group_filter, read_scope_params

        if _MUTATION == "M4_empty_count_shape":
            return {}  # 验伪：空键集会让 all() 恒真，形状门必须抓住

        params = read_scope_params(scope_gid, context="g29_canary.Neo4jFacet.count")

        def f(alias: str) -> str:
            if _MUTATION == "M2_no_scope_filter":
                # 验伪：R4 禁止的「group 缺失就不过滤」——作用域过滤整条失效
                return "true"
            return read_group_filter(alias)

        rows = await self._c.run_query(
            f"""
            CALL {{
                MATCH (c:Concept)
                WHERE {f("c")} AND c.name = $concept
                  AND ($only IS NULL OR c.group_id = $only)
                RETURN 'concept' AS kind, count(c) AS n
              UNION ALL
                MATCH (u:User)-[r:LEARNED]->(c:Concept)
                WHERE {f("r")} AND {f("c")} AND c.name = $concept
                  AND ($only IS NULL OR (r.group_id = $only AND c.group_id = $only))
                RETURN 'learned' AS kind, count(r) AS n
              UNION ALL
                MATCH (b:Canvas)
                WHERE {f("b")} AND b.path = $path
                  AND ($only IS NULL OR b.group_id = $only)
                RETURN 'canvas' AS kind, count(b) AS n
              UNION ALL
                MATCH (n:Node)
                WHERE {f("n")} AND n.id = $node
                  AND ($only IS NULL OR n.group_id = $only)
                RETURN 'node' AS kind, count(n) AS n
              UNION ALL
                MATCH (b:Canvas)-[e:CONTAINS_NODE]->(n:Node)
                WHERE {f("b")} AND {f("e")} AND {f("n")}
                  AND b.path = $path AND n.id = $node
                  AND ($only IS NULL OR (b.group_id = $only
                       AND e.group_id = $only AND n.group_id = $only))
                RETURN 'contains_node' AS kind, count(e) AS n
            }}
            RETURN kind, n
            """,
            concept=SHARED_CONCEPT,
            path=SHARED_CANVAS_PATH,
            node=SHARED_NODE_ID,
            only=only_group,
            **params,
        )
        got = {str(r["kind"]): int(r["n"]) for r in rows}
        return {k: got.get(k, 0) for k in self.KINDS}

    async def group_distribution(self) -> dict[str, int]:
        """全库按 group_id 数「同名 Concept」——证明同名资产被**拆成了几个物理节点**。

        这条刻意**不带**作用域过滤（跨 vault 读，R2 声明式豁免：canary 的
        职责就是从库的全局视角核对拆分结果）。隔离成立时它恰好是
        ``{A: 1, B: 1}``；若 W1 的复合键 MERGE 退化成 ``MERGE (c:Concept {name})``，
        它会变成单个 group 计 1（后写方 SET 覆盖先写方归属）。
        """
        rows = await self._c.run_query(
            "MATCH (c:Concept) WHERE c.name = $concept RETURN c.group_id AS g, count(c) AS n",
            concept=SHARED_CONCEPT,
        )
        return {str(r["g"]): int(r["n"]) for r in rows}

    async def delete(self, gid: str) -> None:
        """删本 group 的全部业务节点。

        ⚠️ 刻意**不删 User**：``create_learning_relationship`` 的
        ``MERGE (u:User {id: $userId})`` **不带 group_id**（neo4j_client.py:1021），
        所以 A 与 B 共用同一个物理 User 节点。删 A 时连 User 一起删会把 B 的
        LEARNED 边一并 DETACH 掉 —— 那是 canary 自己制造的"泄漏"，不是被测行为。
        共享 User 节点本身是既有设计，本卡如实记录、不改（硬边界禁改 neo4j_client.py）。
        """
        if _MUTATION == "M3_unscoped_delete":
            # 验伪：W2 要求 DELETE 默认带 group scope。这里按业务键删、不带 group，
            # 于是"删 A"会连 B 的同名资产一起带走。
            await self._c.run_query(
                "MATCH (c:Concept) WHERE c.name = $concept DETACH DELETE c",
                concept=SHARED_CONCEPT,
            )
            await self._c.run_query(
                "MATCH (b:Canvas) WHERE b.path = $path DETACH DELETE b",
                path=SHARED_CANVAS_PATH,
            )
            await self._c.run_query(
                "MATCH (n:Node) WHERE n.id = $node DETACH DELETE n",
                node=SHARED_NODE_ID,
            )
            return
        if _MUTATION == "M9_no_delete":
            return  # 验伪：删除整体 no-op（M12 只坏 graphiti 一面，业务扫荡照跑）
        await self._c.run_query("MATCH (n) WHERE n.group_id = $g DETACH DELETE n", g=gid)


class GraphitiFacet:
    """Graphiti 写入面（graphiti_core 落的 EpisodicNode / EntityNode）。"""

    name = "graphiti"

    def __init__(self, driver: Any, graphiti_group_id: str, vault_id: str) -> None:
        self._d = driver
        self.gid = graphiti_group_id
        self._vault = vault_id

    async def write(self) -> None:
        _require_scope(self._vault)
        from graphiti_core.nodes import EntityNode, EpisodeType, EpisodicNode

        ep = EpisodicNode(
            name=SHARED_EPISODE_NAME,
            group_id=self.gid,
            source=EpisodeType.text,
            source_description="g29 dual-vault canary",
            content="两个 vault 写入完全相同的情节内容。",
            valid_at=FIXED_TS,
            created_at=FIXED_TS,
            entity_edges=[],
        )
        await ep.save(self._d)
        en = EntityNode(
            name=SHARED_ENTITY_NAME,
            group_id=self.gid,
            labels=["Entity"],
            summary="g29 dual-vault canary entity",
            created_at=FIXED_TS,
            # name_embedding 必填：EntityNode.save 会调 Neo4j 的
            # db.create.setNodeVectorProperty，为 None 时服务端抛 NPE
            # （2026-09-05 于 7692 实测）。固定值 —— 报告要能 diff。
            name_embedding=[0.1] * CANARY_VECTOR_DIM,
        )
        await en.save(self._d)

    KINDS = ("episodic", "entity", "outside_read_scope")

    async def count(self, scope_gid: str, only_group: str | None = None) -> dict[str, int]:
        """走 graphiti_core 自己的 ``get_by_group_ids``（graphiti 的读侧口径本身）。

        ``outside_read_scope`` 是这一面的**验伪锚**：把 graphiti 返回的每个节点
        再过一遍生产的 :func:`app.core.vault_scope.group_in_read_scope`，数出
        「graphiti 交回来了、但按生产读侧语义不该被本作用域看见」的条数。
        它恒 0 才说明 graphiti 的等值口径与生产读侧口径没有分叉；只数
        ``episodic``/``entity`` 的话，graphiti 若哪天返回跨组数据也看不出来。
        """
        from graphiti_core.nodes import EntityNode, EpisodicNode

        from app.core.vault_scope import group_in_read_scope

        query_groups = [scope_gid]
        if _MUTATION == "M8_sentinel_scope_divergence":
            # ⛔ 变异打在**系统侧**（graphiti 的读真的多交回了别组的节点），
            #    不是打在判据自己的比较参数上。上一版把 sentinel 的比较 scope
            #    换成无关值 —— 那是改判据的输入，不是制造分叉（round-2 复核点名）。
            #    这里让查询多带一个兄弟组，等价于"graphiti 改成了更宽的匹配"：
            #    返回集合里真的出现本作用域看不见的节点。
            sibling = VAULT_B if scope_gid == _physical_of(VAULT_A) else VAULT_A
            query_groups = [scope_gid, _physical_of(sibling)]
        eps = await EpisodicNode.get_by_group_ids(self._d, query_groups)
        ens = await EntityNode.get_by_group_ids(self._d, query_groups)

        def _match(node: Any, want_name: str) -> bool:
            if node.name != want_name:
                return False
            return only_group is None or node.group_id == only_group

        # sentinel：graphiti 交回来的每个节点，按**生产读侧口径**是否真在本作用域内。
        # 正常路径下恒 0（graphiti 是精确等值过滤，见
        # evidence-g29/sentinel-self-audit-*.txt 的实测）；M8 让它的查询真的变宽
        # 之后，越界节点会出现在返回集合里，这一项随即非 0。
        outside = sum(1 for node in (*eps, *ens) if not group_in_read_scope(node.group_id, scope_gid))
        return {
            "episodic": sum(1 for x in eps if _match(x, SHARED_EPISODE_NAME)),
            "entity": sum(1 for x in ens if _match(x, SHARED_ENTITY_NAME)),
            "outside_read_scope": outside,
        }

    async def delete(self, gid: str) -> int:
        """删本 group 的 graphiti 节点，**返回实删条数**。

        返回值不是装饰：它是 ``graphiti_delete_is_load_bearing`` 判据的输入。
        没有它就无法区分「删干净了」和「本来就没东西可删」——初版正是后者
        （业务删除排在前面，顺带把 Episodic/Entity 清了），见 :func:`_purge`。
        """
        from graphiti_core.nodes import EntityNode, EpisodicNode

        skip = _MUTATION in ("M9_no_delete", "M12_graphiti_delete_only_broken")
        deleted = 0
        for cls in (EpisodicNode, EntityNode):
            for node in await cls.get_by_group_ids(self._d, [gid]):
                if not skip:
                    await node.delete(self._d)
                # ⛔ 计数**照实增**，哪怕删除被跳过：变异要拆的是**删除这条防线**，
                #    不是判据的输入。上一版在这里 `return 0`，那是在改判据读到的
                #    数字——门当然会红，但红得毫无信息量（见 M9 的整改记录）。
                deleted += 1
        return deleted

    async def residual(self, gid: str) -> int:
        """本 group 还剩几个 graphiti 节点。**必须在业务节点扫荡之前调用**。

        ⛔ 这个方法是 HIGH-1 真正的修复点（第一版只是把问题挪了个位置）：
        `_purge` 里业务删除的 `MATCH (n) WHERE n.group_id=$g DETACH DELETE n`
        **没有 label 限制**，即使把它排到最后，它仍会把 graphiti 删除**漏掉的**
        节点一并清走 —— 于是 `A_after_delete` 的 graphiti 面照样是 0，
        「graphiti 删除自己有没有生效」依旧没有证据。
        2026-09-06 实测复现：让 graphiti 删除只遍历不真删，计数器仍得 2、
        业务扫荡之后 graphiti 面仍是 0，两条判据双双被喂饱。
        取证只能取在**这一刻**：graphiti 删完、业务扫荡未跑。
        """
        from graphiti_core.nodes import EntityNode, EpisodicNode

        left = 0
        for cls in (EpisodicNode, EntityNode):
            left += len(await cls.get_by_group_ids(self._d, [gid]))
        return left


class LanceDBFacet:
    """LanceDB 面（表名经 ``resolve_table_name`` 前缀化）。"""

    name = "lancedb"

    def __init__(self, client: Any, vault_id: str) -> None:
        self._c = client
        self._vault = vault_id

    @property
    def table_name(self) -> str:
        return self._c.resolve_table_name(LANCE_TABLE)

    async def write(self) -> None:
        _require_scope(self._vault)
        if _MUTATION == f"M{6 if self._vault == VAULT_A else 7}_skip_write_{self._letter()}":
            return  # 验伪：本 vault 的 LanceDB 写入被跳过
        n = await self._c.add_documents(
            LANCE_TABLE,
            [
                {
                    "doc_id": SHARED_DOC_ID,
                    "content": "两个 vault 写入完全相同的文档内容。",
                    "vector": [0.1] * CANARY_VECTOR_DIM,
                    "canvas_file": SHARED_CANVAS_PATH,
                    "node_id": SHARED_NODE_ID,
                    # doc_type 必填：缺列会被 _check_and_fix_dimension_mismatch
                    # 判成 schema drift 并 drop 表（lancedb_client.py:3662-3690）。
                    "doc_type": "canvas_node",
                    "metadata": {"canary": "g29"},
                }
            ],
        )
        if n != 1:
            raise IsolationFailed(f"LanceDB 写入返回 {n}，期望 1")

    KINDS = ("rows", "table_exists")

    def _letter(self) -> str:
        """本 facet 属于 A 还是 B —— 只给 M6/M7 变异定位用。"""
        return "A" if self._vault == VAULT_A else "B"

    def count(self, logical_table: str = LANCE_TABLE) -> dict[str, int]:
        """经**生产入口** ``resolve_table_name`` 定位表，再数行。

        ⛔ 参数是**逻辑**表名，不是物理表名 —— 这正是交叉查询的要害：把 B 的
        物理表名（``g29canary_b_canvas_nodes``）交给 A 的 client，生产入口会把它
        **再前缀化**成 ``g29canary_a_g29canary_b_canvas_nodes``（一张不存在的表），
        A 因此到不了 B 的数据。若哪天 G2-4 删掉的"裸表回退"被谁加回来，
        这里就会退化成读到 B 的表，判据当场翻红。

        （直接 ``db.open_table("g29canary_b_canvas_nodes")`` 当然读得到 —— 两个
        vault 共用一个 LanceDB 目录，隔离边界在**表名**这一层，不在连接层。
        所以交叉判据必须走生产入口，绕开它去开表只是在证明"文件系统没锁"。）
        """
        if _MUTATION == "M5_lancedb_bare_table":
            # 验伪：G2-4 删掉的裸表回退 —— 绕开命名空间直接开表
            table_name = logical_table
        else:
            table_name = self._c.resolve_table_name(logical_table)
        db = self._c._db
        if db is None or table_name not in db.table_names():
            return {"rows": 0, "table_exists": 0}
        tbl = db.open_table(table_name)
        rows = tbl.search().where(f"doc_id = '{SHARED_DOC_ID}'").limit(100).to_list()
        return {"rows": len(rows), "table_exists": 1}

    def delete(self, vault_id_physical: str) -> int:
        """走生产 API ``drop_vault_tables``（按 vault 前缀删表）。

        ⚠️ 返回值是**尝试删的表数**，不是"实删数"：``drop_vault_tables``
        （`lancedb_client.py:866-877`）返回的是 ``len(tables)``，而它的循环里
        ``except Exception: pass`` **吞掉了单表删除失败**。所以这个数字单独
        不能作证，必须配 :meth:`residual`（Codex round-2 复核 LOW）。
        """
        tables = self._c.list_vault_tables(vault_id_physical)
        if _MUTATION == "M9_no_delete":
            # ⛔ 拆的是**删表这个动作**，不是判据读到的数字。上一版在这里
            #    `return 0`，那是伪造判据的输入 —— 门当然会红，但红得毫无信息量
            #    （与 graphiti 侧同一条理由，round-2 复核点名）。计数照实报，
            #    让 residual 那一半去抓。
            return len(tables)
        return int(self._c.drop_vault_tables(vault_id_physical) or 0)

    def residual(self) -> int:
        """本 vault 名下还剩几张表（补上 ``drop_vault_tables`` 吞异常的那个洞）。"""
        db = self._c._db
        if db is None:
            return 0
        prefix = f"{self._c.active_vault_id}_"
        return sum(1 for t in db.table_names() if t.startswith(prefix))


# ═══════════════════════════════════════════════════════════════════════════
# scope 装配
# ═══════════════════════════════════════════════════════════════════════════


class VaultScope:
    """一个 vault 在三个存储上的全部身份 + 客户端。"""

    def __init__(self, logical_group_id: str, uri: str, lancedb_path: str) -> None:
        from app.graphiti.group_id_compat import (
            sanitize_group_id_for_graphiti,
            to_physical_group_id,
        )

        if _MUTATION == "M1_same_identity":
            # 验伪：两个 vault 拿到逐字相同的身份 —— 隔离彻底不存在
            logical_group_id = VAULT_A
        self.logical = logical_group_id
        #: Neo4j 物理格式（W3：写 group_id 属性前必须物理化）
        self.physical = to_physical_group_id(logical_group_id)
        #: Graphiti 侧格式（graphiti_core validator 只收 [A-Za-z0-9_-]）
        self.graphiti_group_id = sanitize_group_id_for_graphiti(logical_group_id)
        #: LanceDB 的表命名空间键（build_vault_group_id 契约：取 vault: 后首段）
        self.lance_vault_id = logical_group_id.split(":", 1)[1].split(":", 1)[0]
        self._uri = uri
        self._lancedb_path = lancedb_path
        self._neo4j: Any = None
        self._driver: Any = None
        self._lance: Any = None

    async def open(self) -> None:
        from graphiti_core.driver.neo4j_driver import Neo4jDriver

        from app.clients.neo4j_client import Neo4jClient
        from lib.agentic_rag.clients.lancedb_client import LanceDBClient

        user = os.environ.get("NEO4J_TEST_USER", "neo4j")
        password = os.environ.get("NEO4J_TEST_PASSWORD", "testpassword")
        self._neo4j = Neo4jClient(uri=self._uri, user=user, password=password, database="neo4j")
        if not await self._neo4j.initialize():
            raise PreconditionRejected(
                f"Neo4jClient 连不上 {self._uri}（测试容器没起来？）",
                rejected_by="g29_dual_vault_canary.VaultScope.open",
                source="backend/scripts/g29_dual_vault_canary.py::VaultScope.open",
            )
        if self._neo4j.is_fallback_mode:
            raise PreconditionRejected(
                "Neo4jClient 进了 JSON fallback 模式 —— 那样测的是内存模拟器，"
                "不是真库隔离，canary 拒绝在这种状态下给出结论。",
                rejected_by="g29_dual_vault_canary.VaultScope.open",
                source="backend/scripts/g29_dual_vault_canary.py::VaultScope.open",
            )
        self._driver = Neo4jDriver(uri=self._uri, user=user, password=password)
        self._lance = LanceDBClient(
            db_path=self._lancedb_path,
            vault_id=self.lance_vault_id,
            embedding_dim=CANARY_VECTOR_DIM,
        )
        await self._lance.initialize()

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
        if self._neo4j is not None:
            await self._neo4j.cleanup()
            self._neo4j = None
        self._lance = None

    @property
    def neo4j(self) -> Neo4jFacet:
        return Neo4jFacet(self._neo4j, self.physical, self.logical)

    @property
    def graphiti(self) -> GraphitiFacet:
        return GraphitiFacet(self._driver, self.graphiti_group_id, self.logical)

    @property
    def lancedb(self) -> LanceDBFacet:
        return LanceDBFacet(self._lance, self.logical)

    def identity(self) -> dict[str, str]:
        return {
            "logical_group_id": self.logical,
            "neo4j_physical_group_id": self.physical,
            "graphiti_group_id": self.graphiti_group_id,
            "lancedb_vault_id": self.lance_vault_id,
            "lancedb_table": self.lancedb.table_name,
        }


# ═══════════════════════════════════════════════════════════════════════════
# canary 主流程
# ═══════════════════════════════════════════════════════════════════════════


async def _purge(scope: VaultScope) -> dict[str, int]:
    """幂等清理本 scope 的三存储痕迹（跑前跑后各一次）。返回各面实删条数。

    ⛔ **删除顺序是契约，不是风格**（Codex round-1 HIGH-1，2026-09-05 实测确认）：
    ``Neo4jFacet.delete`` 的 ``MATCH (n) WHERE n.group_id = $g DETACH DELETE n``
    **没有 label 限制**，而 graphiti 的 group_id 与业务物理 group_id 在本卡的
    命名下**逐字相同**（都是 ``vault__g29canary_a``）。初版把业务删除排在前面，
    于是那一刀顺带清掉了 Episodic/Entity —— 后跑的 ``GraphitiFacet.delete``
    **无对象可删**，它的承重从未被证明，而报告却写着"三存储各自删除后 A=0"。
    实测：只写 graphiti 节点、单跑那条 Cypher，episodic/entity 双双归零。

    现在 graphiti 与 lancedb **先**删（各自返回实删条数，由
    ``graphiti_delete_is_load_bearing`` 判据要求删 A 那次 > 0），业务节点最后删。
    """
    with scope_session(scope.logical):
        graphiti_deleted = await scope.graphiti.delete(scope.graphiti_group_id)
        # ⛔ 取证必须在业务扫荡**之前**：那条 DETACH DELETE 没有 label 限制，
        #    会把 graphiti 漏删的节点一并清走，事后再查恒为 0（HIGH-1 的真身）。
        graphiti_residual = await scope.graphiti.residual(scope.graphiti_group_id)
        lancedb_deleted = scope.lancedb.delete(scope.lance_vault_id)
        lancedb_residual = scope.lancedb.residual()
        await scope.neo4j.delete(scope.physical)
        if _MUTATION == "M11_purge_leaves_residue" and scope.logical == VAULT_A:
            # 验伪：清理跑完却留下了残渣 —— `purge_left_nothing` 是整份报告的
            # **起点前提**（"这些计数是本轮写进去的，不是上轮的遗留"）。它是
            # 唯一一条不靠隔离机制、只靠清理彻底性的判据，所以要单独有变异打它。
            await scope.neo4j.write()
    return {
        "graphiti_deleted": graphiti_deleted,
        "graphiti_residual_before_sweep": graphiti_residual,
        "lancedb_drop_attempted": lancedb_deleted,
        "lancedb_residual": lancedb_residual,
    }


#: 每个存储面的**完整**键集。形状断言按它逐一核对 —— 见 :func:`_assert_shape`。
FACET_KINDS: dict[str, tuple[str, ...]] = {
    "neo4j": Neo4jFacet.KINDS,
    "graphiti": GraphitiFacet.KINDS,
    "lancedb": LanceDBFacet.KINDS,
}
#: 写入后**应当为正**的键（资产计数）。
FACET_POSITIVE_KINDS: dict[str, tuple[str, ...]] = {
    "neo4j": Neo4jFacet.KINDS,
    "graphiti": ("episodic", "entity"),
    "lancedb": ("rows", "table_exists"),
}
#: **恒应为 0** 的验伪锚（不参与"计数为正"的判定，但单独立一条判据）。
FACET_SENTINEL_KINDS: dict[str, tuple[str, ...]] = {
    "neo4j": (),
    "graphiti": ("outside_read_scope",),
    "lancedb": (),
}


def _assert_shape(counts: dict[str, dict[str, int]], where: str) -> None:
    """键集必须完整。

    ⛔ 这不是防御性编程，是**堵一个实测到的假绿面**：Cypher 的分组聚合在空输入
    下返回 0 行 ⇒ 计数 dict 为空 ⇒ ``_all_positive({})`` 与 ``_all_zero({})``
    **同时为 True**，"A 写入成功"和"A 已被清空"会一起假通过。2026-09-05 首跑
    实测复现（删 A 之后 neo4j 面就是 ``{}``）。修在 facet 里补 0，这里再钉一道
    形状门，防以后有人加了新计数键却忘了补齐。
    """
    for facet, kinds in FACET_KINDS.items():
        got = counts.get(facet)
        if got is None:
            raise IsolationFailed(f"{where}: 计数缺少 {facet!r} 面")
        if set(got) != set(kinds):
            raise IsolationFailed(
                f"{where}: {facet!r} 面的键集是 {sorted(got)}，期望 {sorted(kinds)}。"
                "空键集会让 all() 恒真 —— 判据必须在完整形状上评估。"
            )


async def _write_and_count(scope: VaultScope) -> dict[str, dict[str, int]]:
    """在**独占** scope 会话里写完再读完，然后交出 scope。"""
    with scope_session(scope.logical):
        await scope.neo4j.write()
        await scope.graphiti.write()
        await scope.lancedb.write()
    return await _count_own(scope)


async def _count_own(scope: VaultScope) -> dict[str, dict[str, int]]:
    """在本 scope 的读作用域下数本 scope 的资产。"""
    with scope_session(scope.logical):
        counts = {
            "neo4j": await scope.neo4j.count(scope.physical),
            "graphiti": await scope.graphiti.count(scope.graphiti_group_id),
            "lancedb": scope.lancedb.count(LANCE_TABLE),
        }
    _assert_shape(counts, f"count_own({scope.logical})")
    return counts


async def _count_cross(scope: VaultScope, other: VaultScope) -> dict[str, dict[str, int]]:
    """交叉查询（判据 2）：以 ``scope`` 的作用域去够 ``other`` 的数据。

    三个存储各有各的"够不着"的形状，不能用同一句话糊过去：

    * **Neo4j** —— 生产读侧的 scope 过滤（``read_group_filter``）**叠加**
      "归属为 other" 的条件。隔离成立时恒 0；若 scope 过滤退化成会吃掉兄弟组
      的前缀，它立刻变 1。
    * **Graphiti** —— 用 scope 自己的 group 去 ``get_by_group_ids``，数其中
      归属为 other 的条数（再加 ``outside_read_scope`` 验伪锚）。
    * **LanceDB** —— 把 other 的**物理表名**当逻辑表名塞给 scope 的 client，
      让生产的 ``resolve_table_name`` 去解析。隔离成立时它被再前缀化成一张
      不存在的表 ⇒ 0 行。
    """
    with scope_session(scope.logical):
        counts = {
            "neo4j": await scope.neo4j.count(scope.physical, only_group=other.physical),
            "graphiti": await scope.graphiti.count(scope.graphiti_group_id, only_group=other.graphiti_group_id),
            "lancedb": scope.lancedb.count(other.lancedb.table_name),
        }
    _assert_shape(counts, f"count_cross({scope.logical} → {other.logical})")
    return counts


def _all_positive(counts: dict[str, dict[str, int]]) -> bool:
    """资产键全为正（验伪锚键不参与——它们本就该是 0）。"""
    return all(counts[facet][k] > 0 for facet, kinds in FACET_POSITIVE_KINDS.items() for k in kinds)


def _all_zero(counts: dict[str, dict[str, int]]) -> bool:
    return all(v == 0 for facet in counts.values() for v in facet.values())


def _sentinels_clean(counts: dict[str, dict[str, int]]) -> bool:
    """验伪锚恒 0（graphiti 交回来的东西必须全在本作用域可见面内）。"""
    return all(counts[facet][k] == 0 for facet, kinds in FACET_SENTINEL_KINDS.items() for k in kinds)


async def run_canary(uri: str, lancedb_path: str) -> dict[str, Any]:
    """跑一遍完整 canary，返回报告 dict。判据不成立即抛 :class:`IsolationFailed`。"""
    a = VaultScope(VAULT_A, uri, lancedb_path)
    b = VaultScope(VAULT_B, uri, lancedb_path)
    report: dict[str, Any] = {"identities": {}, "phases": {}, "verdicts": {}}
    await a.open()
    await b.open()
    try:
        report["identities"] = {"A": a.identity(), "B": b.identity()}

        phases = report["phases"]

        # ── 起点干净（幂等）──
        await _purge(a)
        await _purge(b)
        phases["after_purge_A"] = await _count_own(a)
        phases["after_purge_B"] = await _count_own(b)

        # ── (a) 顺序切换：A 全程 → 再 B 全程 ──
        phases["A_written"] = await _write_and_count(a)
        # A 已写、B **还没写**时的 A 计数。下面 `A_unaffected_by_B` 就靠它 ——
        # "看不见对方"最直接的证据是"对方写入前后我的数字一样"。
        a_before_b = phases["A_written"]
        phases["B_written"] = await _write_and_count(b)

        # ── (b) 交叉 0 命中 ──
        phases["A_sees_B"] = await _count_cross(a, b)
        phases["B_sees_A"] = await _count_cross(b, a)
        # B 写入之后再数一次 A：数字必须与 B 写入之前逐字相同
        phases["A_after_B_written"] = await _count_own(a)

        # ── 同名资产在库里被拆成了几个物理节点（W1 复合键的直接证据）──
        with scope_session(a.logical):
            phases["concept_group_distribution"] = await a.neo4j.group_distribution()

        # ── (b) 删 A 之前先记 B 的计数（删后拿"现在的 B"跟"现在的 B"比 = 自证）──
        b_before_delete = await _count_own(b)
        phases["B_before_deleting_A"] = b_before_delete

        deleted_a = await _purge(a)
        phases["deleted_when_purging_A"] = deleted_a
        phases["A_after_delete"] = await _count_own(a)
        b_after_delete = await _count_own(b)
        phases["B_after_deleting_A"] = b_after_delete

        # ── 判据 ──
        ca = phases["A_written"]
        cb = phases["B_written"]
        verdicts = report["verdicts"]
        verdicts["purge_left_nothing"] = _all_zero(phases["after_purge_A"]) and _all_zero(phases["after_purge_B"])
        verdicts["A_counts_positive"] = _all_positive(ca)
        verdicts["B_counts_positive"] = _all_positive(cb)
        verdicts["A_equals_B"] = ca == cb
        verdicts["A_cannot_see_B"] = _all_zero(phases["A_sees_B"])
        verdicts["B_cannot_see_A"] = _all_zero(phases["B_sees_A"])
        verdicts["A_unaffected_by_B_write"] = phases["A_after_B_written"] == a_before_b
        verdicts["read_scope_sentinels_clean"] = (
            _sentinels_clean(ca) and _sentinels_clean(cb) and _sentinels_clean(phases["A_after_B_written"])
        )
        # ⛔ A/B 的身份必须两两不同 —— 这是**前置不变量**，不是"结果"。
        #    没有它，任何"A==B"型缺陷都会让下面的期望值跟着一起退化：
        #    `{a.physical: 1, b.physical: 1}` 在 a.physical == b.physical 时
        #    字面折叠成单键，实际分布也是单键 ⇒ 判据假 PASS。期望值绝不能与
        #    被测量同源（变异 M1 就是照着这一点写的）。
        ids_a, ids_b = a.identity(), b.identity()
        verdicts["identities_distinct"] = all(ids_a[k] != ids_b[k] for k in ids_a)
        dist = phases["concept_group_distribution"]
        verdicts["shared_concept_split_per_group"] = (
            len(dist) == 2 and set(dist.values()) == {1} and set(dist) == {a.physical, b.physical}
        )
        verdicts["A_gone_after_delete"] = _all_zero(phases["A_after_delete"])
        # ⛔ Codex round-1 HIGH-1：初版把业务节点删除排在 graphiti 之前，而业务删除的
        #    `MATCH (n) WHERE n.group_id = $g` 没有 label 限制、graphiti 与业务的
        #    group_id 又逐字相同 ⇒ 那一刀顺带清掉了 Episodic/Entity，后跑的
        #    GraphitiFacet.delete **无对象可删**，承重从未被证明，而报告却写着
        #    "三存储各自删除后 A=0"。现在 graphiti 先删并交出实删条数，这条判据
        #    要求删 A 那次它 > 0 —— 「删干净了」与「本来就没东西」必须能分开。
        # 「删干净了」与「本来就没东西可删」与「调了但没删掉」是**三**种情况，
        # 判据必须能把它们分开：前者要 deleted > 0（确有对象），后者要
        # residual == 0（且这个 0 是在业务扫荡之前测的，不是被扫荡做掉的）。
        verdicts["graphiti_delete_is_load_bearing"] = (
            deleted_a["graphiti_deleted"] > 0 and deleted_a["graphiti_residual_before_sweep"] == 0
        )
        verdicts["lancedb_delete_is_load_bearing"] = (
            deleted_a["lancedb_drop_attempted"] > 0 and deleted_a["lancedb_residual"] == 0
        )
        verdicts["B_unchanged_after_deleting_A"] = b_after_delete == b_before_delete

        failed = [k for k, v in verdicts.items() if not v]
        if failed:
            raise IsolationFailed(
                "隔离判据不成立：" + ", ".join(failed) + f"\n{json.dumps(report, ensure_ascii=False, indent=2)}",
                report=report,
            )
    except IsolationFailed as exc:
        # 形状门等更早的断言抛出时 report 还没挂上 —— 验伪模式要读它
        if not exc.report:
            exc.report = report
        raise
    finally:
        # 收尾 purge：canary 不在测试库里留渣（第二次跑才能拿到相同报告）
        try:
            await _purge(a)
            await _purge(b)
        finally:
            await a.close()
            await b.close()
    return report


def audit_judge_coverage(verdicts: dict[str, Any]) -> dict[str, Any]:
    """判据覆盖自检：每条 verdict 是否**至少被一条变异点名**。

    ⛔ round-2 复核指出：验收单写着"脚本自带覆盖自检"，而脚本里根本没有这段代码——
    13/13 是我在 shell 里手算的。手算的数字不会随代码演进自动失效：以后有人加了
    一条判据却忘了配变异，没有任何东西会报警。所以把它变成脚本里的门。

    返回 ``{covered, uncovered, total, complete}``；``complete`` 为 False 时
    ``--verify-judges`` 以非 0 退出。
    """
    named: set[str] = set()
    for spec in MUTATION_SPECS.values():
        named.update(spec.get("expect_red", ()))
    all_names = set(verdicts)
    uncovered = sorted(all_names - named)
    # 反向也要查：点名了一个**不存在**的判据 = 变异写错了名字，静默失效
    phantom = sorted(named - all_names)
    return {
        "total": len(all_names),
        "covered": len(all_names) - len(uncovered),
        "uncovered": uncovered,
        "phantom_targets": phantom,
        "complete": not uncovered and not phantom,
    }


async def verify_judges(uri: str, lancedb_path: str) -> dict[str, Any]:
    """逐条注入变异，要求**指定的那条判据**当场翻红。

    判定不是"有判据红了"（那太松：M3 会顺带让别的判据也红），而是
    「``expect_red`` 里点名的每一条都红」。目标判据仍绿 = SURVIVED。

    每条变异先自证**生效**：把变异后的报告与基线逐字比对，**完全相同**即
    判 NOT_APPLIED —— 否则"没红"分不清是门够硬还是变异压根没打进去
    （这正是历史上多次把假 SURVIVED 当结论的原因）。
    """
    global _MUTATION

    async def _run() -> tuple[dict[str, Any], str | None]:
        try:
            return await run_canary(uri, lancedb_path), None
        except IsolationFailed as exc:
            return exc.report, str(exc)

    baseline, baseline_err = await _run()
    if baseline_err is not None:
        raise IsolationFailed(f"验伪需要一个干净的基线，但未变异的 canary 就已经红了：{baseline_err}")
    baseline_norm = normalize(baseline)

    results: list[dict[str, Any]] = []
    for name, spec in MUTATION_SPECS.items():
        _MUTATION = name
        try:
            report, err = await _run()
        finally:
            _MUTATION = None
            # 变异版的 purge 可能没删干净，用正常模式再清一遍，防污染下一条
            for logical in (VAULT_A, VAULT_B):
                scope = VaultScope(logical, uri, lancedb_path)
                await scope.open()
                try:
                    await _purge(scope)
                finally:
                    await scope.close()

        verdicts = report.get("verdicts", {})
        applied = normalize(report) != baseline_norm or err is not None
        if "expect_raises" in spec:
            killed = err is not None and spec["expect_raises"] in err
            target_state = {"raised": err is not None}
        else:
            targets = spec["expect_red"]
            missing = [k for k in targets if k not in verdicts]
            killed = not missing and all(verdicts[k] is False for k in targets)
            target_state = {k: verdicts.get(k, "<未产出>") for k in targets}
        results.append(
            {
                "mutation": name,
                "what": spec["what"],
                "breaks": spec.get("breaks", ""),
                "applied": applied,
                "verdict": "KILLED" if killed else ("SURVIVED" if applied else "NOT_APPLIED"),
                "target_judges": target_state,
            }
        )

    survived = [r for r in results if r["verdict"] != "KILLED"]
    coverage = audit_judge_coverage(baseline["verdicts"])
    return {
        "baseline_verdicts": baseline["verdicts"],
        "mutations": results,
        "all_killed": not survived,
        "coverage": coverage,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 附带发现：LanceDB 跨 vault 的 schema-drift 连带删表
#
# ⚠️ 这一段**不是**主线判据，是 canary 端到端跑出来的**发现**，登记移交、
#    本卡不修（硬边界禁改 lancedb_client.py）。
#
#    ``_cache_tables`` (:962-968) 对 ``db.table_names()`` 的**全部**表跑
#    ``_check_and_fix_dimension_mismatch``，而那个集合含**别的 vault 前缀**
#    的表。于是 vault A 的 ``initialize()`` 会 drop 掉 schema 与 A 的期望
#    不符的 **vault B 的表** —— 一个 vault 的进程能删掉另一个 vault 的数据。
#    单点表名前缀单测照不出这条：它证的是"写去哪张表"，不是"初始化会碰谁的表"。
# ═══════════════════════════════════════════════════════════════════════════


async def probe_schema_drift_side_effect(base_tmp: str) -> dict[str, Any]:
    """实测 A 的 initialize 是否会连带删掉 B 的表。返回观察结果（不做判据）。"""
    from lib.agentic_rag.clients.lancedb_client import LanceDBClient

    tmp = str(pathlib.Path(base_tmp) / "drift-probe")
    pathlib.Path(tmp).mkdir(parents=True, exist_ok=True)
    vid_a, vid_b = "g29drift_a", "g29drift_b"

    # B 先建表，向量维度 16（与 A 期望的 8 不同 = schema drift）
    cb = LanceDBClient(db_path=tmp, vault_id=vid_b, embedding_dim=16)
    await cb.initialize()
    await cb.add_documents(
        LANCE_TABLE,
        [{"doc_id": "b-1", "content": "B 的数据", "vector": [0.2] * 16, "doc_type": "canvas_node"}],
    )
    db_b = cb._db
    assert db_b is not None, "LanceDB 未连上 tmp 目录"
    before = sorted(db_b.table_names())

    # A 用 8 维初始化 —— 它会遍历**全部**表（含 B 的）跑维度检查
    ca = LanceDBClient(db_path=tmp, vault_id=vid_a, embedding_dim=CANARY_VECTOR_DIM)
    await ca.initialize()
    db_a = ca._db
    assert db_a is not None, "LanceDB 未连上 tmp 目录"
    after = sorted(db_a.table_names())

    b_table = f"{vid_b}_{LANCE_TABLE}"
    return {
        "tables_before_A_init": before,
        "tables_after_A_init": after,
        "B_table": b_table,
        "B_table_survived_A_init": b_table in after,
        "finding": (
            "CONFIRMED: vault A 的 LanceDBClient.initialize() 删掉了 vault B 的表"
            if b_table in before and b_table not in after
            else "NOT REPRODUCED（本次未观察到连带删表）"
        ),
        "source": "backend/lib/agentic_rag/clients/lancedb_client.py:962-968 "
        "(_cache_tables 对 db.table_names() 全表跑 _check_and_fix_dimension_mismatch)",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 报告
# ═══════════════════════════════════════════════════════════════════════════

#: normalized 报告要剥掉的 volatile 键（(a) 的「剥掉时间戳后 diff 为空」）。
#: ⛔ 只剥这些 —— 全部**计数、group_id、表名、判据布尔值**都保留，否则
#:    normalized 会变成一个剥到没有实质内容的空壳，diff 恒空 = 假判据。
_VOLATILE_KEYS = frozenset(
    {"timestamp", "duration_s", "lancedb_path", "evidence_dir", "guard_summary", "python", "argv"}
)


def normalize(report: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in report.items() if k not in _VOLATILE_KEYS}


def _write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _print_count_table(report: dict[str, Any]) -> None:
    print("\n── 三存储 A/B 计数表 ──")
    phases = report["phases"]
    for facet in ("neo4j", "graphiti", "lancedb"):
        print(f"  [{facet}]")
        for phase in (
            "after_purge_A",
            "after_purge_B",
            "A_written",
            "B_written",
            "A_after_B_written",
            "A_sees_B",
            "B_sees_A",
            "B_before_deleting_A",
            "A_after_delete",
            "B_after_deleting_A",
        ):
            print(f"    {phase:<22} {phases[phase][facet]}")
    print(f"\n  同名 Concept 的 group 分布: {phases['concept_group_distribution']}")
    print(f"  删 A 时的删除取证: {phases['deleted_when_purging_A']}")
    print("    （deleted=确有对象可删；residual=删完当场复查，取在业务扫荡之前）")
    print("\n── 判据 ──")
    for k, v in report["verdicts"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")


def _report_rejection(exc: PreconditionRejected, where: str, evidence: pathlib.Path, ts: str) -> int:
    """统一的拒绝出口，preflight 与运行期共用。

    ⛔ round-2 复核实测：`VaultScope.open()` 也会抛 :class:`PreconditionRejected`
    （连不上测试库 / 掉进 JSON fallback 模拟器），而初版只在 preflight 外面接了
    一层 ⇒ 那两条路径会**裸 traceback 逃出**、以 **rc=1** 结束、不打横幅、不落账本。
    而 rc=1 在本脚本文档里的含义是「隔离判据失败」—— 于是一个**配置问题**会被
    误报成**隔离失败**。这正是"判据必须绑定被哪一层拒的"要防的事，只不过这次
    错归因发生在退出码这一层。

    账本文件名带 pid：同一秒内的多次拒绝原本会互相覆盖（实测 7 条负控只落
    5 份账本）。
    """
    print(f"*** G2-9 CANARY REJECTED ({where}) ***", file=sys.stderr)
    print(f"NEGCTL_REJECTED_BY={exc.rejected_by}", file=sys.stderr)
    print(f"NEGCTL_REJECTED_SOURCE={exc.source}", file=sys.stderr)
    print(f"NEGCTL_REASON={exc}", file=sys.stderr)
    print(live_port_guard.STATE.summary_line())
    live_port_guard.write_ledger(str(evidence / f"ledger-negctl-{ts}-{os.getpid()}.json"))
    return EXIT_PRECONDITION_REJECTED


async def _amain(args: argparse.Namespace) -> int:
    evidence = pathlib.Path(args.evidence_dir).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stage = "preflight"
    try:
        uri = _preflight_neo4j_uri()
        lancedb_path = _preflight_lancedb_path(args.lancedb_path, allow_outside_tmp=args.allow_path_outside_tmp)
        os.environ["LANCEDB_DATA_PATH"] = lancedb_path
        stage = "runtime"
        return await _run_canary_cli(args, evidence, ts, uri, lancedb_path)
    except PreconditionRejected as exc:
        return _report_rejection(exc, stage, evidence, ts)


async def _run_canary_cli(
    args: argparse.Namespace,
    evidence: pathlib.Path,
    ts: str,
    uri: str,
    lancedb_path: str,
) -> int:
    started = time.monotonic()

    if args.verify_judges:
        vr = await verify_judges(uri, lancedb_path)
        vr["timestamp"] = ts
        _write_json(evidence / f"canary-verify-judges-{ts}.json", vr)
        print("\n── 验伪：每条判据必须被证明能翻红 ──")
        for r in vr["mutations"]:
            print(f"  {r['verdict']:<11} {r['mutation']}  ({r['breaks']})")
            print(f"              {r['what']}")
            print(f"              目标判据: {r['target_judges']}")
        cov = vr["coverage"]
        print(f"\n── 判据覆盖自检 ──\n  {cov['covered']}/{cov['total']} 条判据被变异点名")
        if cov["uncovered"]:
            print(f"  ⛔ 未被任何变异点名: {cov['uncovered']}")
        if cov["phantom_targets"]:
            print(f"  ⛔ 变异点名了不存在的判据（名字写错会静默失效）: {cov['phantom_targets']}")
        print(f"\n验伪报告: {evidence / f'canary-verify-judges-{ts}.json'}")
        live_port_guard.write_ledger(str(evidence / f"ledger-verify-{ts}.json"))
        print(live_port_guard.STATE.summary_line())
        if not vr["all_killed"]:
            print(
                "*** 有变异未被目标判据杀死 —— 那条判据此刻不承重 ***",
                file=sys.stderr,
            )
            return EXIT_ISOLATION_FAILED
        if not vr["coverage"]["complete"]:
            print(
                "*** 判据覆盖不全 —— 有判据没有任何变异证明过它能翻红 ***",
                file=sys.stderr,
            )
            return EXIT_ISOLATION_FAILED
        return EXIT_OK

    report = await run_canary(uri, lancedb_path)

    if args.probe_schema_drift:
        report["side_effect_probe"] = await probe_schema_drift_side_effect(lancedb_path)

    report["timestamp"] = ts
    report["duration_s"] = round(time.monotonic() - started, 3)
    report["lancedb_path"] = lancedb_path
    report["evidence_dir"] = str(evidence)
    report["guard_summary"] = live_port_guard.STATE.summary_line()

    _write_json(evidence / f"canary-report-{ts}.json", report)
    _write_json(evidence / f"canary-normalized-{ts}.json", normalize(report))

    _print_count_table(report)
    if "side_effect_probe" in report:
        p = report["side_effect_probe"]
        print("\n── 附带发现（登记移交，本卡不修）──")
        print(f"  {p['finding']}")
        print(f"  来源: {p['source']}")
    print(f"\n报告: {evidence / f'canary-report-{ts}.json'}")
    print(f"规范化报告(可 diff): {evidence / f'canary-normalized-{ts}.json'}")

    live_port_guard.write_ledger(str(evidence / f"ledger-{ts}.json"))
    print(live_port_guard.STATE.summary_line())
    return EXIT_OK


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-dir", required=True, help="报告 / 账本落盘目录")
    ap.add_argument(
        "--lancedb-path",
        default=None,
        help="LanceDB tmp 目录（不传则读 LANCEDB_DATA_PATH；两者皆空即拒绝）",
    )
    ap.add_argument(
        "--no-probe-schema-drift",
        dest="probe_schema_drift",
        action="store_false",
        help="跳过 LanceDB 跨 vault schema-drift 连带删表的附带探测",
    )
    ap.add_argument(
        "--allow-path-outside-tmp",
        action="store_true",
        help="显式逃生阀：允许 LanceDB 路径落在临时目录之外（现网 data/lancedb 仍拒）",
    )
    ap.add_argument(
        "--verify-judges",
        action="store_true",
        help="验伪模式：逐条注入已知会破坏隔离的变异，要求指定判据当场翻红",
    )
    ap.set_defaults(probe_schema_drift=True)
    args = ap.parse_args()
    try:
        rc = asyncio.run(_amain(args))
    except IsolationFailed as exc:
        print(f"*** G2-9 ISOLATION FAILED ***\n{exc}", file=sys.stderr)
        print(live_port_guard.STATE.summary_line())
        rc = EXIT_ISOLATION_FAILED
    sys.exit(rc)


if __name__ == "__main__":
    main()
