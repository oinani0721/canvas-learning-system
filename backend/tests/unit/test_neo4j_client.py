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
