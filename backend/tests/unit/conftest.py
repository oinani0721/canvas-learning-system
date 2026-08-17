# Shared fixtures for EPIC-32 FSRS unit tests
# Extracted from test_review_service_fsrs.py, test_fsrs_state_query.py
# to eliminate fixture duplication across 4 files.
"""
Shared pytest fixtures for FSRS unit tests.

Provides mock dependencies (CanvasService, BackgroundTaskManager) and
ReviewService factory/instance fixtures used by:
- test_review_service_fsrs.py
- test_fsrs_state_query.py
- test_card_state_concurrent_write.py (indirectly)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _stub_vault_identity_registry(monkeypatch):
    """R10 P0-01 注册表引入后的单测隔离 (autouse).

    endpoint 型单测 (TestClient) 会走到 get_vault_identity_registry() —
    真实 registry 连真 Neo4j, 会把测试 vault 名认领进生产注册表 (实测
    污染过一次: test_vault_id_reaches_cypher_as_physical_group 把生产桶
    vault__canvas_vault 认领成了 'canvas_vault', 真插件发 'canvas-vault'
    将来必 409)。unit 层一律 stub 模块级 accessor 为 no-op。

    ⚠️ 只 patch get_vault_identity_registry() 函数, 不动
    VaultIdentityRegistry 类 — test_vault_identity_registry.py 直接
    实例化类 + fake driver, 不受影响; tests/integration/ 有独立
    conftest, 真注册表路径在那里验收。
    """

    class _NoopRegistry:
        async def assert_identity(self, *, raw_vault_id: str, physical_gid: str) -> None:
            return None

    import app.services.vault_identity_registry as vir

    monkeypatch.setattr(vir, "get_vault_identity_registry", lambda: _NoopRegistry())
    yield


@pytest.fixture
def mock_canvas_service():
    """Shared mock CanvasService for FSRS unit tests."""
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    """Shared mock BackgroundTaskManager for FSRS unit tests."""
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


@pytest.fixture
def review_service_factory(mock_canvas_service, mock_task_manager):
    """Factory to create ReviewService with mocked dependencies."""

    def _create():
        from app.services.review_service import ReviewService

        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
        )

    return _create


@pytest.fixture
def review_service(review_service_factory):
    """Create ReviewService instance for testing."""
    return review_service_factory()


@pytest.fixture
def fallback_service(mock_canvas_service, mock_task_manager):
    """ReviewService with FSRS disabled (Ebbinghaus fallback mode)."""
    from app.services.review_service import ReviewService

    with patch("app.services.review_service.create_fsrs_manager", return_value=None):
        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            fsrs_manager=None,
        )
