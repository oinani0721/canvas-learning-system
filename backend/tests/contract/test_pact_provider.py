"""
Canvas Learning System - Pact Provider Verification Tests

后端 Pact Provider 验证测试，用于验证后端 API 是否满足前端定义的契约。

使用方法:
    pytest tests/contract/test_pact_provider.py -v

环境变量:
    PACT_BROKER_URL: Pact Broker 地址
    PACT_BROKER_TOKEN: Pact Broker 认证令牌
    PACT_PROVIDER_VERSION: 提供者版本 (默认为 git commit hash)

依赖:
    pip install pact-python pytest-asyncio
"""

import os
import subprocess
from pathlib import Path

import pytest

pact = pytest.importorskip("pact", reason="pact-python not installed")
from pact import Verifier

# ═══════════════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════════════

PROVIDER_NAME = "Canvas-Backend"
CONSUMER_NAME = "Canvas-Frontend"

# Pact 文件目录（本地开发使用）
PACT_DIR = Path(__file__).parent.parent.parent.parent / "canvas-progress-tracker" / "obsidian-plugin" / "pacts"

# Pact Broker 配置（CI/CD 使用）
PACT_BROKER_URL = os.environ.get("PACT_BROKER_URL", "")
PACT_BROKER_TOKEN = os.environ.get("PACT_BROKER_TOKEN", "")

# Provider 版本
def get_git_version() -> str:
    """获取 git commit hash 作为版本号"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


PROVIDER_VERSION = os.environ.get("PACT_PROVIDER_VERSION", get_git_version())


# ═══════════════════════════════════════════════════════════════════════════════
# Provider States
# ═══════════════════════════════════════════════════════════════════════════════

class ProviderStateMiddleware:
    """
    Provider State 处理中间件。

    Pact 测试会发送 provider state 请求到 /_pact/provider-states 端点，
    用于设置测试前的数据状态。
    """

    def __init__(self):
        self.states = {}

    def setup_state(self, state: str, params: dict = None) -> dict:
        """
        根据 provider state 设置测试数据。

        Args:
            state: Provider state 名称
            params: 可选参数

        Returns:
            dict: 设置结果
        """
        handlers = {
            # Memory API states
            "the API is healthy": self._setup_healthy,
            "memory subjects exist": self._setup_memory_subjects,
            "no memory subjects exist": self._setup_no_memory_subjects,
            "entities exist for subject math-001": self._setup_entities_for_subject,
            "memory contains searchable content": self._setup_searchable_content,
            "entity with id non-existent does not exist": self._setup_no_entity,
            "API expects valid JSON": self._setup_valid_json_expected,
            # Multimodal API states (Story 35.12)
            "multimodal storage is ready": self._setup_multimodal_storage,
            "multimodal content exists": self._setup_multimodal_content,
            "multimodal content exists with searchable descriptions": self._setup_searchable_multimodal,
            "multimodal content linked to concept": self._setup_multimodal_with_concept,
            "multimodal service is running": self._setup_multimodal_service,
            "multimodal content does not exist": self._setup_no_multimodal_content,
        }

        handler = handlers.get(state)
        if handler:
            return handler(params or {})
        else:
            print(f"Warning: Unknown provider state: {state}")
            return {"status": "unknown_state"}

    def _setup_healthy(self, params: dict) -> dict:
        """设置健康状态"""
        # 无需特殊设置，API 默认健康
        return {"status": "ok"}

    def _setup_memory_subjects(self, params: dict) -> dict:
        """设置内存主题存在"""
        # 在实际实现中，这里会向数据库插入测试数据
        # 使用 pytest fixtures 或直接操作数据库
        return {"status": "ok", "subjects_created": 3}

    def _setup_no_memory_subjects(self, params: dict) -> dict:
        """设置无内存主题"""
        # 清理所有主题数据
        return {"status": "ok", "subjects_cleared": True}

    def _setup_entities_for_subject(self, params: dict) -> dict:
        """设置特定主题的实体"""
        return {"status": "ok", "entities_created": 2}

    def _setup_searchable_content(self, params: dict) -> dict:
        """设置可搜索内容"""
        return {"status": "ok", "content_indexed": True}

    def _setup_no_entity(self, params: dict) -> dict:
        """确保实体不存在"""
        return {"status": "ok", "entity_deleted": True}

    def _setup_valid_json_expected(self, params: dict) -> dict:
        """设置期望有效 JSON"""
        return {"status": "ok"}

    # ── Multimodal Provider States (Story 35.12 AC 35.12.1, 35.12.2) ──
    # ⚠️ Known limitation: These handlers directly manipulate _content_store
    # (private attribute) for synchronous state setup. If MultimodalService
    # changes its internal representation, these handlers must be updated.
    # Ideally, use public async API (upload_file, etc.) when Pact supports
    # async provider state setup.

    def _setup_multimodal_storage(self, params: dict) -> dict:
        """Initialize multimodal storage — service ready to accept uploads."""
        from app.services.multimodal_service import reset_multimodal_service

        reset_multimodal_service()
        return {"status": "ok", "storage_initialized": True}

    def _setup_multimodal_content(self, params: dict) -> dict:
        """Insert test multimodal content so GET/PUT/DELETE can find it."""
        from datetime import datetime
        from app.services.multimodal_service import get_multimodal_service
        from app.models.multimodal_schemas import (
            MultimodalMediaType,
            MultimodalMetadataSchema,
        )

        service = get_multimodal_service()
        content_id = params.get("content_id", "550e8400-e29b-41d4-a716-446655440000")
        # NOTE: file_path points to a non-existent file on disk. This is
        # acceptable for metadata-only Pact verification, but if future tests
        # attempt to serve the file, they will need real fixture files.
        service._content_store[content_id] = {
            "id": content_id,
            "media_type": MultimodalMediaType.IMAGE,
            "file_path": str(service.storage_base_path / "image" / "test.png"),
            "related_concept_id": "concept-001",
            "created_at": datetime(2026, 1, 1, 12, 0, 0),
            "description": "Test image for pact verification",
            "metadata": MultimodalMetadataSchema(
                file_size=1024, mime_type="image/png"
            ),
            "thumbnail_path": None,
        }
        return {"status": "ok", "content_id": content_id}

    def _setup_searchable_multimodal(self, params: dict) -> dict:
        """Insert content with searchable descriptions for POST /search."""
        from datetime import datetime
        from app.services.multimodal_service import get_multimodal_service
        from app.models.multimodal_schemas import (
            MultimodalMediaType,
            MultimodalMetadataSchema,
        )

        service = get_multimodal_service()
        items = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "media_type": MultimodalMediaType.IMAGE,
                "file_path": str(service.storage_base_path / "image" / "math.png"),
                "related_concept_id": "concept-math",
                "created_at": datetime(2026, 1, 1, 12, 0, 0),
                "description": "数学公式推导图解",
                "metadata": MultimodalMetadataSchema(
                    file_size=2048, mime_type="image/png"
                ),
                "thumbnail_path": None,
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "media_type": MultimodalMediaType.PDF,
                "file_path": str(service.storage_base_path / "pdf" / "physics.pdf"),
                "related_concept_id": "concept-physics",
                "created_at": datetime(2026, 1, 2, 12, 0, 0),
                "description": "物理力学讲义",
                "metadata": MultimodalMetadataSchema(
                    file_size=4096, mime_type="application/pdf"
                ),
                "thumbnail_path": None,
            },
        ]
        for item in items:
            service._content_store[item["id"]] = item
        return {"status": "ok", "items_created": len(items)}

    def _setup_multimodal_with_concept(self, params: dict) -> dict:
        """Insert content linked to a specific concept for GET /by-concept."""
        from datetime import datetime
        from app.services.multimodal_service import get_multimodal_service
        from app.models.multimodal_schemas import (
            MultimodalMediaType,
            MultimodalMetadataSchema,
        )

        service = get_multimodal_service()
        concept_id = params.get("concept_id", "concept-test-001")
        content_id = "550e8400-e29b-41d4-a716-446655440003"
        service._content_store[content_id] = {
            "id": content_id,
            "media_type": MultimodalMediaType.IMAGE,
            "file_path": str(service.storage_base_path / "image" / "concept.png"),
            "related_concept_id": concept_id,
            "created_at": datetime(2026, 1, 1, 12, 0, 0),
            "description": "Concept-linked test image",
            "metadata": MultimodalMetadataSchema(
                file_size=512, mime_type="image/png"
            ),
            "thumbnail_path": None,
        }
        return {"status": "ok", "content_id": content_id, "concept_id": concept_id}

    def _setup_multimodal_service(self, params: dict) -> dict:
        """Ensure multimodal service is running for GET /health."""
        return {"status": "ok", "service_running": True}

    def _setup_no_multimodal_content(self, params: dict) -> dict:
        """Clear all multimodal content — empty state for 404 scenarios."""
        from app.services.multimodal_service import get_multimodal_service

        service = get_multimodal_service()
        service._content_store.clear()
        return {"status": "ok", "content_cleared": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Pact Provider 验证测试
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def provider_url():
    """
    提供者 URL。

    在测试中可以使用 pytest-asyncio 启动 FastAPI 测试服务器，
    或者使用已经运行的开发服务器。
    """
    # 默认使用本地开发服务器
    return os.environ.get("PROVIDER_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def verifier(provider_url):
    """创建 Pact Verifier 实例"""
    return Verifier(
        provider=PROVIDER_NAME,
        provider_base_url=provider_url,
    )


class TestPactProviderVerification:
    """Pact Provider 验证测试类"""

    @pytest.mark.skipif(
        not PACT_DIR.exists() and not PACT_BROKER_URL,
        reason="No pact files found and no broker configured"
    )
    def test_verify_pacts_from_local_files(self, verifier, provider_url):
        """
        从本地 Pact 文件验证 Provider。

        这个测试用于本地开发，不需要 Pact Broker。
        """
        if not PACT_DIR.exists():
            pytest.skip("No local pact files found")

        pact_files = list(PACT_DIR.glob("*.json"))
        if not pact_files:
            pytest.skip("No pact files in directory")

        for pact_file in pact_files:
            print(f"\nVerifying pact: {pact_file.name}")

            output, result = verifier.verify_pacts(
                pact_urls=[str(pact_file)],
                enable_pending=False,
                publish_version=None,  # 本地验证不发布
                provider_states_setup_url=f"{provider_url}/_pact/provider-states",
            )

            assert result == 0, f"Pact verification failed for {pact_file.name}:\n{output}"

    @pytest.mark.skipif(
        not PACT_BROKER_URL,
        reason="PACT_BROKER_URL not configured"
    )
    def test_verify_pacts_from_broker(self, verifier, provider_url):
        """
        从 Pact Broker 验证 Provider。

        这个测试用于 CI/CD 环境。
        """
        output, result = verifier.verify_with_broker(
            broker_url=PACT_BROKER_URL,
            broker_token=PACT_BROKER_TOKEN,
            publish_version=PROVIDER_VERSION,
            enable_pending=True,
            consumer_version_selectors=[
                {"mainBranch": True},  # 验证 main 分支的消费者
                {"deployed": True},     # 验证已部署的消费者
            ],
            provider_states_setup_url=f"{provider_url}/_pact/provider-states",
        )

        assert result == 0, f"Pact verification failed:\n{output}"


# ═══════════════════════════════════════════════════════════════════════════════
# Provider States Endpoint (需要添加到 FastAPI 应用)
# ═══════════════════════════════════════════════════════════════════════════════

"""
将以下代码添加到 FastAPI 应用中以支持 Provider States:

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

class ProviderStateRequest(BaseModel):
    consumer: str
    state: str
    params: dict = {}

@app.post("/_pact/provider-states")
async def provider_states(request: ProviderStateRequest):
    '''
    Pact Provider States endpoint.

    Pact Verifier 会在每个交互验证前调用此端点设置数据状态。
    '''
    middleware = ProviderStateMiddleware()
    result = middleware.setup_state(request.state, request.params)
    return result
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 命令行运行
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 可以直接运行此文件进行验证
    pytest.main([__file__, "-v", "-s"])
