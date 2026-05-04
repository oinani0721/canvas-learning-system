"""Story 2.5 Task 1 — 对话错误提取器单元测试.

覆盖:
- AC #1: 自动提取对话中的错误
- AC #5: 无错误返回空 list, 不产生 false positive
- LLM 失败优雅降级到空 list
- extract_and_classify 集成 Task 1 + Task 2
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_extractor import (
    DialogMessage,
    ErrorExtractor,
    ExtractedError,
)


# ════════════════════════════════════════════════════════════════════
# 基础提取行为
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_extract_empty_messages_returns_empty():
    """空消息 list → 空 list."""
    extractor = ErrorExtractor()
    result = await extractor.extract_errors_from_dialog([], node_id="x")
    assert result == []


@pytest.mark.asyncio
async def test_extract_no_errors_returns_empty():
    """LLM 返回 [] (对话无错误) → 空 list (AC #5)."""
    extractor = ErrorExtractor()
    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=[])
    ):
        messages = [
            DialogMessage(role="user", content="什么是特征值?"),
            DialogMessage(role="assistant", content="特征值是 ..."),
        ]
        result = await extractor.extract_errors_from_dialog(messages, "节点/X.md")
    assert result == []


@pytest.mark.asyncio
async def test_extract_with_errors_parses_correctly():
    """LLM 返回 N 个错误 → ExtractedError 列表."""
    extractor = ErrorExtractor()
    raw_errors = [
        {
            "description": "学生混淆了 admissibility 和 consistency",
            "context": "对话第 2 轮: 学生说它们一样",
        },
        {
            "description": "学生错认为所有矩阵都有实特征值",
            "context": "对话第 4 轮",
        },
    ]
    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=raw_errors)
    ):
        messages = [DialogMessage(role="user", content="...")]
        result = await extractor.extract_errors_from_dialog(messages, "节点/X.md")

    assert len(result) == 2
    assert all(isinstance(e, ExtractedError) for e in result)
    assert result[0].description == "学生混淆了 admissibility 和 consistency"
    assert "对话第 2 轮" in result[0].context
    assert result[1].description == "学生错认为所有矩阵都有实特征值"


@pytest.mark.asyncio
async def test_extract_filters_empty_descriptions():
    """LLM 返回含空 description 的项 → 过滤掉 (AC #5 防 false positive)."""
    extractor = ErrorExtractor()
    raw_errors = [
        {"description": "", "context": "..."},  # 空描述, 应过滤
        {"description": "  ", "context": "..."},  # 空白描述, 应过滤
        {"description": "真错误", "context": "ctx"},
    ]
    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=raw_errors)
    ):
        messages = [DialogMessage(role="user", content="...")]
        result = await extractor.extract_errors_from_dialog(messages, "x")

    assert len(result) == 1
    assert result[0].description == "真错误"


@pytest.mark.asyncio
async def test_extract_llm_failure_returns_empty():
    """LLM 抛异常 → 优雅降级返回空 list."""
    extractor = ErrorExtractor()
    with patch.object(
        extractor,
        "_llm_extract",
        new=AsyncMock(side_effect=RuntimeError("LLM API down")),
    ):
        messages = [DialogMessage(role="user", content="...")]
        result = await extractor.extract_errors_from_dialog(messages, "x")
    assert result == []


# ════════════════════════════════════════════════════════════════════
# Markdown fence 处理 (LLM 偶尔加 ```json ... ```)
# ════════════════════════════════════════════════════════════════════


def test_strip_markdown_fence_with_json_lang():
    """LLM 输出 ```json\\n[...]\\n``` 应被剥离."""
    extractor = ErrorExtractor()
    raw = '```json\n[{"description": "x", "context": "y"}]\n```'
    stripped = extractor._strip_markdown_fence(raw)
    assert stripped == '[{"description": "x", "context": "y"}]'


def test_strip_markdown_fence_without_lang():
    """LLM 输出 ```\\n[...]\\n``` (无语言标记) 应被剥离."""
    extractor = ErrorExtractor()
    raw = '```\n[{"description": "x"}]\n```'
    stripped = extractor._strip_markdown_fence(raw)
    assert stripped == '[{"description": "x"}]'


def test_strip_markdown_fence_no_fence():
    """无 fence 的纯 JSON 不应被改动."""
    extractor = ErrorExtractor()
    raw = '[{"description": "x"}]'
    assert extractor._strip_markdown_fence(raw) == raw


# ════════════════════════════════════════════════════════════════════
# 对话格式化
# ════════════════════════════════════════════════════════════════════


def test_format_dialog_uses_roles_in_chinese():
    """对话格式化用中文角色标签 (学习者 / AI 老师)."""
    extractor = ErrorExtractor()
    messages = [
        DialogMessage(role="user", content="问题 A"),
        DialogMessage(role="assistant", content="回答 A"),
    ]
    formatted = extractor._format_dialog(messages)
    assert "学习者" in formatted
    assert "AI 老师" in formatted
    assert "问题 A" in formatted
    assert "回答 A" in formatted
    assert "[第 1 轮 学习者]" in formatted
    assert "[第 2 轮 AI 老师]" in formatted


# ════════════════════════════════════════════════════════════════════
# extract_and_classify 集成 (Task 1 + Task 2 端到端)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_extract_and_classify_full_pipeline():
    """完整链路: dialog → extract → classify_with_pedagogy → ClassifiedError list."""
    extractor = ErrorExtractor()

    fake_classified = ClassifiedError(
        legacy_type=ErrorType.SUPERFICIAL,
        pedagogy_type=PedagogyErrorType.METACOGNITIVE_ERROR,
        description="学生不能迁移定义到新场景",
        context="对话第 3 轮",
        confidence=0.82,
        legacy_remedy=extractor._classifier.__class__.__module__  # placeholder
        and __import__(
            "app.graphiti.entity_types", fromlist=["RemedyStrategy"]
        ).RemedyStrategy.DISCRIMINATION_TRANSFER,
        pedagogy_remedies=[
            __import__(
                "app.graphiti.entity_types", fromlist=["RemedyStrategy"]
            ).RemedyStrategy.TRANSFER_SELF_EXPLANATION
        ],
        sub_tags=[],
    )

    with patch.object(
        extractor,
        "_llm_extract",
        new=AsyncMock(
            return_value=[
                {
                    "description": "学生不能迁移定义",
                    "context": "对话第 3 轮",
                }
            ]
        ),
    ), patch.object(
        extractor._classifier,
        "classify_with_pedagogy",
        new=AsyncMock(return_value=fake_classified),
    ):
        messages = [
            DialogMessage(role="user", content="特征值?"),
            DialogMessage(role="assistant", content="..."),
        ]
        result = await extractor.extract_and_classify(
            messages, node_id="节点/X.md", session_id="sess1"
        )

    assert len(result) == 1
    assert isinstance(result[0], ClassifiedError)
    assert result[0].pedagogy_type == PedagogyErrorType.METACOGNITIVE_ERROR
    assert result[0].confidence == 0.82


@pytest.mark.asyncio
async def test_extract_and_classify_no_errors_returns_empty():
    """无错误时 extract_and_classify 也返回空 list (短路, 不调 classifier)."""
    extractor = ErrorExtractor()
    classifier_mock = AsyncMock()

    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=[])
    ), patch.object(
        extractor._classifier,
        "classify_with_pedagogy",
        new=classifier_mock,
    ):
        result = await extractor.extract_and_classify(
            [DialogMessage(role="user", content="x")],
            node_id="x",
            session_id="x",
        )

    assert result == []
    classifier_mock.assert_not_called()  # 短路, classifier 没被调


@pytest.mark.asyncio
async def test_extract_and_classify_continues_on_classify_failure():
    """单条 classify 失败不影响其他错误的处理."""
    extractor = ErrorExtractor()
    raw_errors = [
        {"description": "错误 1", "context": ""},
        {"description": "错误 2", "context": ""},
    ]

    fake_classified = ClassifiedError(
        legacy_type=ErrorType.PROBLEM_FRAMING,
        pedagogy_type=PedagogyErrorType.CARELESS_SLIP,
        description="错误 2",
        context="",
        confidence=0.8,
        legacy_remedy=__import__(
            "app.graphiti.entity_types", fromlist=["RemedyStrategy"]
        ).RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM,
        pedagogy_remedies=[
            __import__(
                "app.graphiti.entity_types", fromlist=["RemedyStrategy"]
            ).RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM
        ],
        sub_tags=[],
    )

    classify_results = [
        RuntimeError("第 1 条 classify 崩"),
        fake_classified,
    ]

    async def _mock_classify(*args, **kwargs):
        result = classify_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=raw_errors)
    ), patch.object(
        extractor._classifier,
        "classify_with_pedagogy",
        side_effect=_mock_classify,
    ):
        result = await extractor.extract_and_classify(
            [DialogMessage(role="user", content="x")],
            node_id="x",
            session_id="x",
        )

    # 只有第 2 条成功
    assert len(result) == 1
    assert result[0].description == "错误 2"
