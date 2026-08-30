# Canvas Learning System - Shared Helpers for Story 31.A.2 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Shared fixtures and helpers for Story 31.A.2 test modules.

NOT a test file — contains only helpers used by:
- test_story_31a2_ac1_neo4j_priority.py
- test_story_31a2_ac2_client_method.py
- test_story_31a2_ac3_persistence.py
- test_story_31a2_ac4_pagination.py
- test_story_31a2_ac5_api_injection.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService

# =============================================================================
# Shared Fixtures
# =============================================================================


@pytest.fixture
def mock_graphiti_memory():
    """Mock LearningMemoryClient to prevent side effects."""
    memory = MagicMock()
    memory.add_learning_episode = AsyncMock()
    return memory


def _make_service(neo4j_client, graphiti_memory=None):
    """Helper to create MemoryService with mocked dependencies."""
    service = MemoryService(neo4j_client=neo4j_client)
    if graphiti_memory is None:
        graphiti_memory = MagicMock()
        graphiti_memory.add_learning_episode = AsyncMock()
    service._learning_memory = graphiti_memory
    return service


def _scope() -> str:
    """CARD-G4-1a (2026-08-30): 当前读作用域的 group_id。

    读侧封堵 (`group_id=None` 直通 Neo4j 全库扫描) 落地后, ``get_learning_history``
    的作用域恒非空, 内存兜底 episode 必须**自带归属**才可见 —— 无 group_id 的
    条目在任何 vault 视角下都 fail-closed 不可见。

    这不是为测试放水: 生产写路径 (``record_learning_event`` /
    ``record_batch_learning_events`` / ``record_temporal_event``) 现在一律给
    内存 episode 落 group_id, 本 helper 让 fixture 与生产写出的形状一致。
    "无归属 episode 不可见"这条契约本身由
    ``tests/unit/test_memory_read_scope_g41a.py`` 正面锁死。
    """
    from app.core.vault_scope import current_group_id

    return current_group_id()


def _subject_scope(subject: str) -> str:
    """当前 vault 下某个**学科子组**的 group_id。

    传了 subject 的读, 作用域是 `<vault>:<subject>` 子组; 前缀语义只向下不向上,
    子组读看不到父组。fixture 要模拟"这条 episode 属于该学科"就必须落进子组 ——
    与生产写侧 `memory_service._vault_scoped_group_id(subject)` 同一落点。
    """
    from app.services.memory_service import _vault_scoped_group_id

    return _vault_scoped_group_id(subject)


def _make_neo4j_mock(**overrides) -> MagicMock:
    """Helper to create a standard Neo4jClient mock."""
    client = MagicMock(spec=Neo4jClient)
    client._initialized = True
    client._use_json_fallback = False
    client.initialize = AsyncMock()
    client.cleanup = AsyncMock()
    client.close = AsyncMock()
    client.get_learning_history = AsyncMock(return_value=[])
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.stats = {"initialized": True, "mode": "NEO4J", "health_status": True}
    for key, val in overrides.items():
        setattr(client, key, val)
    return client
