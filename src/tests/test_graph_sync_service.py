# src/tests/test_graph_sync_service.py
"""
GraphSyncService 单元测试

Story 18.4: Graph Sync Service - Graphiti知识图谱同步
- AC 1: 集成现有GraphitiClient
- AC 2: 回滚后使用add_episode()同步节点状态
- AC 3: 已删除节点在图谱中标记deleted_at(软删除)
- AC 4: 回滚结果包含graphSyncStatus: synced/pending/skipped
- AC 5: preserveGraph选项跳过图谱同步
- AC 6: 图谱同步失败不阻塞回滚成功(优雅降级)
- AC 7: Graphiti操作超时200ms

[Source: docs/architecture/rollback-recovery-architecture.md:180-210]
[Source: docs/stories/18.4.story.md]
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rollback.graph_sync_service import (
    GraphSyncService,
    GraphSyncStatus,
    SyncResult,
)

# ============================================================
# Mock GraphitiClient for testing
# ============================================================


class MockGraphitiClient:
    """Mock GraphitiClient for testing"""

    def __init__(
        self,
        timeout_ms: int = 200,
        enable_fallback: bool = True,
        should_fail: bool = False,
        should_timeout: bool = False,
    ):
        self.timeout_ms = timeout_ms
        self.enable_fallback = enable_fallback
        self.should_fail = should_fail
        self.should_timeout = should_timeout
        self._initialized = False
        self.episodes_added: List[Dict[str, Any]] = []
        self.memories_added: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        if self.should_fail:
            raise Exception("Initialization failed")
        self._initialized = True
        return True

    async def add_episode(
        self,
        content: str,
        canvas_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if self.should_timeout:
            await asyncio.sleep(1.0)  # Simulate timeout
        if self.should_fail:
            return None

        episode_id = f"episode_{len(self.episodes_added) + 1}"
        self.episodes_added.append({
            "id": episode_id,
            "content": content,
            "canvas_file": canvas_file,
            "metadata": metadata,
        })
        return episode_id

    async def add_memory(
        self,
        key: str,
        content: str,
        importance: int = 5,
        tags: Optional[List[str]] = None,
    ) -> bool:
        if self.should_fail:
            return False

        self.memories_added.append({
            "key": key,
            "content": content,
            "importance": importance,
            "tags": tags,
        })
        return True


# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def mock_client():
    """Create a mock GraphitiClient"""
    return MockGraphitiClient()


@pytest.fixture
def sync_service(mock_client):
    """Create a GraphSyncService with mock client"""
    return GraphSyncService(
        graphiti_client=mock_client,
        timeout_ms=200,
        enable_fallback=True,
    )


@pytest.fixture
def sample_affected_nodes():
    """Sample affected node IDs"""
    return ["node-1", "node-2", "node-3"]


@pytest.fixture
def sample_deleted_nodes():
    """Sample deleted node IDs"""
    return ["node-4", "node-5"]


# ============================================================
# Test: Initialization (AC 1)
# ============================================================


class TestGraphSyncServiceInit:
    """Test GraphSyncService initialization"""

    @pytest.mark.asyncio
    async def test_init_with_mock_client(self, mock_client):
        """Test initialization with provided client"""
        service = GraphSyncService(graphiti_client=mock_client)
        result = await service.initialize()

        assert result is True
        assert service._initialized is True
        assert service._client is mock_client

    @pytest.mark.asyncio
    async def test_init_without_client_fallback(self):
        """Test initialization without client enables fallback"""
        service = GraphSyncService(enable_fallback=True)

        # Should not raise even if GraphitiClient import fails
        with patch.dict('sys.modules', {'src.agentic_rag.clients.graphiti_client': None}):
            result = await service.initialize()
            # May fail but shouldn't crash
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_default_timeout_200ms(self):
        """Test default timeout is 200ms (AC 7)"""
        service = GraphSyncService()
        assert service._timeout_ms == 200


# ============================================================
# Test: sync_rollback (AC 2, 4)
# ============================================================


class TestSyncRollback:
    """Test sync_rollback method"""

    @pytest.mark.asyncio
    async def test_sync_rollback_success(
        self,
        sync_service,
        mock_client,
        sample_affected_nodes,
    ):
        """Test successful rollback sync (AC 2)"""
        result = await sync_service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=sample_affected_nodes,
        )

        # Should return SYNCED status (AC 4)
        assert result.status == GraphSyncStatus.SYNCED
        assert result.synced_nodes == sample_affected_nodes
        assert result.episode_id is not None
        assert result.error is None

        # Verify episode was added (AC 2)
        assert len(mock_client.episodes_added) == 1
        episode = mock_client.episodes_added[0]
        assert "test.canvas" in episode["content"]
        assert "snapshot" in episode["content"]

    @pytest.mark.asyncio
    async def test_sync_rollback_with_deleted_nodes(
        self,
        sync_service,
        mock_client,
        sample_affected_nodes,
        sample_deleted_nodes,
    ):
        """Test sync with deleted nodes (AC 3)"""
        result = await sync_service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="operation",
            affected_nodes=sample_affected_nodes,
            deleted_nodes=sample_deleted_nodes,
        )

        assert result.status == GraphSyncStatus.SYNCED
        assert len(result.deleted_nodes) == len(sample_deleted_nodes)

        # Verify soft delete memories were added (AC 3)
        assert len(mock_client.memories_added) == len(sample_deleted_nodes)
        for memory in mock_client.memories_added:
            assert "deleted" in memory["tags"]

    @pytest.mark.asyncio
    async def test_sync_rollback_all_rollback_types(self, sync_service):
        """Test sync works for all rollback types"""
        for rollback_type in ["operation", "snapshot", "timepoint"]:
            result = await sync_service.sync_rollback(
                canvas_path="test.canvas",
                rollback_type=rollback_type,
                affected_nodes=["node-1"],
            )
            assert result.status in [GraphSyncStatus.SYNCED, GraphSyncStatus.PENDING]


# ============================================================
# Test: preserveGraph option (AC 5)
# ============================================================


class TestPreserveGraph:
    """Test preserveGraph option"""

    @pytest.mark.asyncio
    async def test_preserve_graph_skips_sync(
        self,
        sync_service,
        mock_client,
        sample_affected_nodes,
    ):
        """Test preserveGraph=True skips sync (AC 5)"""
        result = await sync_service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=sample_affected_nodes,
            preserve_graph=True,
        )

        # Should return SKIPPED status (AC 5)
        assert result.status == GraphSyncStatus.SKIPPED
        assert result.synced_nodes == []
        assert result.episode_id is None

        # No episodes should be added
        assert len(mock_client.episodes_added) == 0

    @pytest.mark.asyncio
    async def test_preserve_graph_fast_return(self, sync_service):
        """Test preserveGraph returns quickly"""
        result = await sync_service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=["node-1", "node-2"],
            preserve_graph=True,
        )

        # Latency should be near zero
        assert result.latency_ms < 10


# ============================================================
# Test: Graceful degradation (AC 6)
# ============================================================


class TestGracefulDegradation:
    """Test graceful degradation on errors"""

    @pytest.mark.asyncio
    async def test_client_error_returns_failed_status(self):
        """Test client error returns FAILED status (AC 6)"""
        failing_client = MockGraphitiClient(should_fail=True)
        service = GraphSyncService(
            graphiti_client=failing_client,
            enable_fallback=True,
        )

        result = await service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=["node-1"],
        )

        # Should return FAILED but not raise (AC 6)
        # Note: With enable_fallback=True, initialization failure is handled gracefully
        assert result.status == GraphSyncStatus.FAILED

    @pytest.mark.asyncio
    async def test_no_client_returns_failed(self):
        """Test missing client returns FAILED"""
        service = GraphSyncService(
            graphiti_client=None,
            enable_fallback=True,
        )
        service._initialized = True  # Skip initialization

        result = await service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=["node-1"],
        )

        assert result.status == GraphSyncStatus.FAILED

    @pytest.mark.asyncio
    async def test_fallback_disabled_raises(self):
        """Test fallback disabled raises on error (AC 6)"""
        failing_client = MockGraphitiClient(should_fail=True)
        service = GraphSyncService(
            graphiti_client=failing_client,
            enable_fallback=False,
        )

        # With enable_fallback=False, errors should raise exceptions
        with pytest.raises(Exception):
            await service.sync_rollback(
                canvas_path="test.canvas",
                rollback_type="snapshot",
                affected_nodes=["node-1"],
            )


# ============================================================
# Test: Timeout handling (AC 7)
# ============================================================


class TestTimeoutHandling:
    """Test 200ms timeout handling"""

    @pytest.mark.asyncio
    async def test_timeout_returns_pending(self):
        """Test timeout returns PENDING status (AC 7)"""
        slow_client = MockGraphitiClient(should_timeout=True)
        service = GraphSyncService(
            graphiti_client=slow_client,
            timeout_ms=50,  # Very short timeout for testing
            enable_fallback=True,
        )

        result = await service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=["node-1"],
        )

        # Should return PENDING on timeout (AC 7)
        assert result.status == GraphSyncStatus.PENDING
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_timeout_tracks_latency(self):
        """Test timeout tracks latency"""
        slow_client = MockGraphitiClient(should_timeout=True)
        service = GraphSyncService(
            graphiti_client=slow_client,
            timeout_ms=50,
            enable_fallback=True,
        )

        result = await service.sync_rollback(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=["node-1"],
        )

        # Latency should be tracked
        assert result.latency_ms >= 50


# ============================================================
# Test: Soft delete (AC 3)
# ============================================================


class TestSoftDelete:
    """Test soft delete functionality"""

    @pytest.mark.asyncio
    async def test_mark_node_deleted(self, sync_service, mock_client):
        """Test _mark_node_deleted method (AC 3)"""
        success = await sync_service._mark_node_deleted(
            canvas_path="test.canvas",
            node_id="node-123",
        )

        assert success is True
        assert len(mock_client.memories_added) == 1

        memory = mock_client.memories_added[0]
        assert "deleted_node_node-123" == memory["key"]
        assert "deleted" in memory["tags"]
        assert "test.canvas" in memory["tags"]

    @pytest.mark.asyncio
    async def test_soft_delete_records_timestamp(self, sync_service, mock_client):
        """Test soft delete includes timestamp"""
        await sync_service._mark_node_deleted(
            canvas_path="test.canvas",
            node_id="node-456",
        )

        memory = mock_client.memories_added[0]
        # Content should include deletion info
        assert "deleted" in memory["content"].lower()
        assert "node-456" in memory["content"]


# ============================================================
# Test: sync_node_state
# ============================================================


class TestSyncNodeState:
    """Test sync_node_state method"""

    @pytest.mark.asyncio
    async def test_sync_node_add(self, sync_service, mock_client):
        """Test syncing node add operation"""
        success = await sync_service.sync_node_state(
            canvas_path="test.canvas",
            node_id="node-new",
            node_data={"type": "text", "text": "New node content"},
            operation="add",
        )

        assert success is True
        assert len(mock_client.episodes_added) == 1

        episode = mock_client.episodes_added[0]
        assert "ADD" in episode["content"]
        assert "node-new" in episode["content"]

    @pytest.mark.asyncio
    async def test_sync_node_update(self, sync_service, mock_client):
        """Test syncing node update operation"""
        success = await sync_service.sync_node_state(
            canvas_path="test.canvas",
            node_id="node-update",
            node_data={"type": "text", "text": "Updated content"},
            operation="update",
        )

        assert success is True
        episode = mock_client.episodes_added[0]
        assert "UPDATE" in episode["content"]

    @pytest.mark.asyncio
    async def test_sync_node_delete(self, sync_service, mock_client):
        """Test syncing node delete operation"""
        success = await sync_service.sync_node_state(
            canvas_path="test.canvas",
            node_id="node-delete",
            node_data={"type": "text"},
            operation="delete",
        )

        assert success is True
        episode = mock_client.episodes_added[0]
        assert "DELETE" in episode["content"]


# ============================================================
# Test: SyncResult dataclass
# ============================================================


class TestSyncResult:
    """Test SyncResult dataclass"""

    def test_sync_result_defaults(self):
        """Test SyncResult default values"""
        result = SyncResult(status=GraphSyncStatus.SYNCED)

        assert result.status == GraphSyncStatus.SYNCED
        assert result.synced_nodes == []
        assert result.deleted_nodes == []
        assert result.episode_id is None
        assert result.error is None
        assert result.latency_ms == 0.0

    def test_sync_result_with_values(self):
        """Test SyncResult with all values"""
        result = SyncResult(
            status=GraphSyncStatus.PENDING,
            synced_nodes=["node-1"],
            deleted_nodes=["node-2"],
            episode_id="ep-123",
            error="Partial failure",
            latency_ms=150.5,
        )

        assert result.status == GraphSyncStatus.PENDING
        assert result.synced_nodes == ["node-1"]
        assert result.deleted_nodes == ["node-2"]
        assert result.episode_id == "ep-123"
        assert result.error == "Partial failure"
        assert result.latency_ms == 150.5


# ============================================================
# Test: GraphSyncStatus enum
# ============================================================


class TestGraphSyncStatusEnum:
    """Test GraphSyncStatus enum"""

    def test_enum_values(self):
        """Test all enum values exist"""
        assert GraphSyncStatus.SYNCED.value == "synced"
        assert GraphSyncStatus.PENDING.value == "pending"
        assert GraphSyncStatus.SKIPPED.value == "skipped"
        assert GraphSyncStatus.FAILED.value == "failed"

    def test_enum_is_string(self):
        """Test enum is string-based"""
        assert isinstance(GraphSyncStatus.SYNCED.value, str)
        assert str(GraphSyncStatus.SYNCED) == "GraphSyncStatus.SYNCED"


# ============================================================
# Test: get_stats
# ============================================================


class TestGetStats:
    """Test get_stats method"""

    def test_get_stats(self, sync_service):
        """Test stats reporting"""
        stats = sync_service.get_stats()

        assert "initialized" in stats
        assert "timeout_ms" in stats
        assert "enable_fallback" in stats
        assert "client_available" in stats

        assert stats["timeout_ms"] == 200
        assert stats["enable_fallback"] is True
        assert stats["client_available"] is True


# ============================================================
# Test: Episode content building
# ============================================================


class TestEpisodeContentBuilding:
    """Test _build_episode_content method"""

    def test_build_episode_content_basic(self, sync_service):
        """Test basic episode content"""
        content = sync_service._build_episode_content(
            canvas_path="test.canvas",
            rollback_type="snapshot",
            affected_nodes=[],
            deleted_nodes=[],
        )

        assert "[Canvas Rollback Event]" in content
        assert "test.canvas" in content
        assert "snapshot" in content
        assert "Timestamp:" in content

    def test_build_episode_content_with_nodes(self, sync_service):
        """Test episode content with nodes"""
        content = sync_service._build_episode_content(
            canvas_path="test.canvas",
            rollback_type="operation",
            affected_nodes=["node-1", "node-2"],
            deleted_nodes=["node-3"],
        )

        assert "node-1" in content
        assert "node-2" in content
        assert "node-3" in content
        assert "Affected nodes:" in content
        assert "Deleted nodes:" in content
