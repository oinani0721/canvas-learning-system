# Story 4.4: Edge Dialog Fallback - Dual-Write Partial Failure Tests
# [Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 9.3]
"""
Unit tests for record_edge_rationale dual-write partial failure handling.

Verifies:
  - AC-4: Graphiti success + LanceDB fail => 207 Multi-Status
  - AC-4: LanceDB success + Graphiti fail => 207 Multi-Status
  - AC-4: Both fail => 500
  - AC-4: Both succeed => 200
  - AC-3: Successful part preserved (not rolled back)

⛔ 本文件的**覆盖边界**（CARD-LANCE-DUALWRITE-NEVER-WRITES / 第十五批 P1-A 补记）:
前 9 个用例整体 ``patch("app.api.v1.endpoints.edges._write_neo4j_triplet")`` 与
``…_write_lancedb``，它们钉住的是 **handler 的 200/207/500 组合逻辑**——这一层仍然
有效，所以本卡**不删**它们。但把两个被测写函数本身换成桩，等于这两个函数在本文件里
**零覆盖**：第十四批 T5-B 的 ``execute_query`` 不存在、以及本卡的
``to_thread`` 调 ``async def`` 从不真写，都对这 9 个用例完全不可见。

这两块缺口各自的门在:
  - ``_write_lancedb`` 真写门 → **本文件下方「真写面」段**（真 LanceDB + tmp_path）;
  - ``_write_neo4j_triplet`` 降级门与真库门 →
    ``backend/tests/integration/test_edges_dual_write_neo4j_t5b.py``。
"""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI TestClient using a minimal app with only the edges router.

    Story 4-3/4-4 FIX M2: Uses a lightweight FastAPI app instead of importing
    the full app (which loads all middleware, startup hooks, DB connections etc.).
    This makes tests faster and avoids side effects from unrelated components.
    """
    from app.api.v1.endpoints.edges import edges_router

    minimal_app = FastAPI()
    minimal_app.include_router(edges_router, prefix="/api/v1/edges")
    return TestClient(minimal_app)


@pytest.fixture
def valid_rationale_payload():
    """Minimal valid EdgeRationaleCreate payload."""
    return {
        "edge_id": "edge-test-001",
        "source_node_id": "node-a",
        "target_node_id": "node-b",
        "source_concept": "Concept A",
        "target_concept": "Concept B",
        "relation_type": "is prerequisite for",
        "rationale_text": "A must be understood before B because of X",
        "confidence": 0.85,
        "strategies_applied": ["EI", "SE"],
        "questioning_rounds": 3,
        "explanation_depth_score": 4,
    }


def _ws(success, error=None):
    """Helper: create WriteStatus instance."""
    from app.models.edge_rationale import WriteStatus

    return WriteStatus(success=success, error=error)


def test_both_writes_succeed_returns_200(client, valid_rationale_payload):
    """When both Graphiti and LanceDB writes succeed, return 200."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        assert body["lancedb_status"]["success"] is True
        assert body["edge_id"] == "edge-test-001"
        assert body["relation_type"] == "is prerequisite for"
        assert "record_id" in body


def test_graphiti_ok_lancedb_fail_returns_207(client, valid_rationale_payload):
    """When Graphiti succeeds but LanceDB fails, return 207 Multi-Status."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "LanceDB connection timeout"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        assert body["lancedb_status"]["success"] is False
        assert body["lancedb_status"]["error"] == "LanceDB connection timeout"
        assert "record_id" in body


def test_lancedb_ok_graphiti_fail_returns_207(client, valid_rationale_payload):
    """When LanceDB succeeds but Graphiti fails, return 207 Multi-Status."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(False, "Neo4j client not available"),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is False
        assert body["graphiti_status"]["error"] == "Neo4j client not available"
        assert body["lancedb_status"]["success"] is True
        assert "record_id" in body


def test_both_writes_fail_returns_500(client, valid_rationale_payload):
    """When both Graphiti and LanceDB fail, return 500."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(False, "Neo4j down"),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "LanceDB disk full"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["graphiti_status"]["success"] is False
        assert body["lancedb_status"]["success"] is False


def test_graphiti_exception_does_not_block_lancedb(client, valid_rationale_payload):
    """Graphiti failure should not prevent LanceDB write from completing."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(False, "ConnectionRefusedError"),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_l,
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["lancedb_status"]["success"] is True
        stub_g.assert_called_once()
        stub_l.assert_called_once()


def test_lancedb_exception_does_not_block_graphiti(client, valid_rationale_payload):
    """LanceDB failure should not prevent Graphiti write from completing."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "ImportError: lancedb not installed"),
        ) as stub_l,
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        stub_g.assert_called_once()
        stub_l.assert_called_once()


def test_partial_failure_includes_error_details(client, valid_rationale_payload):
    """207 response includes specific error details for each failed write."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "Table edge_rationales locked by concurrent writer"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert "locked" in body["lancedb_status"]["error"]
        assert "timestamp" in body


def test_strategy_fields_accepted(client, valid_rationale_payload):
    """Verify strategies_applied, questioning_rounds, explanation_depth_score
    are accepted in the request and passed to the write functions."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 200
        call_args = stub_g.call_args
        rationale_arg = call_args[0][0]
        assert rationale_arg.strategies_applied == ["EI", "SE"]
        assert rationale_arg.questioning_rounds == 3
        assert rationale_arg.explanation_depth_score == 4


def test_strategy_fields_defaults(client):
    """Verify strategy fields use defaults when not provided."""
    minimal_payload = {
        "edge_id": "edge-min-001",
        "source_node_id": "node-a",
        "target_node_id": "node-b",
        "relation_type": "related",
        "rationale_text": "They are related",
        "confidence": 0.5,
    }
    with (
        patch(
            "app.api.v1.endpoints.edges._write_neo4j_triplet",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=minimal_payload,
        )
        assert resp.status_code == 200
        call_args = stub_g.call_args
        rationale_arg = call_args[0][0]
        assert rationale_arg.strategies_applied == ["EI", "SE"]
        assert rationale_arg.questioning_rounds == 0
        assert rationale_arg.explanation_depth_score == 0


def test_response_model_fully_successful():
    """EdgeRationaleResponse.fully_successful is True when both succeed."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=True),
        lancedb_status=WriteStatus(success=True),
    )
    assert resp.fully_successful is True
    assert resp.partially_successful is False


def test_response_model_partially_successful():
    """EdgeRationaleResponse.partially_successful is True when one fails."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=True),
        lancedb_status=WriteStatus(success=False, error="fail"),
    )
    assert resp.fully_successful is False
    assert resp.partially_successful is True


def test_response_model_both_failed():
    """Both failed => not fully_successful, not partially_successful."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=False, error="g-fail"),
        lancedb_status=WriteStatus(success=False, error="l-fail"),
    )
    assert resp.fully_successful is False
    assert resp.partially_successful is False


# ═══════════════════════════════════════════════════════════════════════════════
# 真写面 — CARD-LANCE-DUALWRITE-NEVER-WRITES [BATCH-2026-09-18-第十五批 / P1-A]
# ═══════════════════════════════════════════════════════════════════════════════
#
# 被锁的缺陷: ``_write_lancedb`` 用 ``await asyncio.to_thread(client.add_documents, …)``
# 调一个 ``async def`` —— ``to_thread`` 在工作线程里**只是调用**它拿到一个协程对象就
# 返回, 函数体一行都不执行、也不抛异常, 于是它恒返 ``WriteStatus(success=True)`` 而
# **零写入**。上面那 9 个用例整体 patch 掉 ``_write_lancedb`` 本身, 所以这条缺陷对它们
# 完全不可见 —— 本段是那个缺口。
#
# ⛔ 纪律(与 ``test_lancedb_cross_vault_drop_g29f1.py`` 同款): 全部数据落 ``tmp_path``,
# 不碰 ``LANCEDB_DATA_PATH`` 指向的真实库; ``connect_lightweight`` / ``add_documents``
# / ``resolve_table_name`` 一律**原样真跑**(本段要证的就是它们被调到了), 只把 ``embed``
# 换成确定性实现以去掉 Ollama 网络依赖。
# ⛔ 写成功的判据是**表名 + 行数 + doc_id**, 不是 ``WriteStatus.success is True`` ——
# 后者恰恰是缺陷期的谎报值。

#: 直接调 ``_write_lancedb`` 的三道门用的 vault（端点门走 active vault，见该门 docstring）。
_REAL_WRITE_VAULT = "p1adualwrite"
_EDGE_TABLE = "edge_rationales"
_EXPECTED_TABLE = f"{_REAL_WRITE_VAULT}_{_EDGE_TABLE}"
#: bge-m3 Dense 维度（``LanceDBClient.DEFAULT_EMBEDDING_DIM``）。
_EMBED_DIM = 1024


def _put_backend_lib_on_path() -> None:
    """把 ``backend/lib`` 挂上 sys.path —— ``agentic_rag`` 在运行期靠这条挂载。

    生产里由 ``rag_service`` / ``vault_index_orchestrator`` 等模块级 ``sys.path.insert``
    完成; ``edges.py`` 自己不挂, 只做函数内 import。测试进程里不保证有哪个模块先被导入,
    所以这里按 ``test_lancedb_cross_vault_drop_g29f1.py`` 的同款写法自挂。
    """
    lib = str(Path(__file__).resolve().parents[2] / "lib")
    if lib not in sys.path:
        sys.path.insert(0, lib)


def _deterministic_vector(text: str) -> list:
    """确定性 1024 维向量 —— 同文本恒同向量, 零网络（不碰 Ollama / 不加载 bge-m3 CPU 权重）。"""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [((digest[i % len(digest)] + i) % 251) / 251.0 for i in range(_EMBED_DIM)]


@pytest.fixture
def real_lancedb(tmp_path, monkeypatch):
    """真 LanceDB(tmp_path) + ``LanceDBClient`` 测试子类, 并把它打进**源模块**。

    ⛔ 打的是 ``agentic_rag.clients.lancedb_client.LanceDBClient``（源模块属性）,
    不是 edges 模块上的名字: ``_write_lancedb`` / ``_lancedb_client_for`` 都在**函数体内**
    局部 import 它, edges 模块上根本没有这个属性。打源模块的另一个好处是它在**缺陷期与
    修复后都生效** —— 两跑的差别只来自 edges.py 自己。
    """
    lancedb = pytest.importorskip("lancedb")
    _put_backend_lib_on_path()
    from agentic_rag.clients import lancedb_client as lancedb_client_module

    db_dir = tmp_path / "lancedb"
    created: list = []

    class _TmpLanceDBClient(lancedb_client_module.LanceDBClient):
        """只改两处: db_path 钉在 tmp_path、embed 换成确定性实现。其余全是真的。"""

        def __init__(self, *args, **kwargs):
            kwargs.pop("db_path", None)
            super().__init__(*args, db_path=str(db_dir), **kwargs)
            created.append(self)

        async def embed(self, text: str) -> list:
            return _deterministic_vector(text)

    class _NoDbLanceDBClient(_TmpLanceDBClient):
        """connect 谎报成功但 ``_db`` 仍是 None —— 逼出 ``add_documents`` 的早退分支(返 0)。

        这不是编出来的形态: ``add_documents`` 开头就是 ``if self._db is None: return 0``,
        且它对内部任何异常都 ``return 0``（不抛）⇒ **返回值是调用方唯一的承重信号**。
        """

        def connect_lightweight(self) -> bool:
            self._initialized = True
            return True

    class _ConnectFailsLanceDBClient(_TmpLanceDBClient):
        """connect 明确失败(如 lancedb 未安装 / 路径不可写)。"""

        def connect_lightweight(self) -> bool:
            return False

    class _AddReturnsZeroLanceDBClient(_TmpLanceDBClient):
        """连接正常, 但 `add_documents` 返 0 —— 它对内部异常一律 `return 0` 而不抛的真实契约。

        ⛔ 为什么需要这个子类: 前置拒写把 `_db is None` 截在更早一步, 于是「按返回值判写
        确认」那条判据在那个场景里**不再被走到**。修复改变了缺陷的可观测性, 门必须跟着分层。
        """

        async def add_documents(self, table_name, documents):
            return 0

    class _SilentRebuildLanceDBClient(_TmpLanceDBClient):
        """模拟**上游将来新增、本卡没复刻**的 drop 触发条件: 整表重建后只剩 1 行, 仍返回 1。

        用来正控「写前/写后行数」这第二层网 —— 它不认原因只认形状。
        """

        async def add_documents(self, table_name, documents):
            resolved = self.resolve_table_name(table_name)
            if self._db is not None and resolved in self._db.table_names():
                self._db.drop_table(resolved, ignore_missing=True)
            return await super().add_documents(table_name, documents)

    class _ReadFailsLanceDBClient(_TmpLanceDBClient):
        """连接正常, 但**读**表名/表会抛 —— 覆盖 `_lancedb_row_count` 的 except 分支。

        ⛔ 为什么需要它(Codex r2 MEDIUM): 原来只有「`_db is None`」一个用例, 它走的是
        `_lancedb_row_count` 更前面那条独立早退, **没有**碰到 except 分支。于是把
        `except: return _ROW_COUNT_UNKNOWN` 改成 `return 0`(正是作者特别防范的
        「读取失败被当成空表」)时, 所有门仍会绿。
        """

        def connect_lightweight(self) -> bool:
            ok = super().connect_lightweight()
            real_db = self._db

            class _ExplodingDb:
                def __getattr__(inner, name):
                    if name in ("table_names", "open_table", "list_tables"):

                        def boom(*a, **k):
                            raise RuntimeError("P1A-READ-FAIL: table listing unavailable")

                        return boom
                    return getattr(real_db, name)

            self._db = _ExplodingDb()
            return ok

    class _BadDimEmbedLanceDBClient(_TmpLanceDBClient):
        """`embed` **成功返回**一个错误形状的向量（8 维）—— 模型配错 / 服务端换模型的真实形态。

        ⛔ 与 `_EmbedFailsLanceDBClient` 的区别是承重的（Codex r3 MEDIUM）: 那个**抛异常**,
        这个**成功返回**。只测抛异常那一格, 「成功返回错误形状」就没有任何门看着。
        """

        async def embed(self, text: str) -> list:
            return _deterministic_vector(text)[:8]

    class _StringEmbedLanceDBClient(_TmpLanceDBClient):
        """`embed` 返回一条**长度正确但类型错误**的「向量」（1024 字符的字符串）。

        ⛔ Codex r4 MEDIUM: 它满足长度判据, 建表时会把 vector 列建成 `string`;
        此后正常 float 向量插进来直接 `ArrowNotImplementedError` —— 这张表从此写不进去。
        """

        async def embed(self, text: str) -> list:
            return "x" * _EMBED_DIM  # pyright: ignore[reportReturnType]  # 刻意违约: 本门要的就是坏返回

    class _EmbedFailsLanceDBClient(_TmpLanceDBClient):
        """embed 全败 —— 真实形态: Ollama 与 sentence-transformers 都不可用时它抛 RuntimeError。"""

        async def embed(self, text: str) -> list:
            raise RuntimeError("P1A-EMBED-DOWN: neither Ollama nor sentence-transformers")

    monkeypatch.setattr(lancedb_client_module, "LanceDBClient", _TmpLanceDBClient)

    return SimpleNamespace(
        lancedb=lancedb,
        db_dir=db_dir,
        created=created,
        cls=_TmpLanceDBClient,
        no_db_cls=_NoDbLanceDBClient,
        add_zero_cls=_AddReturnsZeroLanceDBClient,
        read_fails_cls=_ReadFailsLanceDBClient,
        bad_dim_cls=_BadDimEmbedLanceDBClient,
        string_embed_cls=_StringEmbedLanceDBClient,
        silent_rebuild_cls=_SilentRebuildLanceDBClient,
        connect_fails_cls=_ConnectFailsLanceDBClient,
        embed_fails_cls=_EmbedFailsLanceDBClient,
        module=lancedb_client_module,
    )


def _rationale(suffix: str, *, vault_id=_REAL_WRITE_VAULT):
    from app.models.edge_rationale import EdgeRationaleCreate

    return EdgeRationaleCreate(
        edge_id=f"edge-p1a-{suffix}",
        source_node_id=f"node-a-{suffix}",
        target_node_id=f"node-b-{suffix}",
        source_concept="Concept A",
        target_concept="Concept B",
        relation_type="is prerequisite for",
        rationale_text=f"A must be understood before B because of X ({suffix})",
        confidence=0.85,
        strategies_applied=["EI", "SE"],
        questioning_rounds=3,
        explanation_depth_score=4,
        vault_id=vault_id,
    )


def _assert_factory_anchor(real_lancedb, expected_min=1):
    """注入锚（承重, 0→≥1）: 证明跑的是 tmp_path 子类, 不是指向生产库的真客户端。"""
    assert len(real_lancedb.created) >= expected_min, (
        f"注入锚失败: _TmpLanceDBClient 实例数 {len(real_lancedb.created)} < {expected_min} —— "
        "这一跑很可能用的是指向 LANCEDB_DATA_PATH 的真客户端, 请登记后再排查"
    )
    for inst in real_lancedb.created:
        assert inst.db_path == str(real_lancedb.db_dir), f"客户端 db_path 不是 tmp_path: {inst.db_path!r}"


async def test_lancedb_real_write_lands_one_row(real_lancedb):
    """G1① 真写门: 调一次 ``_write_lancedb`` 后, 真表里必须恰有 1 行且 doc_id = record_id.

    改前（``to_thread`` 调 async）: 表根本不存在 ⇒ RED, 而 ``WriteStatus.success`` 仍是
    True —— 失败消息里一并打出那个值, 它就是「端点谎报写成功」的证据。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    record_id = "rec-p1a-0001"
    rationale = _rationale("0001")
    status_ = await _write_lancedb(rationale, record_id)

    _assert_factory_anchor(real_lancedb)

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    tables = db.table_names()
    assert _EXPECTED_TABLE in tables, (
        f"表 {_EXPECTED_TABLE!r} 不存在 ⇒ LanceDB 侧没有真写。库内表: {tables}。"
        f"⚠️ 同一次调用返回的 WriteStatus.success = {status_.success!r} (error={status_.error!r})"
        # ⛔ 这句推断必须跟着实际值走, 不能写死: 负控(把调用改回交给 to_thread)下
        # success 是 False —— 写确认判据抓到了协程对象。失败消息不得比事实更强。
        + (
            " —— success=True + 表不存在 = 端点在谎报写成功"
            if status_.success
            else " —— success 已为 False(写确认判据接住了), 但表仍未建出 ⇒ 真写路径断了"
        )
    )
    table = db.open_table(_EXPECTED_TABLE)
    assert table.count_rows() == 1, f"期望恰 1 行, 实得 {table.count_rows()}"

    rows = table.to_arrow().to_pylist()
    assert rows[0]["doc_id"] == record_id, f"doc_id 不符: {rows[0]['doc_id']!r}"
    assert rationale.rationale_text in rows[0]["content"], f"content 里没有 rationale_text: {rows[0]['content']!r}"
    assert len(rows[0]["vector"]) == _EMBED_DIM, (
        f"向量维度 {len(rows[0]['vector'])} != {_EMBED_DIM} —— 写进去的不是 bge-m3 Dense 形态"
    )
    # metadata 十键经 add_documents 序列化进 metadata_json —— 钉住键没在传参时丢掉
    # metadata 十键经 add_documents 序列化进 metadata_json —— **逐键**核对
    # ⛔ Codex r2 LOW 整改: 原来只核 record_id / edge_id 两项, 而注释却写「十键」——
    # 删掉生产 metadata 里的 source_node_id / confidence / timestamp 该门照样绿,
    # 判据的取名面小于它的主张。
    meta = json.loads(rows[0]["metadata_json"])
    assert set(meta) == {
        "record_id",
        "edge_id",
        "source_node_id",
        "target_node_id",
        "source_concept",
        "target_concept",
        "relation_type",
        "source_type",
        "confidence",
        "timestamp",
    }, f"metadata 键集漂移(期望恰 10 键): {sorted(meta)}"
    assert meta["record_id"] == record_id
    assert meta["edge_id"] == rationale.edge_id
    assert meta["source_node_id"] == rationale.source_node_id
    assert meta["target_node_id"] == rationale.target_node_id
    assert meta["relation_type"] == rationale.relation_type
    assert meta["source_type"] == "edge_rationale"
    assert meta["confidence"] == rationale.confidence
    # ⛔ Codex r3 LOW 整改: 原来漏了这两个 concept 的**值** —— 把生产里两者互换,
    # 门照样绿。键集对上不等于值对上。
    assert meta["source_concept"] == rationale.source_concept
    assert meta["target_concept"] == rationale.target_concept
    assert meta["source_concept"] != meta["target_concept"], "两个 concept 取到了同一个值 —— 互换/错位不可分辨"
    from datetime import datetime as _dt

    _dt.fromisoformat(meta["timestamp"])  # 形状必须是 ISO 8601, 非空还不够
    # doc_type 列必须在 schema 里, 否则下一次写入会触发 drop+重建(见生产侧注释)
    assert "doc_type" in set(table.schema.names), (
        f"表 schema 缺 doc_type 列 ⇒ 下一次写入会把整张表 drop 重建: {table.schema.names}"
    )
    assert status_.success is True, f"真写成功后 WriteStatus 应为成功, 实得 {status_!r}"


async def test_lancedb_real_write_is_append_only(real_lancedb):
    """G1② append-only: **同一条 edge** 的第二次记录写进同一张表 ⇒ 2 行（AC-5 去重不做）。

    ⛔ 两次写必须用**同一个 edge_id**(Codex r1 MEDIUM 整改): 原写法用两个不同 suffix ⇒
    两个不同 edge_id, 那只证明了「跨 edge 会累积、第二次写没把整表清空」, **证明不了
    Story 4.2 AC-5 要的「同一条 edge 的时序版本历史」** —— 把写路径改成「每个 edge 只
    保留最新记录」, 原写法照样绿。判据的取名面不等于它的主张。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    shared = _rationale("same-edge")
    first = await _write_lancedb(shared, "rec-p1a-0002")
    second = await _write_lancedb(shared, "rec-p1a-0003")

    _assert_factory_anchor(real_lancedb, expected_min=2)

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE in db.table_names(), f"表不存在 ⇒ 没有真写（两次 WriteStatus: {first!r} / {second!r}）"
    table = db.open_table(_EXPECTED_TABLE)
    assert table.count_rows() == 2, f"append-only 期望 2 行, 实得 {table.count_rows()}"
    rows = table.to_arrow().to_pylist()
    doc_ids = sorted(r["doc_id"] for r in rows)
    assert doc_ids == ["rec-p1a-0002", "rec-p1a-0003"], f"doc_id 集合不符: {doc_ids}"
    # 承重: 两行属于**同一条 edge** ⇒ 这才是「同一条边的版本历史」
    edge_ids = {json.loads(r["metadata_json"])["edge_id"] for r in rows}
    assert edge_ids == {shared.edge_id}, (
        f"两行不属于同一条 edge({edge_ids}) —— 本门若用不同 edge_id, 「每 edge 只留最新」"
        f"的实现照样能过, 判据就名不副实了"
    )


async def test_lancedb_real_write_db_unreadable_is_refused(real_lancedb, monkeypatch):
    """G1③-a 前置拒写: 连接没就绪(读不出目标表行数) ⇒ 拒写, **不调** add_documents。

    ⛔ 「读不出来」必须与「表不存在(0 行)」可分辨: 合并成 0 会造出假绿 —— 写前读失败被
    当成 0 行, 整表被 drop 重建后的 1 行正好等于 0+1, 历史全丢反而判通过。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", real_lancedb.no_db_cls)

    status_ = await _write_lancedb(_rationale("0004"), "rec-p1a-0004")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"连接未就绪必须拒写, 实得 {status_!r}"
    assert "refused" in (status_.error or "").lower(), f"错误串未表明是拒写: {status_.error!r}"

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE not in db.table_names(), "拒写路径却建出了表 —— 前提已变"


async def test_lancedb_real_write_add_documents_returns_zero_is_failure(real_lancedb, monkeypatch):
    """G1③-b 写确认: 连接正常但 `add_documents` 返 0 ⇒ 必须记失败, 不得报成功。

    `add_documents` 对内部任何异常都 `return 0` 而**不抛** ⇒ 返回值是调用方唯一的承重
    信号, 与 Neo4j 侧「返回 0 行 = 未取得写入确认」同口径。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", real_lancedb.add_zero_cls)

    status_ = await _write_lancedb(_rationale("0004b"), "rec-p1a-0004b")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"add_documents 返 0 必须记失败, 实得 {status_!r}"
    assert "not confirmed" in (status_.error or "").lower(), f"错误串里缺「not confirmed」: {status_.error!r}"
    assert "returned 0" in (status_.error or ""), f"错误串未带上那个承重的返回值: {status_.error!r}"


def _seed_incompatible_table(real_lancedb, *, with_doc_type: bool, dim: int, rows: int = 2):
    """预置一张**含历史**的目标表, 供前置拒写门用。返回 (db, table_name)。"""
    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    data = []
    for i in range(rows):
        row = {
            "doc_id": f"legacy-{i}",
            "content": f"历史记录 {i}",
            "vector": [0.01 * (i + 1)] * dim,
        }
        if with_doc_type:
            row["doc_type"] = "edge_rationale"
        data.append(row)
    db.create_table(_EXPECTED_TABLE, data=data)
    return db


@pytest.mark.parametrize(
    "with_doc_type,dim,expected_fragment",
    [(False, _EMBED_DIM, "doc_type"), (True, 8, "维度")],
    ids=["legacy-table-missing-doc_type", "legacy-table-dim-mismatch"],
)
async def test_lancedb_real_write_refuses_to_destroy_existing_history(
    real_lancedb, with_doc_type, dim, expected_fragment
):
    """G1⑥ **前置拒写(主防线)**: 既有表与本次写入不兼容 ⇒ 拒写, **旧行一条不少**。

    ⛔ 这是 Codex r1 HIGH 的锁: `add_documents` 写入前调
    `_check_and_fix_dimension_mismatch`, 它对「缺 doc_type 列」或「向量维度不符」的
    **已存在表**直接 drop + 重建 —— 写一条新记录会把整张表的历史删光, 而它照样返回 1。
    只看返回值的调用方会报成功。本门要求: 走到 `add_documents` **之前**就拒掉。
    ⚠️ 与 G1⑧ 的分工: 本门证「预防」(旧行还在), G1⑧ 证「发现」(历史已丢但不谎报成功)。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    db = _seed_incompatible_table(real_lancedb, with_doc_type=with_doc_type, dim=dim)
    assert db.open_table(_EXPECTED_TABLE).count_rows() == 2, "种子表没铺好"

    status_ = await _write_lancedb(_rationale("0006"), "rec-p1a-0006")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"不兼容的既有表必须拒写, 实得 {status_!r}"
    assert "refused" in (status_.error or "").lower()
    assert "2 existing rows" in (status_.error or ""), f"错误串未说明会毁掉几行历史: {status_.error!r}"
    assert expected_fragment in (status_.error or ""), f"错误串未点明不兼容的具体原因: {status_.error!r}"

    # ── 承重: 旧行一条不少（证明这是**预防**而不是事后发现）──
    after = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE in after.table_names(), "整张表被删掉了 —— 拒写失效"
    table = after.open_table(_EXPECTED_TABLE)
    assert table.count_rows() == 2, f"历史行数从 2 变成 {table.count_rows()} —— 历史被毁"
    assert sorted(r["doc_id"] for r in table.to_arrow().to_pylist()) == [
        "legacy-0",
        "legacy-1",
    ]


async def test_lancedb_real_write_row_count_net_catches_silent_rebuild(real_lancedb, monkeypatch):
    """G1⑧ **写后行数网(第二层)**: 整表被重建但仍返回 1 ⇒ 必须记失败。

    模拟的是**上游将来新增、本卡前置判据没复刻**的 drop 触发条件。本网不认原因只认形状:
    `before=N(≥1)` 变成 `after=1` 就红。
    ⚠️ 如实: 它只**发现**不**预防** —— 走到这里历史已经没了, 所以 G1⑥ 的前置拒写才是主防线。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    _seed_incompatible_table(real_lancedb, with_doc_type=True, dim=_EMBED_DIM)
    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", real_lancedb.silent_rebuild_cls)

    status_ = await _write_lancedb(_rationale("0008"), "rec-p1a-0008")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"整表被重建却报了成功: {status_!r}"
    assert "not confirmed" in (status_.error or "").lower()
    assert "2 -> 1" in (status_.error or "") and "expected 3" in (status_.error or ""), (
        f"错误串未带上行数形状(2 -> 1, 期望 3): {status_.error!r}"
    )


@pytest.mark.parametrize(
    "variant,expected_error_fragment",
    [("connect_fails", "connect failed"), ("embed_fails", "P1A-EMBED-DOWN")],
    ids=["connect-fails", "embed-fails"],
)
def test_lancedb_real_write_新打通分支的失败必须记成写失败(real_lancedb, monkeypatch, variant, expected_error_fragment):
    """G1⑤ **本卡修复新打通的分支**: connect / embed 失败必须记成 WriteStatus(False) 且零建表。

    ⛔ 为什么这两条是新的: 改前 `_write_lancedb` 既不 connect 也不 embed —— 它把 async 的
    `add_documents` 交给 `to_thread` 拿了个协程就走人, 这两个调用**根本不存在**, 它们的
    失败路径此前不可达。修好一个恒失败的调用, 等于打通它下游一整片没人走过的分支,
    所以这两条必须各自有门, 不能靠「反正 except 会接住」。

    - connect 失败 → 明确的 "LanceDB connect failed"(不是笼统异常);
    - embed 失败 → 真实形态是 `RuntimeError`(Ollama 与 CPU vectorizer 全败), 由既有
      except 元组里的 RuntimeError 接住并把原文放进 error。
    """
    import asyncio as _asyncio

    from app.api.v1.endpoints.edges import _write_lancedb

    cls = {
        "connect_fails": real_lancedb.connect_fails_cls,
        "embed_fails": real_lancedb.embed_fails_cls,
    }[variant]
    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", cls)

    status_ = _asyncio.run(_write_lancedb(_rationale(f"0005-{variant}"), f"rec-p1a-{variant}"))

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"{variant} 必须记成写失败, 实得 {status_!r}"
    assert expected_error_fragment in (status_.error or ""), f"错误串未带可分辨信息({variant}): {status_.error!r}"

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE not in db.table_names(), f"失败路径上却建出了表: {db.table_names()}"


async def test_lancedb_real_write_survives_table_name_pagination(real_lancedb):
    """G1⑨ **分页门**: 库里已有 11 张排序靠前的表时, 行数判据仍须认出目标表。

    ⛔ Codex r2 MEDIUM(实测坐实): `Connection.table_names()` 默认 **limit=10**。目标表
    `p1adualwrite_edge_rationales` 以 `p` 开头, 被 11 张 `aa_*` 挤出第一页 ⇒ 用它做存在性
    判断会把**已写成功**的表读成「不存在」, 行数网得 `0 -> 0`, 于是**真实写入被报成失败**。
    生产 vault 的表数很容易 >10, 所以这几乎必然发生 —— 本卡的修复会退化成「恒不确认」。
    ⇒ 两个 helper 必须走 `_all_table_names()`(它正是为绕开这个分页而写的)。

    临时库实测(本门之外的独立探针): 建 12 张表时 `table_names()` 恰返回 10 张、目标表缺席;
    `_all_table_names()` 返回 12 张。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    for i in range(11):
        db.create_table(
            f"aa_{i:02d}",
            data=[{"doc_id": "x", "content": "c", "vector": [0.1] * 8, "doc_type": "t"}],
        )
    # 前提锚: 这些表确实把目标表挤出了第一页（否则本门什么也没测）
    assert len(db.table_names()) == 10, f"分页前提不成立: {db.table_names()}"

    status_ = await _write_lancedb(_rationale("0009"), "rec-p1a-0009")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is True, f"分页把已写成功的表读成不存在 ⇒ 真实写入被误报成失败: {status_!r}"
    after = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    table = after.open_table(_EXPECTED_TABLE)
    assert table.count_rows() == 1
    assert table.to_arrow().to_pylist()[0]["doc_id"] == "rec-p1a-0009"


async def test_lancedb_real_write_read_failure_is_refused_not_treated_as_empty(real_lancedb, monkeypatch):
    """G1⑩ **读异常门**: 读表名/表本身抛异常 ⇒ 拒写, **不得**被当成「空表」。

    ⛔ Codex r2 MEDIUM: 「`_db is None`」那一格走的是更前面的独立早退, 碰不到
    `_lancedb_row_count` 的 except 分支。把 `except: return _ROW_COUNT_UNKNOWN` 改成
    `return 0` 时, 写前被当成 0 行 ⇒ 跳过前置兼容检查 ⇒ 整表重建后的 1 行恰好满足
    `1 == 0 + 1` ⇒ 全绿。本门就是锁那条分支的。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", real_lancedb.read_fails_cls)

    status_ = await _write_lancedb(_rationale("0010"), "rec-p1a-0010")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"读不出行数却照写: {status_!r}"
    assert "refused" in (status_.error or "").lower(), f"读取失败被当成了空表(错误串不是拒写): {status_.error!r}"


@pytest.mark.parametrize(
    "variant,expect_fragment",
    [("bad_dim", "dim"), ("string_embed", "dim")],
    ids=["embed-returns-8-dim", "embed-returns-1024-char-string"],
)
async def test_lancedb_real_write_refuses_wrong_embedding_dim(real_lancedb, monkeypatch, variant, expect_fragment):
    """G1⑪ **向量维度契约**: `embed` **成功返回**错误形状时必须拒写, 不得建出坏表。

    ⛔ Codex r3 MEDIUM: `embed()` 只保证非 None, 其 Ollama 分支原样返回服务端给的向量。
    模型配错时它会成功返回一条 8 维向量 —— 那足以**建出一张 8 维表**, 满足
    `written == 1` 与 `0 -> 1` 被确认成功; 此后恢复正常的 1024 维输出反倒被前置拒写
    **永久**挡在门外。一次坏嵌入 = 这张表从此写不进去。
    ⚠️ 与「embed 抛异常」那一格的区别是承重的: 那个抛, 这个**成功返回**。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    cls = {
        "bad_dim": real_lancedb.bad_dim_cls,
        "string_embed": real_lancedb.string_embed_cls,
    }[variant]
    monkeypatch.setattr(real_lancedb.module, "LanceDBClient", cls)

    status_ = await _write_lancedb(_rationale(f"0011-{variant}"), f"rec-p1a-0011-{variant}")

    _assert_factory_anchor(real_lancedb)
    assert status_.success is False, f"错误维度的向量被写进去了: {status_!r}"
    assert "refused" in (status_.error or "").lower()
    assert expect_fragment in (status_.error or "").lower(), f"错误串未点明维度问题: {status_.error!r}"

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE not in db.table_names(), f"拒写路径却建出了表（而且是坏维度的）: {db.table_names()}"


async def test_lancedb_real_write_appends_beyond_default_pagination(
    real_lancedb,
):
    """G1⑫ **上游已修**: 目标表排在默认分页之外时, 第二次追加仍然**真的追加进去**。

    本门是 P1-A 那条 ``…_second_append_beyond_pagination_fails_loudly`` 的**翻转版**,
    按它自己写下的指令改造 —— 它的失败消息原文是:

        「若哪天它真的成功了, 说明上游已修, 请删掉本门并把 G1② 的 append-only
         覆盖到分页外场景」

    上游限制(P1-A 登记): ``add_documents`` 内部用默认分页的 ``table_names()`` 判存在性,
    目标表排在第 11 张之后时误走 ``create_table``, 撞上同名表报错 ⇒ 返回 0 ⇒ 调用方侧
    报响亮失败。当时卡文硬边界不许改 ``add_documents``, 所以只能把「坏了会说」钉住。

    **CARD-LANCE-INDEX-DELETE-CONTRACT (BATCH-2026-09-18-第十五批) 的 (e3) 修掉了它**:
    ``add_documents`` 的两处存在性判断改走 ``_all_table_names()``。于是本门从「证明坏了会说」
    升级成 G1② append-only 在**分页外**的正向覆盖 —— 与
    ``test_lancedb_real_write_is_append_only`` 同判据(同一条 edge ⇒ 2 行),
    只是把目标表推到默认分页之外。

    ⚠️ 两条前提断言都不能删: 没有 ``len(db.table_names()) == 10`` 与「目标表不在默认分页内」,
    本门就退化成 ``test_lancedb_real_write_is_append_only`` 的重复, 一点分页面也没覆盖到。
    """
    from app.api.v1.endpoints.edges import _write_lancedb

    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    for i in range(11):
        db.create_table(
            f"aa_{i:02d}",
            data=[{"doc_id": "x", "content": "c", "vector": [0.1] * 8, "doc_type": "t"}],
        )
    assert len(db.table_names()) == 10, "分页前提不成立"

    shared = _rationale("0012")
    first = await _write_lancedb(shared, "rec-p1a-0012a")
    assert first.success is True, f"第一次写（建表）应成功: {first!r}"

    second = await _write_lancedb(shared, "rec-p1a-0012b")
    assert second.success is True, (
        f"分页外的第二次追加仍然失败 —— 上游 add_documents 的存在性判断又退回默认分页了? {second!r}"
    )

    after = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert _EXPECTED_TABLE not in set(after.table_names()), (
        "前提失效: 目标表竟落在默认分页**之内**, 本门覆盖不到分页外场景, 需重新校准"
    )
    table = after.open_table(_EXPECTED_TABLE)
    assert table.count_rows() == 2, f"append-only 期望 2 行, 实得 {table.count_rows()}"
    rows = table.to_arrow().to_pylist()
    assert sorted(r["doc_id"] for r in rows) == ["rec-p1a-0012a", "rec-p1a-0012b"], (
        f"doc_id 集合不符: {sorted(r['doc_id'] for r in rows)}"
    )
    # 承重: 两行属于**同一条 edge** ⇒ 与 G1② 同一条主张, 只是覆盖面推到分页外
    edge_ids = {json.loads(r["metadata_json"])["edge_id"] for r in rows}
    assert edge_ids == {shared.edge_id}, f"两行不属于同一条 edge: {edge_ids}"


class _RowsNeo4jStub:
    """端点门用的 Neo4j 侧 stub: 要么正常返回指定行, 要么抛指定异常（形态同 t5b）。"""

    def __init__(self, rows=None, exc_factory=None):
        self.calls = 0
        self._rows = rows
        self._exc_factory = exc_factory

    async def run_query(self, query, **params):
        self.calls += 1
        if self._exc_factory is not None:
            raise self._exc_factory()
        return self._rows if self._rows is not None else []


@pytest.mark.parametrize(
    "neo4j_ok,expected_status",
    [(True, 200), (False, 207)],
    ids=["neo4j-ok-200", "neo4j-down-207"],
)
def test_lancedb_real_write_via_endpoint(real_lancedb, monkeypatch, valid_rationale_payload, neo4j_ok, expected_status):
    """G1④ 端点级: POST 之后**表里真有行**, 且 HTTP 码与两侧结果一致。

    ⛔ 207 这一格是本卡的要害: 缺陷期它同样返 207, 但 LanceDB 那一半**什么都没写** ——
    「部分成功已保留」是一句不实陈述。现在 207 意味着 LanceDB 半边确实落了盘。

    ⚠️ 本门的 payload **不带 vault_id**: ``resolve_vault_group_id`` 对「显式 vault_id 与
    进程 active vault 不一致」会 409(fail-closed), 而 active vault 随环境变。于是表名由
    工厂真造出来的那个客户端自己 ``resolve_table_name`` 得出 —— 断言的仍是一张**具体的**
    表, 只是名字不写死。
    """
    import app.api.v1.endpoints.edges as edges_module
    import app.clients.neo4j_client as neo4j_module
    from neo4j.exceptions import ServiceUnavailable

    factory_calls: list = []

    def _factory(vault_id):
        factory_calls.append(vault_id)
        return real_lancedb.cls(vault_id=vault_id)

    # raising=True: 缺陷期 edges 模块上没有 _lancedb_client_for, 这里直接报错 = 改前红
    monkeypatch.setattr(edges_module, "_lancedb_client_for", _factory)

    stub = _RowsNeo4jStub(
        rows=[{"record_id": "whatever"}] if neo4j_ok else None,
        exc_factory=None if neo4j_ok else (lambda: ServiceUnavailable("P1A-NEO4J-DOWN")),
    )

    def _fake_get_neo4j_client(*args, **kwargs):
        return stub

    monkeypatch.setattr("app.clients.neo4j_client.get_neo4j_client", _fake_get_neo4j_client)
    if neo4j_module.get_neo4j_client is not _fake_get_neo4j_client:
        pytest.fail("注入锚失败: 源模块 get_neo4j_client 未被替换, 已立即停跑")

    payload = dict(valid_rationale_payload)
    payload.pop("vault_id", None)

    app = FastAPI()
    app.include_router(edges_module.edges_router, prefix="/api/v1/edges")
    resp = TestClient(app, raise_server_exceptions=False).post("/api/v1/edges/record-rationale", json=payload)

    # ── 注入锚（承重, 0→1）: 工厂确实被端点调到了 ──
    assert factory_calls == [payload.get("vault_id")], (
        f"注入锚失败: _lancedb_client_for 调用记录 {factory_calls!r} —— 端点没走本工厂"
    )
    assert stub.calls >= 1, f"注入锚失败: Neo4j stub 一次都没被调用 (calls={stub.calls})"
    _assert_factory_anchor(real_lancedb)

    assert resp.status_code == expected_status, f"期望 {expected_status}, 实得 {resp.status_code}: {resp.text[:400]}"
    body = resp.json()
    assert body["lancedb_status"]["success"] is True, f"LanceDB 侧应成功: {body['lancedb_status']!r}"

    # ── 核心: 表里真有这一行（不用 success 当写成功判据）──
    written_client = real_lancedb.created[-1]
    expected_table = written_client.resolve_table_name(_EDGE_TABLE)
    db = real_lancedb.lancedb.connect(str(real_lancedb.db_dir))
    assert expected_table in db.table_names(), (
        f"表 {expected_table!r} 不存在 ⇒ 端点报了 {resp.status_code} 但 LanceDB 侧零写入。"
        f"库内表: {db.table_names()}; lancedb_status={body['lancedb_status']!r}"
    )
    table = db.open_table(expected_table)
    assert table.count_rows() == 1, f"期望恰 1 行, 实得 {table.count_rows()}"
    assert table.to_arrow().to_pylist()[0]["doc_id"] == body["record_id"], (
        "表里的 doc_id 与响应体的 record_id 不一致 —— 写的不是这一次的记录"
    )
