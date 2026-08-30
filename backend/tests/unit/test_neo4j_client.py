"""
Unit tests for Neo4jClient with AsyncGraphDatabase driver.

Story 30.2: Neo4jClient真实驱动实现
- AC-1: AsyncGraphDatabase connection replaces JSON storage
- AC-2: Connection pool (50 connections, 30s timeout, 3600s lifetime)
- AC-3: JSON Fallback mode preserved (NEO4J_ENABLED=false)
- AC-4: Write latency < 200ms P95
- AC-5: Retry mechanism (3 times, exponential backoff 1s, 2s, 4s)

[Source: docs/stories/30.2.story.md]
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.clients.neo4j_client import (
    Neo4jClient,
    get_neo4j_client,
    reset_neo4j_client,
)


class TestNeo4jClientInitialization:
    """Test Neo4jClient initialization modes."""

    def test_init_with_default_params(self):
        """Test initialization with default parameters."""
        client = Neo4jClient()

        assert client._uri == "bolt://localhost:7687"
        assert client._user == "neo4j"
        assert client._database == "neo4j"
        assert client._max_connection_pool_size == 50
        assert client._connection_acquisition_timeout == 30
        assert client._max_connection_lifetime == 3600
        assert client._retry_attempts == 3
        assert client._retry_delay_base == 1.0
        assert client._initialized is False
        assert client._use_json_fallback is False

    def test_init_with_json_fallback(self):
        """Test initialization with JSON fallback mode."""
        client = Neo4jClient(use_json_fallback=True)

        assert client._use_json_fallback is True
        assert client.is_fallback_mode is True
        assert client.enabled is False  # enabled=False when in fallback

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters - AC-2."""
        client = Neo4jClient(
            uri="bolt://custom:7687",
            user="custom_user",
            password="custom_pass",
            database="custom_db",
            max_connection_pool_size=100,
            connection_acquisition_timeout=60,
            max_connection_lifetime=7200,
            retry_attempts=5,
            retry_delay_base=2.0,
            retry_max_delay=20.0,
        )

        assert client._uri == "bolt://custom:7687"
        assert client._user == "custom_user"
        assert client._password == "custom_pass"
        assert client._database == "custom_db"
        assert client._max_connection_pool_size == 100
        assert client._connection_acquisition_timeout == 60
        assert client._max_connection_lifetime == 7200
        assert client._retry_attempts == 5
        assert client._retry_delay_base == 2.0
        assert client._retry_max_delay == 20.0

    def test_stats_property(self):
        """Test stats property returns correct structure."""
        client = Neo4jClient(use_json_fallback=True)
        stats = client.stats

        assert "enabled" in stats
        assert "initialized" in stats
        assert "mode" in stats
        assert "metrics" in stats
        assert stats["mode"] == "JSON_FALLBACK"


def _json_fallback_scope() -> str:
    """CARD-G4-1a: JSON 降级模式下记录的归属 = 当前读作用域。

    降级路径与 Cypher 路径同一套 scope 语义（Codex round-2 反证：不过滤等于
    "把 Neo4j 弄挂就能绕过封堵"）。生产写侧本来就落 group_id，fixture 对齐。
    """
    from app.core.vault_scope import current_group_id

    return current_group_id()


def scope_physical(group_id: str) -> str:
    """逻辑 D16 组 → 物理 `vault__` 组 (库内/JSON 内的落盘形态)。"""
    from app.graphiti.group_id_compat import to_physical_group_id

    return to_physical_group_id(group_id)


async def _unreachable_run_query(*_args, **_kwargs):
    """作用域解析失败时**不得**发出查询 —— 发出即说明 fail-closed 在查询之后。"""
    raise AssertionError("scope 解析失败后仍发出了查询 (fail-closed 位置错误)")


class TestNeo4jClientJsonFallback:
    """Test Neo4jClient JSON fallback mode - AC-3."""

    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """Create temporary storage path for tests."""
        return tmp_path / "test_neo4j_memory.json"

    @pytest.mark.asyncio
    async def test_json_fallback_initialization(self, temp_storage_path):
        """Test JSON fallback mode initialization creates storage file."""
        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)

        result = await client.initialize()

        assert result is True
        assert client._initialized is True
        assert temp_storage_path.exists()

    @pytest.mark.asyncio
    async def test_json_fallback_loads_existing_data(self, temp_storage_path):
        """Test JSON fallback mode loads existing data."""
        # Create existing data
        existing_data = {
            "users": [{"id": "user-1", "created_at": "2024-01-01T00:00:00"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": [],
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        assert len(client._data["users"]) == 1
        assert client._data["users"][0]["id"] == "user-1"

    @pytest.mark.asyncio
    async def test_create_learning_relationship_json_fallback(self, temp_storage_path):
        """Test creating learning relationship in JSON fallback mode."""
        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        result = await client.create_learning_relationship(
            user_id="test-user",
            concept="Test Concept",
            score=85,
            group_id="vault:testvault",
        )

        assert result is True
        assert len(client._data["users"]) == 1
        assert len(client._data["concepts"]) == 1
        assert len(client._data["relationships"]) == 1

        rel = client._data["relationships"][0]
        assert rel["user_id"] == "test-user"
        assert rel["concept_name"] == "Test Concept"
        assert rel["last_score"] == 85
        # G2-3 (W1 镜像): 记录携带物理化 group_id
        assert rel["group_id"] == "vault__testvault"

    @pytest.mark.asyncio
    async def test_create_learning_relationship_dual_group_no_merge(self, temp_storage_path):
        """G2-3 (W1 镜像): JSON 层同名概念双组独立, 不跨组合并/覆盖."""
        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        ok_a = await client.create_learning_relationship(user_id="u1", concept="Shared", score=80, group_id="vault:va")
        ok_b = await client.create_learning_relationship(user_id="u1", concept="Shared", score=60, group_id="vault:vb")
        assert ok_a and ok_b

        # 双键: 同名概念两条记录, 各归其组
        concepts = [c for c in client._data["concepts"] if c["name"] == "Shared"]
        assert sorted(c["group_id"] for c in concepts) == ["vault__va", "vault__vb"]

        rels = [r for r in client._data["relationships"] if r["concept_name"] == "Shared"]
        assert sorted((r["group_id"], r["last_score"]) for r in rels) == [
            ("vault__va", 80),
            ("vault__vb", 60),
        ]

    @pytest.mark.asyncio
    async def test_create_learning_relationship_fail_closed_no_group(self, temp_storage_path, caplog):
        """G2-3 fail-closed 门: group 不可解析 → 拒写返 False, 不抛异常 (防 500)."""
        import logging as _logging

        from app.core.subject_config import _current_subject_id

        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        token = _current_subject_id.set("general")  # 无 vault 上下文
        try:
            with caplog.at_level(_logging.ERROR):
                result = await client.create_learning_relationship(
                    user_id="test-user", concept="No Group Concept", score=85
                )
        finally:
            _current_subject_id.reset(token)

        assert result is False
        assert len(client._data["concepts"]) == 0
        assert len(client._data["relationships"]) == 0
        assert any("fail-closed" in r.message for r in caplog.records)

    @pytest.mark.parametrize(
        "raw",
        [
            None,
            "",
            "   ",  # 空白串: 曾被 canonical_group_id 静默映射成 vault__default
            "\t",
            "vault:",  # 裸前缀: 曾产出空后缀的 vault__ 垃圾组
            "vault:  ",  # 空白 vault 段: 曾产出 punycode 垃圾
        ],
    )
    def test_group_resolution_rejects_degenerate_inputs(self, raw):
        """G2-3 W3 边界门: 退化输入不得静默降级 DEFAULT 或产垃圾组.

        2026-08-28 边界实测发现: 空白串走 canonical_group_id 会静默变成
        ``vault__default`` (正是本卡禁止的静默降级); ``"vault:"`` 会产出
        空后缀的 ``vault__``。两者都必须收敛为 None 交调用方 fail-closed。
        """
        from app.clients.neo4j_client import _resolve_physical_group_id
        from app.core.subject_config import _current_subject_id

        token = _current_subject_id.set("general")  # 排除 ContextVar 兜底
        try:
            assert _resolve_physical_group_id(raw) is None
        finally:
            _current_subject_id.reset(token)

    @pytest.mark.parametrize("raw", ["vault::x", "vault:::y"])
    def test_group_resolution_rejects_empty_segment(self, raw):
        """C1b (Codex round-2): 空段物理值 (vault____x) 必须拒绝.

        畸形输入 ``vault::x`` 物理化成 ``vault____x`` —— 段级校验按 ``__``
        切分, 任一段为空即判非法。
        """
        from app.clients.neo4j_client import _resolve_physical_group_id

        assert _resolve_physical_group_id(raw) is None

    def test_group_resolution_blank_explicit_does_not_fall_back(self):
        """C1a (Codex round-2): 显式空白 group_id 不得回退推导链落到别的 vault.

        空白是调用方 bug —— 若静默推导, 写入会落到 ContextVar 指向的另一个
        vault (错误归属), 且日志里看不出发生过降级。
        """
        from app.clients.neo4j_client import _resolve_physical_group_id
        from app.core.subject_config import _current_subject_id

        token = _current_subject_id.set("vault:othervault")
        try:
            # None 走推导 (合法)
            assert _resolve_physical_group_id(None) == "vault__othervault"
            # 显式空白 → fail-closed, 不得变成 othervault
            assert _resolve_physical_group_id("   ") is None
            # C1 round-3: 空串与空白串口径必须一致 (原实现空串因假值漏进推导链)
            assert _resolve_physical_group_id("") is None
        finally:
            _current_subject_id.reset(token)

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("vault:cs_61b", "vault__cs_61b"),
            (" vault:cs_61b ", "vault__cs_61b"),  # 两侧空白被 strip
            ("vault__cs_61b", "vault__cs_61b"),  # 幂等
            ("vault:a:b", "vault__a__b"),  # 二级 group 合法 (段均非空)
        ],
    )
    def test_group_resolution_accepts_valid_inputs(self, raw, expected):
        """合法输入必须原样物理化 —— 校验不能宽到把正常写路径也拒掉."""
        from app.clients.neo4j_client import _resolve_physical_group_id

        assert _resolve_physical_group_id(raw) == expected

    @pytest.mark.asyncio
    async def test_scoped_write_methods_fail_closed_no_group(self, temp_storage_path, caplog):
        """G2-3 W2/W5 fail-closed: delete/update 无 group scope → 拒执行且目标无损.

        鉴别力设计 (对抗审查 2026-08-28 整改): 对不存在的 ID 断言 False 是
        空转 —— JSON fallback 对任何未知 ID 本来就返 False, 把 guard 整体
        删掉测试照样绿。故先用显式组建好**真实**关联, 再断言无 scope 调用
        既返 False、目标记录又原样存活 (拒绝 ≠ not-found)。
        """
        import logging as _logging

        from app.core.subject_config import _current_subject_id

        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        assert await client.create_canvas_association(
            association_id="assoc-live",
            source_canvas="src.canvas",
            target_canvas="dst.canvas",
            association_type="related",
            confidence=1.0,
            group_id="vault:testvault",
        )
        before = json.loads(json.dumps(client._data["canvas_associations"]))

        token = _current_subject_id.set("general")  # 无 vault 上下文
        try:
            with caplog.at_level(_logging.ERROR):
                assert await client.delete_edge_relationship("edge-1") is False
                # 真实存在的目标: 拒绝必须表现为"返 False 且记录毫发无损"
                assert await client.update_canvas_association("assoc-live", confidence=0.5) is False
                assert await client.delete_canvas_association("assoc-live") is False
        finally:
            _current_subject_id.reset(token)

        assert client._data["canvas_associations"] == before, "fail-closed path mutated the store"
        assert sum("fail-closed" in r.message for r in caplog.records) >= 3

    @pytest.mark.asyncio
    async def test_get_review_suggestions_json_fallback(self, temp_storage_path):
        """Test getting review suggestions in JSON fallback mode."""
        # Create data with past due review
        past_date = "2024-01-01T00:00:00"
        existing_data = {
            "users": [{"id": "user-1", "created_at": "2024-01-01T00:00:00"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": [
                {
                    "id": "rel-1",
                    "user_id": "user-1",
                    "concept_id": "concept-1",
                    "concept_name": "Test Concept",
                    "timestamp": past_date,
                    "last_score": 80,
                    "next_review": past_date,
                    "review_count": 1,
                    # CARD-G4-1a (2026-08-30): JSON 降级模式的复习建议现在也按
                    # 作用域过滤 (Codex round-2: 否则"把 Neo4j 弄挂"就能绕过封
                    # 堵)。生产写侧 create_learning_relationship 的 JSON 分支本
                    # 来就落物理化 group_id, fixture 与之对齐。
                    "group_id": _json_fallback_scope(),
                }
            ],
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        suggestions = await client.get_review_suggestions("user-1")

        assert len(suggestions) == 1
        assert suggestions[0]["concept"] == "Test Concept"
        assert suggestions[0]["priority"] == "high"  # review_count < 3

    @pytest.mark.asyncio
    async def test_get_concept_history_json_fallback(self, temp_storage_path):
        """Test getting concept history in JSON fallback mode."""
        existing_data = {
            "users": [{"id": "user-1"}],
            "concepts": [{"id": "concept-1", "name": "Test Concept"}],
            "relationships": [
                {
                    "id": "rel-1",
                    "user_id": "user-1",
                    "concept_id": "concept-1",
                    "concept_name": "Test Concept",
                    "timestamp": "2024-01-01T00:00:00",
                    "last_score": 90,
                    "review_count": 3,
                    # CARD-G4-1b (2026-08-31): `_handle_query_history` 升为
                    # fail-closed 后, 无归属的记录不再对任何作用域可见 —— 与
                    # 生产写侧 (JSON 分支恒落物理化 group_id) 对齐。
                    "group_id": _json_fallback_scope(),
                }
            ],
        }
        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(existing_data, f)

        client = Neo4jClient(use_json_fallback=True, storage_path=temp_storage_path)
        await client.initialize()

        history = await client.get_concept_history("concept-1", user_id="user-1")

        assert len(history) == 1
        assert history[0]["concept"] == "Test Concept"
        assert history[0]["score"] == 90


class TestNeo4jClientDriver:
    """Test Neo4jClient with real Neo4j driver - AC-1, AC-2."""

    @pytest.mark.asyncio
    async def test_driver_initialization_success(self):
        """Test successful driver initialization with mocked Neo4j."""
        client = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="test_password")

        # Mock the AsyncGraphDatabase.driver
        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            result = await client.initialize()

            assert result is True
            assert client._initialized is True
            assert client._use_json_fallback is False

            # Verify driver was created with correct pool config - AC-2
            mock_agd.driver.assert_called_once()
            call_kwargs = mock_agd.driver.call_args[1]
            assert call_kwargs["max_connection_pool_size"] == 50
            assert call_kwargs["connection_acquisition_timeout"] == 30
            assert call_kwargs["max_connection_lifetime"] == 3600

    @pytest.mark.asyncio
    async def test_driver_initialization_fallback_on_failure(self, tmp_path):
        """Test fallback to JSON when Neo4j connection fails - AC-3."""
        storage_path = tmp_path / "fallback_test.json"
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrong_password",
            storage_path=storage_path,
        )

        # Mock driver creation to raise AuthError
        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            from neo4j.exceptions import AuthError

            mock_agd.driver.side_effect = AuthError("Authentication failed")

            result = await client.initialize()

            assert result is True  # Should succeed via fallback
            assert client._use_json_fallback is True
            assert storage_path.exists()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True when Neo4j is healthy."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            await client.initialize()
            result = await client.health_check()

            assert result is True
            assert client._health_status is True
            assert client._last_health_check is not None

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False when Neo4j is unhealthy."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # Now make health check fail
            mock_driver.verify_connectivity = AsyncMock(side_effect=Exception("Connection lost"))

            result = await client.health_check()

            assert result is False
            assert client._health_status is False

    @pytest.mark.asyncio
    async def test_health_check_json_fallback(self, tmp_path):
        """Test health check always returns True in JSON fallback mode."""
        storage_path = tmp_path / "health_test.json"
        client = Neo4jClient(use_json_fallback=True, storage_path=storage_path)
        await client.initialize()

        result = await client.health_check()

        assert result is True
        assert client._health_status is True


class TestNeo4jClientRetry:
    """Test Neo4jClient retry mechanism - AC-5."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry mechanism on transient errors - AC-5."""
        client = Neo4jClient(
            retry_attempts=3,
            retry_delay_base=0.1,  # Fast retries for test
            retry_max_delay=1.0,
        )

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)

            # Create mock result
            mock_result = AsyncMock()
            mock_result.data = AsyncMock(return_value=[{"count": 1}])

            from neo4j.exceptions import TransientError

            call_count = [0]

            async def mock_run(query, params):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise TransientError("Transient error")
                return mock_result

            # Create async context manager mock for session
            mock_session = AsyncMock()
            mock_session.run = mock_run

            # Session returns an async context manager
            async def session_context_manager(*args, **kwargs):
                return mock_session

            mock_driver.session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )

            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # This should retry and eventually succeed
            result = await client.run_query("RETURN 1 as count")

            assert call_count[0] == 3  # Failed twice, succeeded on third try
            assert result == [{"count": 1}]

    @pytest.mark.asyncio
    async def test_fallback_after_max_retries(self, tmp_path):
        """Test fallback to JSON after max retries exhausted."""
        storage_path = tmp_path / "retry_fallback.json"
        client = Neo4jClient(retry_attempts=2, retry_delay_base=0.1, storage_path=storage_path)

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_driver.close = AsyncMock()

            from neo4j.exceptions import ServiceUnavailable

            # Create async context manager mock for session that always fails
            mock_session = AsyncMock()
            mock_session.run = AsyncMock(side_effect=ServiceUnavailable("Service down"))

            mock_driver.session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )

            mock_agd.driver.return_value = mock_driver

            await client.initialize()

            # Run query that will fail and trigger fallback
            # Use a query that JSON fallback can handle
            result = await client.run_query(
                "MERGE (u:User {id: $userId}) MERGE (c:Concept {name: $concept})",
                userId="test-user",
                concept="Test Concept",
            )

            # Should have fallen back to JSON mode
            assert client._use_json_fallback is True


class TestNeo4jClientMetrics:
    """Test Neo4jClient performance metrics - AC-4."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, tmp_path):
        """Test query metrics are tracked correctly."""
        storage_path = tmp_path / "metrics_test.json"
        client = Neo4jClient(use_json_fallback=True, storage_path=storage_path)
        await client.initialize()

        # Execute a few queries
        await client.create_learning_relationship("user-1", "concept-1", 80, group_id="vault:testvault")
        await client.create_learning_relationship("user-1", "concept-2", 90, group_id="vault:testvault")

        metrics = client._metrics

        assert metrics["total_queries"] == 2
        assert metrics["successful_queries"] == 2
        assert metrics["failed_queries"] == 0
        assert metrics["total_latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_latency_warning(self, tmp_path, caplog):
        """Test warning is logged when latency exceeds 200ms - AC-4."""
        import logging

        storage_path = tmp_path / "latency_test.json"
        client = Neo4jClient(use_json_fallback=True, storage_path=storage_path)
        await client.initialize()

        # Mock time.perf_counter to simulate slow query
        original_perf_counter = time.perf_counter
        call_count = [0]

        def mock_perf_counter():
            call_count[0] += 1
            if call_count[0] == 1:
                return 0  # Start time
            return 0.25  # 250ms later (exceeds 200ms threshold)

        with patch("app.clients.neo4j_client.time.perf_counter", mock_perf_counter):
            with caplog.at_level(logging.WARNING):
                await client.create_learning_relationship("user-1", "concept-1", 80, group_id="vault:testvault")

        # Check warning was logged
        assert any("exceeded 200ms" in record.message for record in caplog.records)


class TestNeo4jClientSingleton:
    """Test Neo4jClient singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_neo4j_client()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_neo4j_client()

    def test_get_neo4j_client_singleton(self):
        """Test get_neo4j_client returns singleton."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.neo4j_enabled = False  # Force JSON fallback
            mock_settings.neo4j_uri = "bolt://localhost:7687"
            mock_settings.neo4j_user = "neo4j"
            mock_settings.neo4j_password = ""
            mock_settings.neo4j_database = "neo4j"
            mock_settings.neo4j_max_connection_pool_size = 50
            mock_settings.neo4j_connection_timeout = 30
            mock_settings.neo4j_max_connection_lifetime = 3600
            mock_settings.neo4j_retry_attempts = 3
            mock_settings.neo4j_retry_delay_base = 1.0
            mock_settings.neo4j_retry_max_delay = 10.0

            client1 = get_neo4j_client()
            client2 = get_neo4j_client()

            assert client1 is client2

    def test_reset_neo4j_client(self):
        """Test reset_neo4j_client clears singleton."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.neo4j_enabled = False
            mock_settings.neo4j_uri = "bolt://localhost:7687"
            mock_settings.neo4j_user = "neo4j"
            mock_settings.neo4j_password = ""
            mock_settings.neo4j_database = "neo4j"
            mock_settings.neo4j_max_connection_pool_size = 50
            mock_settings.neo4j_connection_timeout = 30
            mock_settings.neo4j_max_connection_lifetime = 3600
            mock_settings.neo4j_retry_attempts = 3
            mock_settings.neo4j_retry_delay_base = 1.0
            mock_settings.neo4j_retry_max_delay = 10.0

            client1 = get_neo4j_client()
            reset_neo4j_client()
            client2 = get_neo4j_client()

            assert client1 is not client2


class TestNeo4jClientCleanup:
    """Test Neo4jClient cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_json_fallback(self, tmp_path):
        """Test cleanup in JSON fallback mode."""
        storage_path = tmp_path / "cleanup_test.json"
        client = Neo4jClient(use_json_fallback=True, storage_path=storage_path)
        await client.initialize()

        await client.cleanup()

        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_cleanup_neo4j_driver(self):
        """Test cleanup closes Neo4j driver."""
        client = Neo4jClient()

        with patch("app.clients.neo4j_client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock(return_value=None)
            mock_driver.close = AsyncMock()
            mock_agd.driver.return_value = mock_driver

            await client.initialize()
            await client.cleanup()

            mock_driver.close.assert_called_once()
            assert client._initialized is False


# =============================================================================
# CARD-G4-1b (BATCH-2026-08-31-第七批) — client 层读收口单测
#
# 关联族三方法 (`get_canvas_associations` / `get_canvas_concepts` /
# `find_common_concepts`) 是**双料僵尸**: 生产零调用方 + 现网零数据。按卡文
# (d) 只做契约收口 + 单测, **不**往 7692 造行为门种子、**不**新增消费方
# (G-PIPE 处置登记另立卡)。因此这一族的判据分两层:
#   · Cypher 侧 —— 拦截真实发出的查询, 断言**每个 alias** 都带上了
#     `read_group_filter` 的等值 OR 前缀片段, 且 scope 参数确实绑定;
#   · JSON 镜像侧 —— 真实行为门 (镜像本来就不需要 Neo4j): 两个 vault 的
#     同名 canvas 数据互不可见, 且本 vault 的子组数据可见 (保召回)。
#
# 另有两条与作用域无关但同批的结构门: 关键词路由不变量 (误路由面的静态锁)
# 与 fail-closed 痕迹。
# =============================================================================


class TestG41bReadScopeContract:
    """CARD-G4-1b: 5 读方法 + 4 JSON 镜像的作用域收口。"""

    @pytest.fixture
    def scope(self):
        return _json_fallback_scope()

    @pytest.fixture
    def other_scope(self):
        """与当前作用域**同前缀但不同 vault** 的另一个组。

        故意取 `<scope>_other` 而不是随便一个名字: 它能同时锁住"裸前缀误配"
        (若过滤写成不带 `__` 定界符的 startswith, `vault__x` 会吃掉
        `vault__x_other`, 本组数据就会串进来)。
        """
        return f"{scope_physical(_json_fallback_scope())}_other"

    # ── Cypher 侧: 逐 alias 过滤片段 ────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,kwargs,branch_aliases",
        [
            # `branch_aliases`: **按 UNION 分段**给出每段各自引入的 alias。
            # ⚠️ 不能把所有 alias 摊平成一个集合再查子串 —— `get_canvas_concepts`
            # 的两个 UNION 分支都有一个叫 `n` 的 alias (分支1=Node, 分支2=
            # LearningNode), 摊平后删掉分支1的 `n` 过滤, 分支2 的那份仍然满足
            # 子串断言, 门照绿。变异负控 `canvas-concepts-drop-n` 实测抓到过这个
            # 死门 —— 判据的粒度必须与缺陷的粒度对齐。
            ("get_canvas_associations", {"canvas_path": "a.canvas"}, (("source", "r", "target"),)),
            ("get_canvas_concepts", {"canvas_path": "a.canvas"}, (("c", "cn", "n"), ("c", "n", "concept"))),
            (
                "find_common_concepts",
                {"canvas1": "a.canvas", "canvas2": "b.canvas"},
                (("c1", "cn1", "n1", "c2", "cn2", "n2"),),
            ),
            ("get_all_recent_episodes", {}, (("r", "c"),)),
            ("get_concept_history", {"concept_id": "x"}, (("r", "c"),)),
        ],
    )
    async def test_cypher_filters_every_alias(self, tmp_path, method, kwargs, branch_aliases):
        from app.core.vault_scope import read_group_filter

        client = Neo4jClient(use_json_fallback=False, storage_path=tmp_path / "s.json")
        client._initialized = True
        captured = {}

        async def _capture(query, **params):
            captured["query"] = query
            captured["params"] = params
            return []

        client.run_query = _capture
        await getattr(client, method)(**kwargs)

        segments = [seg for seg in captured["query"].split("UNION")]
        assert len(segments) == len(branch_aliases), (
            f"{method}: UNION 分段数与期望不符 ({len(segments)} vs "
            f"{len(branch_aliases)}) —— 查询结构变了, 本门的分段判据已失真"
        )
        for seg, aliases in zip(segments, branch_aliases):
            for alias in aliases:
                assert read_group_filter(alias) in seg, (
                    f"{method}: 分支内 alias {alias!r} 缺 group 过滤 (R1 每个 alias 逐一过滤)\n{seg}"
                )
        assert captured["params"].get("group_id"), f"{method}: scope 参数未绑定"
        assert captured["params"].get("group_prefix", "").endswith("__"), (
            f"{method}: 前缀锚必须带 `__` 定界符, 否则 vault__x 会吃掉 vault__xy"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,kwargs",
        [
            ("get_canvas_associations", {"canvas_path": "a.canvas"}),
            ("get_canvas_concepts", {"canvas_path": "a.canvas"}),
            ("find_common_concepts", {"canvas1": "a.canvas", "canvas2": "b.canvas"}),
            ("get_all_recent_episodes", {}),
            ("get_concept_history", {"concept_id": "x"}),
        ],
    )
    async def test_blank_scope_is_refused_not_derived(self, tmp_path, method, kwargs):
        """显式空白串 = 调用方 bug, 不得静默推导到另一个作用域 (C1 口径)。"""
        from app.core.vault_scope import VaultScopeUnresolved

        client = Neo4jClient(use_json_fallback=False, storage_path=tmp_path / "s.json")
        client._initialized = True
        client.run_query = _unreachable_run_query

        with pytest.raises(VaultScopeUnresolved):
            await getattr(client, method)(group_id="   ", **kwargs)

    # ── JSON 镜像侧: 真实可见面行为门 ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_associations_json_mirror_is_scoped(self, tmp_path, scope, other_scope):
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "a.json")
        await client.initialize()
        sub = f"{scope_physical(scope)}__board_x"  # 本 vault 的白板子组
        client._data["canvas_associations"] = [
            {
                "association_id": "mine-root",
                "source_canvas": "a.canvas",
                "target_canvas": "b.canvas",
                "association_type": "t",
                "created_at": "2026-01-01",
                "group_id": scope_physical(scope),
            },
            {
                "association_id": "mine-sub",
                "source_canvas": "a.canvas",
                "target_canvas": "b.canvas",
                "association_type": "t",
                "created_at": "2026-01-02",
                "group_id": sub,
            },
            {
                "association_id": "theirs",
                "source_canvas": "a.canvas",
                "target_canvas": "b.canvas",
                "association_type": "t",
                "created_at": "2026-01-03",
                "group_id": other_scope,
            },
        ]

        got = {a["association_id"] for a in await client.get_canvas_associations(canvas_path="a.canvas")}
        assert got == {"mine-root", "mine-sub"}, f"保召回(子组)/零泄漏(他 vault) 至少一半红: {sorted(got)}"

    @pytest.mark.asyncio
    async def test_canvas_concepts_json_mirror_is_scoped(self, tmp_path, scope, other_scope):
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "c.json")
        await client.initialize()
        sub = f"{scope_physical(scope)}__board_x"
        client._data["relationships"] = [
            {
                "user_id": "u",
                "concept_name": "mine-root",
                "canvas_path": "shared.canvas",
                "group_id": scope_physical(scope),
            },
            {"user_id": "u", "concept_name": "mine-sub", "canvas_path": "shared.canvas", "group_id": sub},
            {"user_id": "u", "concept_name": "theirs", "canvas_path": "shared.canvas", "group_id": other_scope},
        ]

        got = set(await client.get_canvas_concepts("shared.canvas"))
        assert got == {"mine-root", "mine-sub"}, f"同名 canvas 在两个 vault 各有节点, 可见面不对: {sorted(got)}"

        # find_common_concepts 的两边必须取自同一个可见面 —— 否则"共同概念"
        # 会由跨 vault 的一侧凑出来。
        # ⚠️ 正向对照不可省 (Codex round-1 MEDIUM): 只有"跨 vault 应为空"这半,
        # 把 find_common 写死成 `return []` 也照样全绿。
        client._data["relationships"] += [
            # 他 vault 在 other.canvas 上也有 theirs → 若过滤失效, 交集会凑出它
            {"user_id": "u", "concept_name": "theirs", "canvas_path": "other.canvas", "group_id": other_scope},
            # 本 vault 在 other.canvas 上有 mine-root → 正向对照, 必须被算出来
            {
                "user_id": "u",
                "concept_name": "mine-root",
                "canvas_path": "other.canvas",
                "group_id": scope_physical(scope),
            },
        ]
        common = set(await client.find_common_concepts("shared.canvas", "other.canvas"))
        assert common == {"mine-root"}, f"缺失(正向对照红)/多出(跨 vault 凑出红): {sorted(common)}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["associations", "canvas_concepts"])
    async def test_mirror_path_match_is_exact_like_cypher(self, tmp_path, scope, method):
        """镜像的 canvas path 匹配必须与 Cypher **同为精确相等**。

        Codex round-1 HIGH: `_get_canvas_concepts_json_fallback` 原来用**子串
        包含**判断 path, 而 Cypher 是 `MATCH (c:Canvas {path: $canvasPath})`
        精确匹配 —— 于是 `x/a.canvas.bak` 会被 `a.canvas` 命中, 降级前后返回不同
        的概念集合。本门用"超串路径"当探针: 精确匹配下它必须**不**命中。
        这两个镜像按卡文 (d) 不做真库对拍, 一致性由本门与逐 alias 片段门保证。
        """
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "x.json")
        await client.initialize()
        gid = scope_physical(scope)
        target = "a.canvas"
        superstring = "x/a.canvas.bak"  # 含 target 作为子串, 但不等于它

        if method == "associations":
            client._data["canvas_associations"] = [
                {
                    "association_id": "sup",
                    "source_canvas": superstring,
                    "target_canvas": superstring,
                    "association_type": "t",
                    "created_at": "2026-01-01",
                    "group_id": gid,
                },
                {
                    "association_id": "exact",
                    "source_canvas": target,
                    "target_canvas": "b.canvas",
                    "association_type": "t",
                    "created_at": "2026-01-02",
                    "group_id": gid,
                },
            ]
            got = {a["association_id"] for a in await client.get_canvas_associations(canvas_path=target)}
            assert got == {"exact"}, f"path 匹配不是精确相等: {sorted(got)}"
        else:
            client._data["relationships"] = [
                {"user_id": "u", "concept_name": "from-superstring", "canvas_path": superstring, "group_id": gid},
                {"user_id": "u", "concept_name": "from-exact", "canvas_path": target, "group_id": gid},
            ]
            got = set(await client.get_canvas_concepts(target))
            assert got == {"from-exact"}, f"path 匹配不是精确相等: {sorted(got)}"

    @pytest.mark.asyncio
    async def test_all_recent_episodes_json_mirror_is_scoped(self, tmp_path, scope, other_scope):
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "e.json")
        await client.initialize()
        sub = f"{scope_physical(scope)}__board_x"
        client._data["relationships"] = [
            {"user_id": "u", "concept_name": "mine-root", "timestamp": "2026-01-01", "group_id": scope_physical(scope)},
            {"user_id": "u", "concept_name": "mine-sub", "timestamp": "2026-01-02", "group_id": sub},
            {"user_id": "u", "concept_name": "theirs", "timestamp": "2026-01-03", "group_id": other_scope},
            {"user_id": "u", "concept_name": "orphan", "timestamp": "2026-01-04"},
        ]

        got = {e["concept"] for e in await client.get_all_recent_episodes(limit=50)}
        assert got == {"mine-root", "mine-sub"}, f"无归属记录(orphan)/他 vault 记录不得进 episode 缓存: {sorted(got)}"

    # ── 关键词路由不变量 (误路由面的静态锁) ─────────────────────────────

    @pytest.mark.asyncio
    async def test_learned_query_shapes_all_route_to_a_scoped_handler(self, tmp_path):
        """三条 `MATCH…LEARNED` 形状的查询都落在**会过滤 scope** 的 handler 上。

        `_run_query_json_fallback` 按关键词派发。中途降级时:
          · 带 next_review → `_handle_query_reviews` (G4-1a 已 fail-closed)
          · 其余           → `_handle_query_history` (本卡升 fail-closed)
        这条门锁住"路由表没有第三条出口" —— 若有人新增一个不过滤的 handler
        或改了判据顺序, 降级时就会出现一条不过 scope 的读。
        """
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "r.json")
        await client.initialize()
        seen = []

        async def _spy(name):
            async def _inner(params):
                seen.append(name)
                return []

            return _inner

        client._handle_query_reviews = await _spy("reviews")
        client._handle_query_history = await _spy("history")

        await client._run_query_json_fallback(
            "MATCH (u:User)-[r:LEARNED]->(c:Concept) WHERE r.next_review < datetime()", {}
        )
        await client._run_query_json_fallback("MATCH (u:User)-[r:LEARNED]->(c:Concept) RETURN c.name", {})
        assert seen == ["reviews", "history"], seen

    @pytest.mark.asyncio
    async def test_handle_query_history_fail_closed(self, tmp_path, caplog):
        """无 scope → 空 + ERROR; 有 scope → 读得到 (正向对照防"恒空"假绿)。"""
        import logging

        scope = _json_fallback_scope()
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "h.json")
        await client.initialize()
        client._data["relationships"] = [
            {
                "user_id": "u",
                "concept_name": "mine",
                "concept_id": "cid",
                "timestamp": "2026-01-01",
                "group_id": scope_physical(scope),
            }
        ]

        with caplog.at_level(logging.ERROR):
            refused = await client._handle_query_history({"userId": "u"})
        assert refused == []
        assert any("G4-1b" in r.message for r in caplog.records)

        allowed = await client._handle_query_history({"userId": "u", "group_id": scope_physical(scope)})
        assert [r["concept"] for r in allowed] == ["mine"]

    @pytest.mark.asyncio
    async def test_degraded_date_filter_is_timezone_correct(self, tmp_path):
        """降级路径的日期过滤按**真实时序**比，不是按 ISO 字符串字典序。

        Codex round-3 Q3' 回归锁。探针刻意取"字典序与时序相反"的一对:
          记录  `2026-01-01T00:00:00+08:00`  = UTC 2025-12-31T16:00Z
          下界  `2026-01-01T00:00:00+00:00`  = UTC 2026-01-01T00:00Z
        字符串比较里 `+08:00` > `+00:00` ⇒ 记录被判为"在下界之后"而**错误放行**;
        转成 UTC 再比才知道它其实更早, 应当被排除。
        """
        scope = _json_fallback_scope()
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "tz.json")
        await client.initialize()
        client._data["relationships"] = [
            {
                "user_id": "u",
                "concept_name": "east",
                "concept_id": "e",
                "timestamp": "2026-01-01T00:00:00+08:00",
                "group_id": scope_physical(scope),
            },
            {
                "user_id": "u",
                "concept_name": "utc-later",
                "concept_id": "l",
                "timestamp": "2026-01-02T00:00:00+00:00",
                "group_id": scope_physical(scope),
            },
        ]
        params = {
            "userId": "u",
            "group_id": scope_physical(scope),
            "startDate": "2026-01-01T00:00:00+00:00",
        }
        got = {r["concept"] for r in await client._handle_query_history(params)}
        assert got == {"utc-later"}, f"日期过滤用了字典序而不是真实时序: {sorted(got)}"

    @pytest.mark.asyncio
    async def test_degraded_unparseable_date_bound_fails_closed(self, tmp_path, caplog):
        """畸形的日期边界 → 拒绝该条, 而不是"过滤悄悄消失、全都放行"。

        Codex round-4 Q3'' 回归锁。正向对照同时在场: 同一份数据换成**可解析**的
        边界时必须读得到 —— 否则"返回空"可能只是这条路径本来就读不出东西。
        """
        import logging

        scope = _json_fallback_scope()
        client = Neo4jClient(use_json_fallback=True, storage_path=tmp_path / "bad.json")
        await client.initialize()
        client._data["relationships"] = [
            {
                "user_id": "u",
                "concept_name": "mine",
                "concept_id": "m",
                "timestamp": "2026-06-01T00:00:00+00:00",
                "group_id": scope_physical(scope),
            },
        ]
        base = {"userId": "u", "group_id": scope_physical(scope)}

        with caplog.at_level(logging.ERROR):
            refused = await client._handle_query_history({**base, "startDate": "not-a-date"})
        assert refused == [], f"畸形边界下过滤被跳过, 记录被放行: {refused}"
        assert any("unparseable date bound" in r.message for r in caplog.records)

        allowed = await client._handle_query_history({**base, "startDate": "2026-01-01T00:00:00+00:00"})
        assert [r["concept"] for r in allowed] == ["mine"], (
            f"正向对照红: 可解析边界也读不到, 上面的空结果不能证明是 fail-closed {allowed}"
        )

    @pytest.mark.asyncio
    async def test_concept_id_match_is_id_or_name_on_both_sides(self, tmp_path):
        """点查按 id **或** name —— 生产写侧从不落 c.id, 只按 id 查等于恒空。

        Cypher 片段与 JSON 镜像必须同一套规则, 否则降级前后条数会变。
        """
        from app.clients.neo4j_client import _CONCEPT_ID_MATCH_CYPHER, _concept_id_matches

        assert "c.id = $conceptId" in _CONCEPT_ID_MATCH_CYPHER
        assert "c.name = $conceptId" in _CONCEPT_ID_MATCH_CYPHER
        # 两个字段**取不同值**, 才能分辨 OR 与 AND (Codex round-1 HIGH:
        # 取相同值的 fixture 杀不掉 `OR → AND` 变异)
        rec = {"concept_id": "X-id", "concept_name": "X"}
        assert _concept_id_matches(rec, "X-id"), "按 id 命中失效"
        assert _concept_id_matches(rec, "X"), "按 name 命中失效 —— 生产 Concept 没有 id, 只按 id 查会让端点恒空"
        assert _concept_id_matches({"concept_name": "X"}, "X"), "无 id 的生产形态命中失效"
        assert not _concept_id_matches({"concept_id": "Y", "concept_name": "Z"}, "X")
