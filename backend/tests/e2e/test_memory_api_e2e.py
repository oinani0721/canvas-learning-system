# Canvas Learning System - Memory API E2E Tests
# Story 31.A.5 AC-31.A.5.4: 端到端 API 测试
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.4]
"""
端到端测试：通过真实 HTTP 请求测试 Memory API。

测试覆盖:
1. POST /api/v1/memory/episodes - 201 Created
2. GET /api/v1/memory/episodes - 200 OK
3. 完整的写入-读取周期

[Source: docs/stories/31.A.5.story.md#AC-31.A.5.4]
[Source: backend/app/api/v1/endpoints/memory.py]
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import app


# =============================================================================
# E2E Test Settings Override
# =============================================================================

def get_e2e_memory_settings() -> Settings:
    """
    Override settings for Memory API E2E tests.
    """
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Memory E2E)",
        VERSION="1.0.0-memory-e2e",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture
async def e2e_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for E2E tests.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: async testing)
    """
    import app.services.memory_service as memory_module

    # Save and reset singleton for test isolation
    original_singleton = memory_module._memory_service_instance
    memory_module._memory_service_instance = None

    app.dependency_overrides[get_settings] = get_e2e_memory_settings

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        # Always restore singleton (even if test fails mid-execution)
        memory_module._memory_service_instance = original_singleton


# =============================================================================
# AC-31.A.5.4: E2E API Tests - Full Cycle
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.4]
# =============================================================================


class TestMemoryApiE2E:
    """
    端到端 API 测试类。

    验收条件:
    - [ ] 通过真实 HTTP 请求测试
    - [ ] 覆盖完整的写入-读取周期
    - [ ] 验证 API 响应格式正确

    [Source: docs/stories/31.A.5.story.md#AC-31.A.5.4]
    """

    @pytest.fixture
    def unique_user_id(self):
        """Generate unique user ID for test isolation."""
        return f"e2e_user_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def test_episode_data(self, unique_user_id):
        """Standard test episode data."""
        return {
            "user_id": unique_user_id,
            "canvas_path": f"test/e2e_{uuid.uuid4().hex[:8]}.canvas",
            "node_id": f"e2e_node_{uuid.uuid4().hex[:8]}",
            "concept": "概率论基础",
            "agent_type": "scoring",
            "score": 88,
            "duration_seconds": 300
        }

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_memory_api_full_cycle(
        self,
        e2e_client: AsyncClient,
        test_episode_data
    ):
        """
        端到端测试: 写入 → 读取 完整周期。

        AC-31.A.5.4: 通过真实 HTTP 请求测试

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.4]
        """
        # 1. 写入学习事件
        write_response = await e2e_client.post(
            "/api/v1/memory/episodes",
            json=test_episode_data
        )

        # 验证写入响应
        assert write_response.status_code == 201, \
            f"Expected 201 Created, got {write_response.status_code}: {write_response.text}"

        write_data = write_response.json()
        assert "episode_id" in write_data
        assert write_data["status"] == "created"
        assert write_data["episode_id"].startswith("episode-")

        # 2. 读取学习历史
        read_response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={"user_id": test_episode_data["user_id"]}
        )

        # 验证读取响应
        assert read_response.status_code == 200, \
            f"Expected 200 OK, got {read_response.status_code}: {read_response.text}"

        read_data = read_response.json()

        # 3. 验证响应格式
        assert "items" in read_data, "Response should have 'items' field"
        assert "total" in read_data, "Response should have 'total' field"
        assert "page" in read_data, "Response should have 'page' field"
        assert "page_size" in read_data, "Response should have 'page_size' field"

        # 4. 验证数据
        items = read_data["items"]
        assert len(items) > 0, "Should have at least one learning event"

        found_concept = any(
            item.get("concept") == test_episode_data["concept"]
            for item in items
        )
        assert found_concept, \
            f"Concept '{test_episode_data['concept']}' not found in response"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_episode_returns_201(
        self,
        e2e_client: AsyncClient,
        test_episode_data
    ):
        """
        验证 POST /episodes 返回 201 Created。

        [Source: docs/stories/31.A.5.story.md#8.1-SDD规范参考]
        """
        response = await e2e_client.post(
            "/api/v1/memory/episodes",
            json=test_episode_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "episode_id" in data
        assert "status" in data
        assert data["status"] == "created"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_episodes_returns_200(
        self,
        e2e_client: AsyncClient,
        unique_user_id
    ):
        """
        验证 GET /episodes 返回 200 OK。

        [Source: docs/stories/31.A.5.story.md#8.1-SDD规范参考]
        """
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={"user_id": unique_user_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_episode_with_all_required_fields(
        self,
        e2e_client: AsyncClient,
        unique_user_id
    ):
        """
        验证必填字段验证。

        必填字段:
        - user_id
        - canvas_path
        - node_id
        - concept
        - agent_type

        [Source: docs/stories/31.A.5.story.md#8.1-SDD规范参考]
        """
        # 完整数据
        complete_data = {
            "user_id": unique_user_id,
            "canvas_path": "test/complete.canvas",
            "node_id": "complete_node_001",
            "concept": "完整测试概念",
            "agent_type": "scoring"
        }

        response = await e2e_client.post(
            "/api/v1/memory/episodes",
            json=complete_data
        )

        assert response.status_code == 201

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_episode_missing_required_field(
        self,
        e2e_client: AsyncClient
    ):
        """
        验证缺少必填字段返回 422。
        """
        # 缺少 concept 字段
        incomplete_data = {
            "user_id": "test_user",
            "canvas_path": "test.canvas",
            "node_id": "node_001",
            # "concept": missing
            "agent_type": "scoring"
        }

        response = await e2e_client.post(
            "/api/v1/memory/episodes",
            json=incomplete_data
        )

        # FastAPI validation returns 422
        assert response.status_code == 422

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_episodes_with_subject_filter(
        self,
        e2e_client: AsyncClient,
        unique_user_id
    ):
        """
        验证 subject 查询参数过滤。

        AC-30.8.3: 支持 subject 查询参数

        [Source: docs/stories/30.8.story.md#AC-30.8.3]
        """
        # 首先创建一个有 subject 的事件
        create_response = await e2e_client.post(
            "/api/v1/memory/episodes",
            json={
                "user_id": unique_user_id,
                "canvas_path": "数学/线代.canvas",
                "node_id": "math_node",
                "concept": "矩阵乘法",
                "agent_type": "scoring",
                "subject": "数学"
            }
        )
        assert create_response.status_code == 201

        # 使用 subject 过滤查询
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={
                "user_id": unique_user_id,
                "subject": "数学"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        # 验证返回的数据都是数学学科
        for item in data["items"]:
            if item.get("subject"):
                assert item["subject"] == "数学"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_episodes_pagination(
        self,
        e2e_client: AsyncClient,
        unique_user_id
    ):
        """
        验证分页功能。

        [Source: backend/app/api/v1/endpoints/memory.py:173-174]
        """
        # 创建多个事件
        for i in range(5):
            await e2e_client.post(
                "/api/v1/memory/episodes",
                json={
                    "user_id": unique_user_id,
                    "canvas_path": f"test/pagination_{i}.canvas",
                    "node_id": f"pagination_node_{i}",
                    "concept": f"分页测试概念_{i}",
                    "agent_type": "scoring"
                }
            )

        # 测试分页
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={
                "user_id": unique_user_id,
                "page": 1,
                "page_size": 2
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 2
        # 验证返回的 items 数量不超过 page_size
        assert len(data["items"]) <= 2


class TestMemoryApiErrorHandling:
    """
    Memory API 错误处理测试。
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_episodes_without_user_id(
        self,
        e2e_client: AsyncClient
    ):
        """
        验证缺少 user_id 参数返回 422。
        """
        response = await e2e_client.get("/api/v1/memory/episodes")

        # user_id 是必填参数
        assert response.status_code == 422

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invalid_page_size(
        self,
        e2e_client: AsyncClient
    ):
        """
        验证无效 page_size 返回 422。
        """
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={
                "user_id": "test_user",
                "page_size": 999  # 超过最大值 100
            }
        )

        # page_size 有限制 le=100
        assert response.status_code == 422


class TestMemoryApiDataPersistence:
    """
    数据持久化验证测试。

    这些测试验证数据在 API 请求之间正确持久化。
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_data_persists_across_requests(
        self,
        e2e_client: AsyncClient
    ):
        """
        验证数据在多个请求之间持久化。

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
        """
        user_id = f"persist_test_{uuid.uuid4().hex[:8]}"
        concept = f"持久化测试_{uuid.uuid4().hex[:8]}"

        # 第一个请求: 写入
        await e2e_client.post(
            "/api/v1/memory/episodes",
            json={
                "user_id": user_id,
                "canvas_path": "test/persist.canvas",
                "node_id": "persist_node",
                "concept": concept,
                "agent_type": "scoring"
            }
        )

        # POST 返回 201 时数据已持久化，无需 sleep

        # 第二个请求: 读取
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={"user_id": user_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证数据持久化
        assert len(data["items"]) > 0
        found = any(item.get("concept") == concept for item in data["items"])
        assert found, f"Concept '{concept}' should be persisted"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_multiple_episodes_same_user(
        self,
        e2e_client: AsyncClient
    ):
        """
        验证同一用户可以有多个学习事件。
        """
        user_id = f"multi_episode_{uuid.uuid4().hex[:8]}"
        concepts = [f"概念A_{uuid.uuid4().hex[:4]}", f"概念B_{uuid.uuid4().hex[:4]}"]

        # 创建多个事件
        for i, concept in enumerate(concepts):
            response = await e2e_client.post(
                "/api/v1/memory/episodes",
                json={
                    "user_id": user_id,
                    "canvas_path": f"test/multi_{i}.canvas",
                    "node_id": f"multi_node_{i}",
                    "concept": concept,
                    "agent_type": "scoring"
                }
            )
            assert response.status_code == 201

        # 查询所有事件
        response = await e2e_client.get(
            "/api/v1/memory/episodes",
            params={"user_id": user_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证所有概念都存在
        found_concepts = {item.get("concept") for item in data["items"] if item.get("concept")}
        for concept in concepts:
            assert concept in found_concepts, \
                f"Concept '{concept}' should be in response"
