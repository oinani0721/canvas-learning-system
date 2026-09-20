# Canvas Learning System - Edge Rationale API Endpoints
# Story 4.2: Edge Dialog — Agent Follow-up & Rationale Recording (AC-6)
# Story 4.3: EI+SE Dual Strategy (AC-6 strategy data)
# Story 4.4: Edge Dialog Fallback (AC-3, AC-4 partial failure handling)
"""
Edge rationale recording endpoint.

Exposes record_edge_rationale as a FastAPI endpoint (MCP tool target).
Performs dual-write to Neo4j (structured KG-triplet) and LanceDB (vector).
Supports partial failure semantics (207 Multi-Status).

[Source: _bmad-output/implementation-artifacts/4-2-edge-dialog-agent-reasoning.md#Task 2]
[Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 6]
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# CARD-T-EDGES: 判定「对端写失败」用. ⛔ 必须是**模块级** import ——
# except 子句是发生异常时才求值的, 名字未绑定会先抛 NameError 把处理器自己炸掉
# (memory_service.py:44-50 记的就是这起事故)。同包先例: sync.py:16。
from neo4j.exceptions import DatabaseError, ServiceUnavailable, SessionExpired, TransientError
from tenacity import RetryError

# CARD-LANCE-DUALWRITE-NEVER-WRITES (第十五批 P1-A): 握手完成后收到畸形 Bolt 帧时驱动抛
# `neo4j._exceptions.BoltError` 族。它**不是** Neo4jError / DriverError 的子类
# (6.1.0 实测 issubclass 为 False), 所以公共异常元组永远接不住, 会逃出本模块的
# `_NEO4J_WRITE_FAILURES` 而 500。驱动自己的连接池写的就是
# `except (Neo4jError, DriverError, BoltError)` —— 我们跟它同口径。
# ⛔ 私有模块 ⇒ 守卫式导入: 驱动版本漂移把它挪走时, 行为退回「收不进元组」(与本卡改前
# 一致), 而不是整个端点 import 失败。版本漂移由 t5b 门 1c 的 BoltError 格钉住。
try:
    from neo4j._exceptions import BoltError as _BoltError
except ImportError:  # pragma: no cover — 仅驱动版本漂移时走到
    _BoltError = None

#: 展开进 `_NEO4J_WRITE_FAILURES` 的 Bolt 协议层故障类型 (导不到 = 空元组)。
_BOLT_PROTOCOL_FAILURES: tuple[type[Exception], ...] = () if _BoltError is None else (_BoltError,)

if TYPE_CHECKING:  # pragma: no cover — 仅供解析器; 运行期由函数内 import 取真类
    from agentic_rag.clients.lancedb_client import LanceDBClient

from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号)
from app.graphiti.group_id_compat import to_physical_group_id
from app.models.edge_rationale import (
    EdgeRationaleCreate,
    EdgeRationaleResponse,
    WriteStatus,
)

logger = logging.getLogger(__name__)

#: `_write_neo4j_triplet` 判定为「**对端**写失败」的类型集 —— 命中即记
#: `WriteStatus(success=False)`, 由 handler 按 Story 4.4 AC-4 判半成功 207,
#: 保住 LanceDB 侧那一半; 未命中的一律原样上抛成 500。
#:
#: ⛔ **刻意不收 `Neo4jError` / `ClientError` 族**(第十四批 T5-B 对抗复核裁定)。
#: `ClientError` 的语义是「**你发来的请求不对**」: `ParameterMissing`(params 少一个键)、
#: `CypherSyntaxError`(Cypher 写错)、`AuthError`/`Forbidden`(凭据或权限没配对)、
#: `ConstraintError`。这些全是**本进程 / 本部署的缺陷**, 收进 207 的后果是:
#: 每个请求都返 207 → 5xx 率恒 0 → 看板全绿 → 前端 Outbox 把 207 当「部分成功已保留」
#: 继续投递 → 全部 edge rationale 的 Neo4j 半边永久丢失且无人察觉。
#: 同理不收 `ConnectionPoolError`、`ResultError`/`SessionError`/`TransactionError` 族、
#: `ConfigurationError` 族 —— 它们都该响亮地 500。
#:
#: 收进来的这四类的共同点是**不指向某一次请求的内容**:
#: ServiceUnavailable/SessionExpired(连不上或会话失效)、TransientError(对端让重试)、
#: DatabaseError(对端内部错)。加上 tenacity `RetryError`(重试耗尽, 在已 fallback 态
#: 由 neo4j_client 裸 raise)与原有四类内建异常。
#:
#: ⚠️ **这是 207/500 的处置策略, 不是根因分类器**(Codex r6 L1 整改, 原措辞过绝对):
#: 同一个类可以有多种根因 —— `ConnectionAcquisitionTimeoutError`(⊂ ConnectionPoolError)
#: 既可能来自我方 session 泄漏, 也可能只是正常慢查询占满了连接池; 官方也写明
#: `ServiceUnavailable` 可能源于配置错误。所以「收/不收」表达的是「这一类**默认**按
#: 对端故障还是按我方缺陷处置」, 不能反过来当成「出现这个类就一定是谁的锅」。
#: `ConnectionAcquisitionTimeoutError` 是这条线上最值得重新裁定的一类, 现按 500 处置。
#:
#: ⚠️ 已知未覆盖(如实记, 已登记移交):
#: 1. packstream 解码层的裸 `ValueError` / `struct.error` —— 握手完成后收到畸形 Bolt 帧
#:    时**仍**会逃出本元组而 500。⛔ 刻意不收: 这两个类与 pydantic 校验、我方 params
#:    组装抛出的同名异常**不可分辨**, 收进来等于把本进程缺陷一并降级成 207。
#:    ✅ `neo4j._exceptions.BoltError` 族已由 CARD-LANCE-DUALWRITE-NEVER-WRITES
#:    (第十五批 P1-A) 收进本元组(见文件顶部的守卫式导入与 `_BOLT_PROTOCOL_FAILURES`):
#:    它表达的是**对端协议层故障**, 与 ServiceUnavailable 同族 → 207。
#: 2. ⛔ **保证的准确形态(Codex r7 H1 给的表述)**: 「``run_query`` 原样抛出、且不被
#:    本元组捕获的异常」才会上抛成 500; **初始化阶段被 client 吞掉的异常不受该保证
#:    覆盖**。别把「驱动已初始化之后」读成充分保证。展开:
#:    ✅ **已收窄** (CARD-LANCE-DUALWRITE-NEVER-WRITES / 第十五批 P1-A):
#:    `Neo4jClient` 的初始化现在对 `AuthError` / `ConfigurationError`(部署缺陷)
#:    **fail-closed 上抛**, 于是「密码配错」这条路上异常会穿过 `run_query` 的 lazy
#:    初始化到达本函数 —— 而这两类都**不在**本元组里 ⇒ 原样上抛成 **500**(响亮)。
#:    ⚠️ 仍然成立的边界: 「对端不可达」(ServiceUnavailable / SessionExpired / 其余
#:    DriverError)在初始化阶段照旧转 JSON fallback, 那条路上后续查询返回 `[]`, 由下面
#:    的写确认判据兜成 207 —— 给出的是「写未确认」而不是「部署坏了」的信号, 这是有意的。
_NEO4J_WRITE_FAILURES: tuple[type[Exception], ...] = (
    RuntimeError,  # neo4j_client.py:595-596 "Neo4j driver not initialized"
    ConnectionError,  # ⊂ OSError, 保留为可读性
    asyncio.TimeoutError,  # 实测 is TimeoutError 且 ⊂ OSError, 同上
    OSError,  # JSON fallback 侧的文件 IO
    AttributeError,  # 客户端缺方法(本卡原缺陷 execute_query 的那一类)
    ServiceUnavailable,  # 对端不可达
    SessionExpired,  # 对端会话失效
    TransientError,  # 对端让重试
    DatabaseError,  # 对端内部错误
    RetryError,  # tenacity 重试耗尽(已 fallback 态下裸 raise)
) + _BOLT_PROTOCOL_FAILURES  # 对端 Bolt 协议层故障(私有模块, 导不到则为空)

edges_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Neo4j Write — Structured KG-Triplet
# ═══════════════════════════════════════════════════════════════════════════════


async def _write_neo4j_triplet(
    rationale: EdgeRationaleCreate,
    record_id: str,
    resolved_group_id: str,
) -> WriteStatus:
    """
    Write edge rationale to Neo4j as structured KG-triplet.

    Story 4.2 AC-3: Uses Agent self-report channel.
    Writes via Neo4j client directly as an :EdgeRationale node,
    following the existing Neo4j direct-write pattern.

    Story 4.2 AC-5: Time-series aware — new rationale creates new node,
    does not overwrite old (append-only for version history).

    Wave-5 Stage B 续: resolved_group_id 由 endpoint 顶部 resolve_vault_group_id 派生,
    确保 Neo4j 写入用 per-vault group_id 防多 vault 串库.
    """
    from app.clients.neo4j_client import get_neo4j_client

    neo4j = get_neo4j_client()
    # ⛔ **防御性守卫** (CARD-LANCE-DUALWRITE-NEVER-WRITES):
    # `get_neo4j_client` 函数体里 `return None` 计数 = 0, 唯一的返回语句是
    # `return _client_instance`, 且返回注解是非 Optional 的 `Neo4jClient`。
    # ⚠️ 措辞边界(Codex r1/r3/r4 LOW 连续三轮): 这两条**只是线索, 不构成「生产不可达」的
    # 证明** —— 注解不是运行期约束, 计数也只覆盖当前实现。所以这里写「防御性」,
    # 不写「死守卫」「不可达」。
    # ⛔ 仍然**保留**, 但理由要说准(Codex r1 LOW 整改, 原措辞过强):
    # 删掉它**不会**让端点崩 —— `None.run_query` 抛的 AttributeError 正在
    # `_NEO4J_WRITE_FAILURES` 里, 照样被接住记成写失败 ⇒ 仍是 207。真正变掉的是
    # **错误文案**: 从可读的「Neo4j client not available」变成一句
    # `'NoneType' object has no attribute 'run_query'`, 运维据此分不清「客户端没造出来」
    # 与「客户端方法漂移」。守卫锁的是这条可分辨性, 语义由 t5b 的
    # `test_neo4j_客户端为_None_时端点给出可分辨的错误文案` 钉住(它断言的正是那句文案)。
    if neo4j is None:
        return WriteStatus(
            success=False,
            error="Neo4j client not available",
        )

    # Build structured episode body
    episode_body = (
        f"Edge rationale: "
        f"{rationale.source_concept} --[{rationale.relation_type}]--> "
        f"{rationale.target_concept}. "
        f"Rationale: {rationale.rationale_text} "
        f"(confidence: {rationale.confidence:.2f}, "
        f"strategies: {','.join(rationale.strategies_applied)}, "
        f"depth: {rationale.explanation_depth_score}/5, "
        f"rounds: {rationale.questioning_rounds})"
    )

    # Write as :EdgeRationale node in Neo4j (time-series append-only)
    query = """
        CREATE (er:EdgeRationale {
            record_id: $record_id,
            edge_id: $edge_id,
            source_node_id: $source_node_id,
            target_node_id: $target_node_id,
            source_concept: $source_concept,
            target_concept: $target_concept,
            relation_type: $relation_type,
            rationale_text: $rationale_text,
            confidence: $confidence,
            strategies_applied: $strategies_applied,
            questioning_rounds: $questioning_rounds,
            explanation_depth_score: $explanation_depth_score,
            episode_body: $episode_body,
            group_id: $group_id,
            created_at: datetime()
        })
        RETURN er.record_id AS record_id
        """

    # CARD-T-EDGES (第十四批): 已改调 run_query(**params) —— Neo4jClient 上只有
    # run_query(query, **params)(neo4j_client.py:536), 从来没有 execute_query,
    # 旧写法每次调用都抛 AttributeError。run_query 收的是 **params 而非位置 dict,
    # 故参数同步展开(键名逐字不变)。
    params = {
        "record_id": record_id,
        "edge_id": rationale.edge_id,
        "source_node_id": rationale.source_node_id,
        "target_node_id": rationale.target_node_id,
        "source_concept": rationale.source_concept,
        "target_concept": rationale.target_concept,
        "relation_type": rationale.relation_type,
        "rationale_text": rationale.rationale_text,
        "confidence": rationale.confidence,
        "strategies_applied": rationale.strategies_applied,
        "questioning_rounds": rationale.questioning_rounds,
        "explanation_depth_score": rationale.explanation_depth_score,
        "episode_body": episode_body,
        # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
        "group_id": to_physical_group_id(resolved_group_id),
    }

    # ⛔ try 只包住**对端调用这一行**(第十四批 T5-B 第二轮收窄)。
    # 之前 try 包整个函数体, 于是 get_neo4j_client() 的配置缺陷、episode_body 的
    # f-string、params 里 14 次 rationale.<field> 取值、to_physical_group_id 的
    # punycode 路径, 任何一处的编程缺陷都会被记成「Neo4j 写失败」⇒ 每个请求静默 207
    # ⇒ 5xx 率恒 0 ⇒ 前端 Outbox 把 207 当「部分成功已保留」继续投递 ⇒ 数据永久丢失
    # 且无人察觉。收窄之后这些缺陷一律原样上抛成 500(响亮), 这也是补进元组的那几类
    # 能保持安全的前提。
    try:
        rows = await neo4j.run_query(query, **params)
    except _NEO4J_WRITE_FAILURES as e:
        # type(e).__name__ 是承重的: ServiceUnavailable(重试有用)与 DatabaseError
        # (对端内部错)在响应体里必须可分辨, 否则运维无法分流。
        logger.error(
            "Neo4j write failed for edge %s: type=%s detail=%s",
            rationale.edge_id,
            type(e).__name__,
            e,
        )
        return WriteStatus(success=False, error=f"{type(e).__name__}: {e}")

    # ⛔ 写确认(⚠️ 判据与 query 末尾那句 `RETURN er.record_id AS record_id` 绑定 ——
    # 7692 实测: 带 RETURN 的 CREATE 返 1 行, 去掉 RETURN 返 0 行。谁删了那句 RETURN,
    # 每一次成功写入都会被本判据误判成失败。存档 write-confirm-rowcount-probe-*.txt):
    # 返回 0 行 = **没有取得写入确认**, 必须记成失败。
    #
    # ⚠️ 措辞边界(Codex r6 M1 整改, 原注释写「没有落盘」过强): `[]` 表达的是
    # **「未取得确认」而不是「确定没写进去」**。存在「已提交但拿不到确认」的路径 ——
    # Neo4j 已提交 → 最终响应在网络上丢失 → ServiceUnavailable/SessionExpired →
    # 重试耗尽 → `_fallback_to_json()` → JSON 分发器返回 `[]`。此时真实结果未知。
    # 保守记成 success=False 仍是对的(宁可让调用方重试/告警, 不可谎报成功), 但不能
    # 宣称「这条没写进去」。本函数不做幂等重试, 那是 client 侧的事, 已登记移交。
    #
    # 为什么非查不可(实测, 存档 evidence-t-edges/fallback-200-falsegreen-*.txt):
    # Neo4jClient 在 JSON fallback 态把查询交给 _run_query_json_fallback, 而那个
    # 分发器只认 MERGE+User+Concept / MATCH+LEARNED 两族, 本函数的
    # `CREATE (er:EdgeRationale …)` 三个分支全不命中 ⇒ 落 else 分支
    # `logger.warning("Unhandled query pattern"); return []` —— **不抛异常**。
    # 进入 fallback 态的路径有三条且都可达: NEO4J_ENABLED=false 构造即 fallback;
    # initialize() 健康检查/AuthError 失败转 fallback; _run_query_neo4j 重试耗尽
    # (ServiceUnavailable 等)转 fallback。⇒ 不查返回值的话, 「Neo4j 宕机」的实际
    # 产出是 **HTTP 200「双写全部成功」, 而这次写连一次确认都没拿到**, 比 500 更坏。
    # (措辞边界 r7-L1: 说「没拿到确认」不说「图库里什么都没有」—— 见上面那段,
    #  返回空行不能据此断言没有落盘。)
    # ⚠️ 这条路是**本卡打通的**: 改前调的 execute_query 不存在, 每次都死在
    # AttributeError, 根本走不到 run_query, 所以 JSON fallback 分支此前不可达。
    if not rows:
        logger.error(
            "Neo4j write NOT confirmed for edge %s (record %s): run_query returned 0 rows "
            "(JSON fallback 的 unhandled-query 分支即如此) — 提交结果未知, 记为写失败",
            rationale.edge_id,
            record_id,
        )
        return WriteStatus(
            success=False,
            error=("Neo4j write not confirmed: query returned no rows (commit outcome unknown — treated as failure)"),
        )

    logger.info(
        "Neo4j write succeeded for edge %s (record %s)",
        rationale.edge_id,
        record_id,
    )
    return WriteStatus(success=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LanceDB Write — Vectorized Rationale Text
# ═══════════════════════════════════════════════════════════════════════════════


#: `_lancedb_row_count` 的「读不出来」哨兵。⛔ 必须与「表不存在(0 行)」分开 ——
#: 两者合并会造出假绿: 写前读失败被当成 0 行, 整表被 drop 重建后的 1 行正好等于 0+1,
#: 历史全丢反而判通过。
_ROW_COUNT_UNKNOWN = -1


def _lancedb_row_count(client: "LanceDBClient", table_name: str) -> int:
    """目标表当前行数; 表不存在返回 0; 读不出来返回 `_ROW_COUNT_UNKNOWN`。

    ⛔ 走 `client._db` / `client._all_table_names()`(都是私有): `LanceDBClient` 的写侧公开
    面上没有「读某张表行数」的访问器, 而本判据必须与 `add_documents` 用**同一个连接**看
    同一个库 —— 另开一条 `lancedb.connect` 既重, 又引入「两个句柄看到不同版本」的新面。已登记。
    """
    db = getattr(client, "_db", None)
    if db is None:
        return _ROW_COUNT_UNKNOWN
    try:
        # ⛔ 存在性判断必须走 `_all_table_names()`, **不是** `db.table_names()`:
        # 后者默认 `limit=10` 分页(lancedb 0.30.2 实测: 建 12 张表只返回 10 张, 排序靠后的
        # 目标表缺席)。用它会把**已经写成功**的表读成「不存在」⇒ 行数网得 `0 -> 0` ⇒ 真实
        # 写入被误报成失败。生产 vault 表数很容易 >10, 那等于本函数恒不确认。
        # 同坑在 `lancedb_client._check_and_fix_dimension_mismatch` 的注释里已记过一次
        # (CARD-G2-9-F1 d), `_all_table_names()` 正是为绕开它而写的。
        if table_name not in client._all_table_names():
            return 0
        return int(db.open_table(table_name).count_rows())
    except Exception:  # noqa: BLE001 — 读不出来必须与「0 行」可分辨, 见上
        return _ROW_COUNT_UNKNOWN


def _lancedb_incompatible_reason(client: "LanceDBClient", table_name: str, vector_dim: int) -> "str | None":
    """既有表与本次写入不兼容的理由; 兼容则返回 None。

    ⛔ **这是前置拒写判据, 不是对上游逻辑的复刻**(CARD-LANCE-DUALWRITE-NEVER-WRITES):
    `add_documents` 在写入前会调 `_check_and_fix_dimension_mismatch`, 后者对
    「缺 `doc_type` 列」或「向量维度不符」的**已存在表**直接 drop + 重建 —— 于是
    「写一条新记录」会把这张表的**全部历史**删掉, 而它照样返回 1, 调用方只看返回值
    会报成功。本函数表达的是**我方的前提**: 只往「schema 与本次写入一致」的表上追加;
    不一致就拒写, 一行历史都不动。
    ⚠️ 覆盖边界如实: 它只挡住上述两条**已知**触发条件。上游若新增第三条, 本函数看不见
    —— 那一层由 `_write_lancedb` 的「写前/写后行数」网兜住(它不认原因, 只认形状)。
    """
    db = getattr(client, "_db", None)
    if db is None:
        return "LanceDB 连接未就绪"
    try:
        table = db.open_table(table_name)
        if "doc_type" not in set(table.schema.names):
            return "既有表缺 doc_type 列 (写入会触发整表 drop 重建)"
        head = table.head(1).to_pydict()
        vectors = head.get("vector") or []
        if vectors and vectors[0] is not None and len(vectors[0]) != vector_dim:
            return f"既有表向量维度 {len(vectors[0])} != 本次 {vector_dim} (写入会触发整表 drop 重建)"
    except Exception as e:  # noqa: BLE001 — 读不出 schema 就不敢写, fail-closed
        return f"既有表 schema 读取失败: {type(e).__name__}: {e}"
    return None


def _lancedb_client_for(vault_id: "str | None") -> "LanceDBClient":
    """按 vault 造一个 LanceDB **写侧**客户端。

    ⛔ 必须传 `vault_id`(CARD-LANCE-DUALWRITE-NEVER-WRITES / 第十五批 P1-A):
    `LanceDBClient.resolve_table_name` 对非 default vault 恒加 `<vault>_` 前缀。改前
    这里是裸 `LanceDBClient()`, 于是表名由进程级 ContextVar / active vault 决定 ——
    双写请求自带的 `vault_id` 被忽略, 多 vault 部署下有写进别人命名空间的面。
    显式传值时 `active_vault_id` 走 `_vault_id_override` 这一支(解析顺序第 1 位);
    传 None 则退回 ContextVar / active vault, 与改前同。

    ⛔ 函数内 import: `agentic_rag` 在 backend/lib, 靠运行期 `sys.path.insert` 挂载
    (rag_service / vault_index_orchestrator 等模块级完成)。导不到时由调用方的
    `except ImportError` 记成「LanceDB 不可用」。
    """
    from agentic_rag.clients.lancedb_client import LanceDBClient

    return LanceDBClient(vault_id=vault_id)


async def _write_lancedb(
    rationale: EdgeRationaleCreate,
    record_id: str,
) -> WriteStatus:
    """
    Write edge rationale to LanceDB for vector retrieval.

    Story 4.2 AC-3: rationale_text vectorized via bge-m3 (1024d Dense).

    ⛔ **本函数改前从不真写** (CARD-LANCE-DUALWRITE-NEVER-WRITES / 第十五批 P1-A):
    `LanceDBClient.add_documents` 是 `async def`, 而改前把它交给 `asyncio` 的
    `to_thread` 去跑 —— `to_thread` 在工作线程里**只是调用**它拿到一个协程对象就
    返回, 函数体一行都不执行、也不抛异常, 于是本函数
    恒返 `WriteStatus(success=True)` 而零写入(进程日志里只有
    `RuntimeWarning: coroutine ... was never awaited`)。端点因此长期谎报「双写成功」,
    半成功 207 里那句「LanceDB 那一半已保留」也是不实陈述。
    现在是单一路径: 工厂 → connect_lightweight → await embed → await add_documents。

    ⛔ **写确认绑 `add_documents` 的返回值**(与 Neo4j 侧「返回 0 行 = 未取得确认」同口径):
    `add_documents` 对内部任何异常都 `return 0` 而**不抛**, 所以返回值是调用方唯一的
    承重信号。返回 != 1 一律记失败。
    ⚠️ 措辞边界: 返回 1 表示「它认为写了 1 条」, 不等于「落盘内容一定正确」——
    真表行数/字段由 `tests/unit/test_edge_rationale_fallback.py` 的真写面段校验。

    ⛔ **不调** `initialize()`: 那会加载 bge-m3 CPU 权重(~7.4s)并跑启动期维度自愈
    (`_cache_tables` → `_check_and_fix_dimension_mismatch`, 有 drop 表的面)。写侧只需要
    一个活的 `_db` 句柄 ⇒ `connect_lightweight`(与 index orchestrator 同口径)。

    ⛔ 不做的相邻面(已登记): AC-5 delete-before-insert 去重 —— `LanceDBClient` 没有
    `delete` 方法(`def delete` 计数 = 0), 改前那三条 `hasattr` 分支是运行期恒不进的死
    分支, 已删。本函数与 Neo4j 侧同为 **append-only**(时序版本历史)。
    """
    try:
        client = _lancedb_client_for(rationale.vault_id)

        # Build document text for vectorization
        doc_text = (
            f"{rationale.source_concept} {rationale.relation_type} "
            f"{rationale.target_concept}: {rationale.rationale_text}"
        )

        metadata = {
            "record_id": record_id,
            "edge_id": rationale.edge_id,
            "source_node_id": rationale.source_node_id,
            "target_node_id": rationale.target_node_id,
            "source_concept": rationale.source_concept,
            "target_concept": rationale.target_concept,
            "relation_type": rationale.relation_type,
            "source_type": "edge_rationale",
            "confidence": rationale.confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if not client.connect_lightweight():
            logger.error(
                "LanceDB connect failed for edge %s (record %s)",
                rationale.edge_id,
                record_id,
            )
            return WriteStatus(success=False, error="LanceDB connect failed")

        # ⛔ 嵌入必须由**调用方**做: `add_documents` 只读 doc 里现成的 `vector`/`embedding`
        # 键, 它自己**不嵌入** —— 改前那句注释「The LanceDBClient handles embedding
        # internally」不实。不给向量就会写进一列 null, 检索侧永远召不回。
        vector = await client.embed(doc_text)

        # ── 向量维度契约(承重, Codex r3 MEDIUM 整改) ──
        # ⛔ `embed()` 只保证「非 None」: 它的 Ollama 分支原样返回服务端给的第一条向量,
        # 模型配错 / 服务端换模型时会**成功返回**一个错误形状的向量。改前本函数零写入,
        # 这条路不可达; 打通写路径后, 一条 8 维向量足以**建出一张 8 维表** ——
        # 它满足 `written == 1` 与 `0 -> 1`, 会被确认成功; 而此后恢复正常的 1024 维输出
        # 反倒被前置拒写永久挡在门外(维度不符)。⇒ 一次坏嵌入 = 这张表从此写不进去。
        # 宁可这一次写不进去, 也不留下一张坏表。
        expected_dim = getattr(client, "embedding_dim", None) or 1024
        # ⛔ **规范化而不是校验**(Codex r3/r4 整改的收敛点): `embed()` 只保证「非 None」,
        # 它的 Ollama 分支原样返回服务端给的东西。真正的危害不是「值不对」而是
        # **列类型被写坏** —— 一条 1024 字符的字符串同样满足长度判据, 建表时会把 vector 列
        # 建成 `string`; 此后正常的 float 向量插进来直接 `ArrowNotImplementedError`,
        # 这张表**从此写不进去**。逐一枚举坏形状关不住(`sum()` 就漏 `bytes`), 所以这里把它
        # **归一成 `list[float]`**: 能归一的列类型必为 float, 归不了的(字符串/嵌套/None)抛错拒写。
        # ⛔ 刻意不用 `isinstance`: `embed()` 注解是 `List[float]`, pyright 会判它多余
        # (reportUnnecessaryIsInstance, 实测 warnings 80→83), 而要防的正是**注解说谎**。
        try:
            vector = [float(component) for component in vector]
            vector_len = len(vector)
        except (TypeError, ValueError):
            vector_len = -1
        if vector_len != expected_dim:
            logger.error(
                "LanceDB write refused for edge %s (record %s): embed 返回长度 %s != 约定维度 %s",
                rationale.edge_id,
                record_id,
                vector_len,
                expected_dim,
            )
            return WriteStatus(
                success=False,
                error=f"LanceDB write refused: embedding dim {vector_len} != expected {expected_dim}",
            )

        # ⛔ `doc_type` 是**承重键**, 不是装饰(本卡真写门实测出来的第二层缺陷):
        # `add_documents` 在写入前调 `_check_and_fix_dimension_mismatch`, 它的 drop 条件
        # 有两个 —— 向量维度不符 **或** 表的 schema 里缺 `doc_type` 列(RAG-P0 A1 加的列)。
        # 不带这个键时首次建表就没有该列, 于是**第二次写入会把整张表 drop 掉重建** ⇒
        # 表里永远只剩最后 1 条, Story 4.2 AC-5 的「时序版本历史(append-only)」当场失效。
        # 改前那条缺陷(从不真写)把这一层完全挡住了, 真写门跑起来才看得见。
        # ⚠️ 本卡**不改** drop 机制本身(G2-9 族, 已登记), 只是让本表不再命中它的触发条件。
        # ── 前置拒写(承重): 既有表与本次写入不兼容 ⇒ 一行历史都不动 ──
        # 改前本函数零写入, 所以这条风险此前不可达; 打通写路径就把它一并打开了。
        table_name = client.resolve_table_name("edge_rationales")
        rows_before = _lancedb_row_count(client, table_name)
        if rows_before == _ROW_COUNT_UNKNOWN:
            logger.error(
                "LanceDB write refused for edge %s (record %s): 目标表 %s 行数读不出来",
                rationale.edge_id,
                record_id,
                table_name,
            )
            return WriteStatus(
                success=False,
                error=f"LanceDB write refused: cannot read row count of {table_name}",
            )
        if rows_before > 0:
            incompatible = _lancedb_incompatible_reason(client, table_name, len(vector))
            if incompatible:
                logger.error(
                    "LanceDB write refused for edge %s (record %s): %s — 拒写以保住 %s 中已有的 %d 行",
                    rationale.edge_id,
                    record_id,
                    incompatible,
                    table_name,
                    rows_before,
                )
                return WriteStatus(
                    success=False,
                    error=(
                        f"LanceDB write refused (would destroy {rows_before} existing rows "
                        f"in {table_name}): {incompatible}"
                    ),
                )

        written = await client.add_documents(
            "edge_rationales",
            [
                {
                    "doc_id": record_id,
                    "content": doc_text,
                    "vector": vector,
                    "source_type": "edge_rationale",
                    "doc_type": "edge_rationale",
                    "metadata": metadata,
                }
            ],
        )

        if written != 1:
            logger.error(
                "LanceDB write NOT confirmed for edge %s (record %s): add_documents returned %s "
                "(它吞掉内部异常返 0, 返回值是唯一信号) — 记为写失败",
                rationale.edge_id,
                record_id,
                written,
            )
            return WriteStatus(
                success=False,
                error=f"LanceDB write not confirmed: add_documents returned {written}",
            )

        # ── 写后行数网(第二层, 承重): after 必须恰好是 before + 1 ──
        # ⛔ 它**不认原因只认形状**: 任何把整表重建掉的机制(含上游将来新增、本卡没复刻的
        # 触发条件)都会让 before=N(≥1) 变成 after=1, 判据当场红。这是前置拒写之外的兜底,
        # ⚠️ 但它只**发现**不**预防** —— 走到这里时历史已经没了, 所以前置拒写才是主防线。
        rows_after = _lancedb_row_count(client, table_name)
        if rows_after != rows_before + 1:
            logger.error(
                "LanceDB write NOT confirmed for edge %s (record %s): %s 行数 %d -> %d (期望 %d) "
                "— 整表可能已被 drop 重建, 历史丢失",
                rationale.edge_id,
                record_id,
                table_name,
                rows_before,
                rows_after,
                rows_before + 1,
            )
            return WriteStatus(
                success=False,
                error=(
                    f"LanceDB write not confirmed: row count of {table_name} went "
                    f"{rows_before} -> {rows_after} (expected {rows_before + 1})"
                ),
            )

        logger.info(
            "LanceDB write succeeded for edge %s (record %s)",
            rationale.edge_id,
            record_id,
        )
        return WriteStatus(success=True)

    except ImportError:
        logger.warning(
            "LanceDB client not available (agentic_rag not installed) for edge %s",
            rationale.edge_id,
        )
        return WriteStatus(
            success=False,
            error="LanceDB client not available (agentic_rag not installed)",
        )

    except (RuntimeError, ConnectionError, OSError, ValueError) as e:
        # RuntimeError 覆盖 `client.embed` 的「Ollama 与 sentence-transformers 全败」路径。
        logger.error(
            "LanceDB write failed for edge %s: %s",
            rationale.edge_id,
            str(e),
        )
        return WriteStatus(success=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /record-rationale — Dual-Write Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@edges_router.post(
    "/record-rationale",
    response_model=EdgeRationaleResponse,
    summary="记录 Edge 连线理由",
    description=(
        "Agent 调用此端点记录用户对连线理由的解释。执行 Neo4j + LanceDB 双写，支持部分失败（207 Multi-Status）。"
    ),
    responses={
        200: {"description": "双写全部成功"},
        207: {"description": "部分成功——一个写入成功，另一个失败"},
        500: {"description": "双写全部失败"},
    },
)
async def record_edge_rationale(
    rationale: EdgeRationaleCreate,
) -> JSONResponse:
    """
    Record edge rationale with dual-write semantics.

    Story 4.2 AC-6: MCP tool record_edge_rationale.
    Story 4.4 AC-3: MCP tool call failure → Outbox retry (frontend side).
    Story 4.4 AC-4: Partial failure → 207, successful part preserved.

    Dual-write flow:
    1. Generate unique record_id
    2. Write to Neo4j (structured KG-triplet) — independent try-catch
    3. Write to LanceDB (vectorized rationale) — independent try-catch
    4. Return combined status (200/207/500)
    """
    record_id = str(uuid.uuid4())

    # Wave-5 Stage B 续 — P0 双写路径! vault_id 注入 ContextVar +
    # 派生 group_id 供 Neo4j INSERT 用.
    resolved_group_id = resolve_vault_group_id(
        rationale.vault_id,
        subject_id=rationale.subject_id,
        legacy_group_id=rationale.group_id,
    )

    logger.info(
        "Recording edge rationale: edge=%s, %s --[%s]--> %s (confidence=%.2f)",
        rationale.edge_id,
        rationale.source_concept,
        rationale.relation_type,
        rationale.target_concept,
        rationale.confidence,
    )

    # Story 4.2 AC-3: Dual-write async — both writes run concurrently
    graphiti_status, lancedb_status = await asyncio.gather(
        _write_neo4j_triplet(rationale, record_id, resolved_group_id),
        _write_lancedb(rationale, record_id),
    )

    response = EdgeRationaleResponse(
        record_id=record_id,
        edge_id=rationale.edge_id,
        relation_type=rationale.relation_type,
        graphiti_status=graphiti_status,
        lancedb_status=lancedb_status,
    )

    # Story 4.4 AC-4: Determine HTTP status based on write results
    if response.fully_successful:
        http_status = status.HTTP_200_OK
    elif response.partially_successful:
        # 207 Multi-Status: one succeeded, one failed
        http_status = 207
        logger.warning(
            "Partial dual-write for edge %s: neo4j=%s, lancedb=%s",
            rationale.edge_id,
            graphiti_status.success,
            lancedb_status.success,
        )
    else:
        # Both failed
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(
            "Both writes failed for edge %s: neo4j=%s, lancedb=%s",
            rationale.edge_id,
            graphiti_status.error,
            lancedb_status.error,
        )

    return JSONResponse(
        status_code=http_status,
        content=response.model_dump(),
    )
