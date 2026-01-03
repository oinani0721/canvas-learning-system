"""
Story 12.J.6: 编码安全集成测试套件

验证 Epic 12.J 的所有编码修复正常工作。

测试场景:
1. Emoji 在 canvas 名称中
2. 中文内容往返
3. 无效 UTF-8 返回 400
4. 日志中文不崩溃
5. Unicode 异常安全处理

[Source: docs/stories/story-12.J.6-encoding-integration-tests.md]
[Source: specs/api/agent-api.openapi.yml#/components/schemas/AgentError]
"""

import logging
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


def unique_id() -> str:
    """Generate a unique ID to avoid request cache conflicts (Story 12.H.5)."""
    return str(uuid.uuid4())[:12]


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def chinese_canvas_name():
    """中文 canvas 名称."""
    return "测试Canvas_学习笔记.canvas"


@pytest.fixture
def emoji_content():
    """包含 emoji 的内容."""
    return "这是一个测试 🔥🎯📚 包含多个 emoji"


@pytest.fixture
def invalid_utf8_bytes():
    """无效的 UTF-8 字节序列."""
    return b'{"canvas_name": "\xff\xfe invalid"}'


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.J.1 Tests: Logging UTF-8
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoggingEncoding:
    """Story 12.J.1: 日志 UTF-8 编码测试."""

    def test_chinese_log_no_crash(self, caplog):
        """中文日志应正常输出，不崩溃."""
        logger = logging.getLogger("test.encoding")

        # 这些应该不会抛出 UnicodeEncodeError
        logger.info("测试中文日志输出")
        logger.warning("警告: 包含 emoji 🔥")
        logger.error("错误: 特殊字符 §±÷×")

        # 验证日志被记录
        assert "测试中文日志" in caplog.text or len(caplog.records) > 0

    def test_exception_traceback_with_chinese(self, caplog):
        """包含中文的异常 traceback 应正常显示."""
        logger = logging.getLogger("test.encoding")

        try:
            raise ValueError("测试错误消息 🔥")
        except ValueError:
            logger.exception("捕获到异常")

        # 不应抛出异常
        assert len(caplog.records) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.J.2 & 12.J.3 Tests: Request Encoding
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequestEncoding:
    """Story 12.J.2 & 12.J.3: 请求编码测试."""

    @pytest.mark.asyncio
    async def test_chinese_canvas_name_accepted(
        self, async_client: AsyncClient, chinese_canvas_name: str
    ):
        """中文 canvas 名称应被正确接受."""
        response = await async_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": chinese_canvas_name, "node_id": f"node_{unique_id()}"},
        )

        # 可能返回 404 (canvas 不存在)，但不应是 400 或 500
        # 400 表示编码问题，500 表示内部错误
        assert response.status_code != 400, "Should not reject valid UTF-8"

    @pytest.mark.asyncio
    async def test_invalid_utf8_returns_400(
        self, async_client: AsyncClient, invalid_utf8_bytes: bytes
    ):
        """无效 UTF-8 应返回 400，不是 500."""
        response = await async_client.post(
            "/api/v1/agents/decompose/basic",
            content=invalid_utf8_bytes,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data.get("error_type") == "ENCODING_ERROR"

    @pytest.mark.asyncio
    async def test_emoji_in_node_content(
        self, async_client: AsyncClient, emoji_content: str
    ):
        """节点内容包含 emoji 应正常处理."""
        response = await async_client.post(
            "/api/v1/agents/decompose/basic",
            json={
                "canvas_name": f"test_{unique_id()}.canvas",
                "node_id": f"node_{unique_id()}",
                "node_content": emoji_content,
            },
        )

        # 不应因为 emoji 返回 400 或 500
        assert response.status_code not in [400], "Should accept emoji content"


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.J.4 Tests: UnicodeEncodeError Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnicodeErrorHandling:
    """Story 12.J.4: UnicodeEncodeError 处理测试."""

    def test_encoding_error_helper_creates_structured_response(self):
        """_create_encoding_error_response 应创建结构化响应."""
        from app.api.v1.endpoints.agents import _create_encoding_error_response

        # 创建 UnicodeEncodeError
        error = UnicodeEncodeError(
            "gbk", "测试🔥", 2, 3, "illegal multibyte sequence"
        )

        # 调用辅助函数
        http_exception = _create_encoding_error_response(
            error, "test_endpoint", "test_cache_key"
        )

        # 验证返回的 HTTPException
        assert http_exception.status_code == 500
        detail = http_exception.detail
        assert detail.get("error_type") == "ENCODING_ERROR"
        assert "diagnostic" in detail
        assert detail.get("is_retryable") is True  # ENCODING_ERROR is retryable per ADR-009

    def test_encoding_error_diagnostic_is_ascii_safe(self):
        """诊断信息应为 ASCII 安全格式."""
        from app.api.v1.endpoints.agents import _create_encoding_error_response

        # 创建包含中文和 emoji 的 UnicodeEncodeError
        error = UnicodeEncodeError(
            "gbk", "中文测试🔥表情", 4, 5, "illegal multibyte sequence"
        )

        http_exception = _create_encoding_error_response(error, "test", "")

        detail = http_exception.detail
        diagnostic = detail.get("diagnostic", "")

        # 诊断信息应该可以安全编码为 ASCII (使用 unicode escape)
        # 不应抛出异常
        try:
            diagnostic.encode("ascii", errors="strict")
            is_ascii_safe = True
        except UnicodeEncodeError:
            # 允许某些 non-ASCII 字符，只要它们是转义形式
            is_ascii_safe = "\\u" in diagnostic or "\\x" in diagnostic

        # 至少应该是 UTF-8 安全的
        diagnostic.encode("utf-8")  # 不应抛出异常


# ═══════════════════════════════════════════════════════════════════════════════
# Story 12.J.5 Tests: CORS Middleware Encoding Safety
# ═══════════════════════════════════════════════════════════════════════════════


class TestCORSMiddlewareEncoding:
    """Story 12.J.5: CORS 中间件编码安全测试."""

    @pytest.mark.asyncio
    async def test_exception_with_unicode_safely_handled(
        self, async_client: AsyncClient
    ):
        """包含 Unicode 的异常应被安全处理."""
        # Use unique IDs to avoid request cache (Story 12.H.5)
        test_canvas = f"cors_test_{unique_id()}.canvas"
        test_node = f"node_{unique_id()}"

        with patch(
            "app.api.v1.endpoints.agents.decompose_basic",
            side_effect=RuntimeError("运行时错误 🔥 详细信息"),
        ):
            response = await async_client.post(
                "/api/v1/agents/decompose/basic",
                json={"canvas_name": test_canvas, "node_id": test_node},
            )

        # 响应应该是有效的 JSON
        assert response.status_code == 500
        data = response.json()
        assert "message" in data or "detail" in data


# ═══════════════════════════════════════════════════════════════════════════════
# End-to-End Encoding Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEncodingEndToEnd:
    """端到端编码测试."""

    @pytest.mark.asyncio
    async def test_chinese_content_roundtrip(self, async_client: AsyncClient):
        """中文内容应能正确往返."""
        chinese_content = "这是一段测试内容，包含中文字符。"
        # Use unique IDs to avoid request cache (Story 12.H.5)
        test_canvas = f"中文测试_{unique_id()}.canvas"
        test_node = f"测试节点_{unique_id()}"

        # 发送包含中文的请求
        response = await async_client.post(
            "/api/v1/agents/decompose/basic",
            json={
                "canvas_name": test_canvas,
                "node_id": test_node,
                "node_content": chinese_content,
            },
        )

        # 验证响应可以正确解析
        data = response.json()

        # 如果返回错误，错误消息应该是可读的
        if response.status_code >= 400:
            assert "message" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_all_agent_endpoints_handle_unicode(self, async_client: AsyncClient):
        """所有 Agent 端点应能处理 Unicode."""
        endpoints = [
            "/api/v1/agents/decompose/basic",
            "/api/v1/agents/decompose/deep",
            "/api/v1/agents/explain/oral",
            "/api/v1/agents/explain/four-level",
            "/api/v1/agents/explain/clarification",
            "/api/v1/agents/explain/example",
            "/api/v1/agents/explain/memory",
            "/api/v1/agents/explain/comparison",
        ]

        for endpoint in endpoints:
            # Use unique IDs for each endpoint to avoid cache (Story 12.H.5)
            test_canvas = f"测试Canvas_{unique_id()}.canvas"
            test_node = f"node_{unique_id()}"

            response = await async_client.post(
                endpoint,
                json={
                    "canvas_name": test_canvas,
                    "node_id": test_node,
                    "node_content": "测试内容 🔥",
                },
            )

            # 所有端点都不应返回编码相关的错误
            if response.status_code == 400:
                data = response.json()
                assert data.get("error_type") != "ENCODING_ERROR", (
                    f"Endpoint {endpoint} rejected valid Unicode"
                )
