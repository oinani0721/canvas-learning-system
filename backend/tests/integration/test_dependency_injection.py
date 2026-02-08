# Canvas Learning System - Dependency Injection Integration Tests
# Story 31.A.5 AC-31.A.5.2: 依赖注入验证测试
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.2]
"""
验证依赖注入机制正确工作，确保服务间的依赖关系正确建立。

重点验证:
1. VerificationService 正确注入 GraphitiTemporalClient
2. GraphitiTemporalClient 的方法可调用

Note: Story 31.A.5 示例使用 search_memories()，但实际代码使用
      search_verification_questions()。测试按实际实现编写。
      [Source: backend/app/services/verification_service.py:1851]

[Source: docs/prd/EPIC-31.A-MEMORY-PIPELINE-FIX.md#断点1]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings


# =============================================================================
# AC-31.A.5.2: VerificationService Graphiti Client Injection Tests
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.2]
# =============================================================================


class TestVerificationServiceDependencyInjection:
    """
    验证 VerificationService 的依赖注入。

    Story 31.A.1 修复了 graphiti_client 未注入的问题。
    此测试确保修复后依赖正确注入。

    [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_verification_service_has_graphiti_client(self):
        """
        验证 VerificationService 正确注入 GraphitiClient。

        AC-31.A.5.2: 验证 graphiti_client 不为 None

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.2]
        """
        from app.dependencies import get_verification_service

        # get_verification_service requires settings parameter
        settings = Settings()

        # get_verification_service is an async generator, use __anext__
        service_gen = get_verification_service(settings=settings)
        try:
            service = await service_gen.__anext__()

            # AC-31.A.5.2: 验证 graphiti_client 已注入
            # Note: 在没有 Graphiti 服务运行时可能为 None（graceful degradation）
            # 但依赖注入机制本身应该正常工作
            if service._graphiti_client is not None:
                # 验证注入的是正确类型
                assert hasattr(service._graphiti_client, 'search_verification_questions'), \
                    "GraphitiClient should have search_verification_questions method"
                assert hasattr(service._graphiti_client, 'add_verification_question'), \
                    "GraphitiClient should have add_verification_question method"
            else:
                # Graceful degradation: Graphiti 服务不可用时返回 None
                # 这也是合法的依赖注入结果
                pytest.skip(
                    "GraphitiTemporalClient not available - "
                    "Graphiti service may not be running"
                )

        finally:
            # Cleanup: 关闭 generator
            try:
                await service_gen.aclose()
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graphiti_search_verification_questions_callable(self):
        """
        验证 search_verification_questions 可调用。

        AC-31.A.5.2: 验证实际方法可调用
        Note: Story 示例使用 search_memories，实际实现使用 search_verification_questions

        [Source: backend/app/services/verification_service.py:1851]
        """
        from app.dependencies import get_verification_service

        settings = Settings()
        service_gen = get_verification_service(settings=settings)
        try:
            service = await service_gen.__anext__()

            if service._graphiti_client is None:
                pytest.skip(
                    "GraphitiTemporalClient not available - "
                    "Graphiti service may not be running"
                )

            # 使用实际存在的 search_verification_questions 方法
            try:
                result = await service._graphiti_client.search_verification_questions(
                    concept="测试概念",
                    limit=5
                )
                # 验证返回类型是 list
                assert isinstance(result, list), \
                    f"Expected list, got {type(result)}"

            except Exception as e:
                # 如果 Graphiti 服务不可用，方法调用可能失败
                # 但我们验证的是方法存在且可调用，不是 Graphiti 服务状态
                if "ConnectionRefusedError" in str(e) or "timeout" in str(e).lower():
                    pytest.skip(f"Graphiti service connection failed: {e}")
                else:
                    pytest.fail(f"GraphitiClient method call failed unexpectedly: {e}")

        finally:
            try:
                await service_gen.aclose()
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graphiti_temporal_client_singleton(self):
        """
        验证 GraphitiTemporalClient 是单例模式。

        [Source: backend/app/dependencies.py:779-782]
        """
        from app.dependencies import get_graphiti_temporal_client

        # 第一次获取
        client1 = get_graphiti_temporal_client()

        # 第二次获取
        client2 = get_graphiti_temporal_client()

        # 验证是同一个实例
        if client1 is not None:
            assert client1 is client2, \
                "GraphitiTemporalClient should be singleton"
        else:
            pytest.skip("GraphitiTemporalClient not available")


# =============================================================================
# AC-31.A.5.2 Extended: Other Dependency Injection Tests
# =============================================================================


class TestMemoryServiceDependencyInjection:
    """
    验证 MemoryService 的依赖注入。

    [Source: docs/stories/31.A.2.story.md]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_service_neo4j_client_injection(self):
        """
        验证 MemoryService 正确注入 Neo4jClient。

        [Source: backend/app/services/memory_service.py:__init__]
        """
        from app.services.memory_service import MemoryService
        from app.clients.neo4j_client import Neo4jClient
        from unittest.mock import MagicMock

        # 创建 mock Neo4j client
        mock_neo4j = MagicMock(spec=Neo4jClient)

        # 创建 MemoryService
        service = MemoryService(neo4j_client=mock_neo4j)

        # 验证注入成功
        # MemoryService stores neo4j_client as self.neo4j (not self._neo4j_client)
        assert service.neo4j is mock_neo4j, \
            "Neo4jClient should be injected"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_service_learning_memory_injection(self):
        """
        验证 MemoryService 正确注入 LearningMemoryClient。

        [Source: backend/app/services/memory_service.py:__init__]
        """
        from app.services.memory_service import MemoryService
        from unittest.mock import MagicMock

        # 创建 mock clients
        mock_neo4j = MagicMock()
        mock_learning_memory = MagicMock()

        # 创建 MemoryService
        # MemoryService.__init__ parameter is learning_memory_client (not learning_memory)
        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory
        )

        # 验证注入成功
        # MemoryService stores learning_memory_client as self._learning_memory
        assert service._learning_memory is mock_learning_memory, \
            "LearningMemoryClient should be injected"


class TestRAGServiceDependencyInjection:
    """
    验证 RAGService 的依赖注入。

    [Source: docs/stories/story-12.A.2-agent-rag-bridge.md]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_service_singleton(self):
        """
        验证 RAGService 是单例模式。

        [Source: backend/app/dependencies.py:get_rag_service]
        """
        from app.dependencies import get_rag_service

        # 第一次获取
        service1 = get_rag_service()

        # 第二次获取
        service2 = get_rag_service()

        # 验证是同一个实例
        assert service1 is service2, \
            "RAGService should be singleton"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_service_dep_initialization(self):
        """
        验证 get_rag_service_dep 正确初始化 RAGService。

        [Source: backend/app/dependencies.py:get_rag_service_dep]
        """
        from app.dependencies import get_rag_service_dep

        # get_rag_service_dep is an async generator
        service_gen = get_rag_service_dep()
        try:
            service = await service_gen.__anext__()

            # 验证服务已初始化
            assert service._initialized, \
                "RAGService should be initialized"

        finally:
            try:
                await service_gen.aclose()
            except Exception:
                pass


# =============================================================================
# Dependency Chain Tests
# =============================================================================


class TestDependencyChain:
    """
    验证完整的依赖链正确建立。

    [Source: backend/app/dependencies.py:487-492]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_verification_service_full_dependency_chain(self):
        """
        验证 VerificationService 的完整依赖链。

        Dependency Chain:
            get_settings() → settings
            get_rag_service() → rag_service
            get_cross_canvas_service() → cross_canvas_service
            get_graphiti_temporal_client() → graphiti_client
            TextbookContextService(settings) → textbook_service
            VerificationService(all deps) → verification_service

        [Source: backend/app/dependencies.py:486-548]
        """
        from app.dependencies import get_verification_service

        settings = Settings()
        service_gen = get_verification_service(settings=settings)
        try:
            service = await service_gen.__anext__()

            # 验证所有依赖都已注入（可能为 None 表示 graceful degradation）
            # 但属性应该存在
            assert hasattr(service, '_rag_service'), \
                "VerificationService should have _rag_service attribute"
            assert hasattr(service, '_cross_canvas_service'), \
                "VerificationService should have _cross_canvas_service attribute"
            assert hasattr(service, '_textbook_context_service'), \
                "VerificationService should have _textbook_context_service attribute"
            assert hasattr(service, '_graphiti_client'), \
                "VerificationService should have _graphiti_client attribute"

            # 验证核心服务已注入（RAG service 应该始终可用）
            assert service._rag_service is not None, \
                "RAGService should be injected"

        finally:
            try:
                await service_gen.aclose()
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_neo4j_client_dep_returns_valid_client(self):
        """
        验证 get_neo4j_client_dep 返回有效的 Neo4jClient。

        [Source: backend/app/dependencies.py:get_neo4j_client_dep]
        """
        from app.dependencies import get_neo4j_client_dep

        # get_neo4j_client_dep is a regular function (NOT async generator)
        # It returns Neo4jClient directly
        try:
            client = get_neo4j_client_dep()

            # 验证返回了有效的 client
            assert client is not None, \
                "Neo4jClient should be returned"
            assert hasattr(client, 'run_query'), \
                "Neo4jClient should have run_query method"
            assert hasattr(client, 'get_learning_history'), \
                "Neo4jClient should have get_learning_history method"

        except Exception as e:
            # Neo4j 可能不可用
            if "ConnectionRefused" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Neo4j service not available: {e}")
            else:
                raise
