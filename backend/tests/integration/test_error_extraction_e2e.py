"""Story 2.5 Task 6 — e2e 集成测试.

覆盖完整对话流: dialog → ErrorExtractor.extract_and_classify → write_error_dual
→ frontmatter (双标签) + Graphiti called.

也覆盖 record_error MCP tool 端到端: input → 双标签分类 → 双写 → output schema.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.error_extractor import (
    DialogMessage,
    ErrorExtractor,
)


# ════════════════════════════════════════════════════════════════════
# E2E #1 — ErrorExtractor.extract_and_classify → write_error_dual
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_dialog_to_frontmatter_full_pipeline(tmp_path):
    """完整链路: dialog → extract → classify (双标签) → frontmatter 写入.

    模拟用户与 AI 关于"特征值"的对话, 用户犯了"混淆 admissibility 与 consistency"错误,
    backend 应该:
    1. 提取此错误
    2. 分类为 KNOWLEDGE_GAP (legacy) + CONCEPTUAL_CONFUSION (pedagogy)
    3. 写入 .md frontmatter `errors[]` 含双标签
    """
    # 创建临时节点 .md
    node_file = tmp_path / "admissibility.md"
    node_file.write_text(
        "---\ntype: concept\nmastery_score: 0.45\n---\n\n"
        "# Admissibility\n\nAdmissibility 是 ...\n",
        encoding="utf-8",
    )

    extractor = ErrorExtractor()

    # Mock LLM 提取阶段返回 1 个错误
    mock_extract = AsyncMock(
        return_value=[
            {
                "description": "学生混淆了 admissibility 和 consistency",
                "context": "对话第 2 轮: 学生说它们是一样的",
            }
        ]
    )

    # Mock 分类阶段返回 KNOWLEDGE_GAP + 0.85 confidence
    mock_classify = AsyncMock(
        return_value=(ErrorType.KNOWLEDGE_GAP, 0.85)
    )

    # Mock memory_service (Graphiti 写入不阻塞)
    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    with patch.object(
        extractor, "_llm_extract", new=mock_extract
    ), patch.object(
        extractor._classifier,
        "_llm_classify_with_confidence",
        new=mock_classify,
    ), patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ):
        messages = [
            DialogMessage(role="user", content="admissibility 就是 consistency 吧?"),
            DialogMessage(role="assistant", content="不是, 它们是不同的概念..."),
        ]

        # Step 1: 提取 + 分类
        classified_list = await extractor.extract_and_classify(
            messages, node_id="admissibility", session_id="sess1"
        )

        assert len(classified_list) == 1
        classified = classified_list[0]
        assert classified.legacy_type == ErrorType.KNOWLEDGE_GAP
        assert classified.pedagogy_type == PedagogyErrorType.CONCEPTUAL_CONFUSION
        assert classified.confidence == 0.85

        # Step 2: 双写 (引入 write_error_dual)
        from app.services.error_writer import write_error_dual

        result = await write_error_dual(
            file_path=node_file,
            error=classified,
            node_id="admissibility",
            session_id="sess1",
            fire_and_forget_graphiti=False,  # 同步等待 Graphiti
        )

    # 验证结果
    assert result["frontmatter"] is True
    assert result["graphiti"] == "ok"

    # 验证 frontmatter 真的写入双标签
    new_text = node_file.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(new_text.split("---")[1])
    assert "errors" in fm_dict
    assert len(fm_dict["errors"]) == 1

    err_record = fm_dict["errors"][0]
    assert err_record["type"] == "conceptual_confusion"  # PRD pedagogy
    assert err_record["legacy_type"] == "knowledge_gap"  # Story 3.6 兼容
    assert "discrimination_comparison" in err_record["remedy_strategies"]
    assert err_record["confidence"] == 0.85
    assert "学生混淆了 admissibility" in err_record["description"]

    # 验证 Graphiti 被调用
    mock_memory_svc.record_knowledge_entity.assert_called_once()
    call_kwargs = mock_memory_svc.record_knowledge_entity.call_args.kwargs
    assert call_kwargs["event_type"] == "misconception"
    assert call_kwargs["metadata"]["pedagogy_type"] == "conceptual_confusion"
    assert call_kwargs["metadata"]["legacy_type"] == "knowledge_gap"


@pytest.mark.asyncio
async def test_e2e_dialog_no_errors_no_writes(tmp_path):
    """无错误对话 → 无 frontmatter / Graphiti 写入 (AC #5)."""
    node_file = tmp_path / "ok-node.md"
    node_file.write_text("---\ntype: concept\n---\n# OK\n", encoding="utf-8")

    extractor = ErrorExtractor()

    # Mock LLM 提取阶段返回空 list (对话无错误)
    with patch.object(
        extractor, "_llm_extract", new=AsyncMock(return_value=[])
    ):
        classified_list = await extractor.extract_and_classify(
            [
                DialogMessage(role="user", content="什么是特征值?"),
                DialogMessage(role="assistant", content="特征值是 ..."),
            ],
            node_id="ok-node",
            session_id="sess1",
        )

    assert classified_list == []
    # frontmatter 不变 (因为没调 write_error_dual)
    assert "errors:" not in node_file.read_text(encoding="utf-8")


# ════════════════════════════════════════════════════════════════════
# E2E #2 — record_error MCP tool 完整链路 (Task 5)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_record_error_mcp_tool_full_pipeline(tmp_path, monkeypatch):
    """record_error MCP tool input → 双标签分类 → 双写 → 扩展 output schema.

    验证 Task 5 升级后 record_error 端到端工作:
    - 接受 sub_tags 输入 (Story 2.5)
    - 返回 pedagogy_type + pedagogy_remedies + confidence + is_ambiguous (新字段)
    - 保留 error_type + remedy_strategy (Story 3.6 兼容)
    - frontmatter 真写入 + Graphiti 被调用
    """
    # 创建临时 vault + 节点
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    nodes_dir = vault_root / "节点"
    nodes_dir.mkdir()
    node_file = nodes_dir / "transfer-error.md"
    node_file.write_text(
        "---\ntype: concept\n---\n# Transfer Error\n",
        encoding="utf-8",
    )

    # canvas_base_path 是 property 无法 setattr, 改 patch _resolve_node_file_path
    # 直接返回预设 file_path (避免依赖 settings 真值).
    _ = monkeypatch  # 保留参数签名兼容 (虽然不再用 monkeypatch)

    # Mock LLM classify 返回 SUPERFICIAL + confidence 0.7
    mock_classify = AsyncMock(
        return_value=(ErrorType.SUPERFICIAL, 0.7)
    )

    # Mock memory_service
    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)

    # Mock audit guardian (避免 side effect)
    mock_guardian = AsyncMock()
    mock_guardian.record_tool_call = AsyncMock()

    # 调 record_error MCP tool
    from app.mcp.tools.error_tools import record_error
    from app.services.error_classifier import get_error_classifier

    classifier = get_error_classifier()

    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=mock_classify,
    ), patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ), patch(
        "app.mcp.tools.error_tools.get_audit_guardian",
        return_value=mock_guardian,
    ), patch(
        "app.mcp.tools.error_tools._resolve_node_file_path",
        return_value=str(node_file),
    ):
        result = await record_error(
            node_id="节点/transfer-error",
            session_id="sess-e2e",
            error_description="学生不能将定义迁移到新场景",
            context="对话第 4 轮",
            sub_tags=["transfer_failure"],
        )

    # 验证 output schema 含 Story 2.5 + Story 3.6 字段
    assert result["recorded"] is True
    # Story 3.6 legacy fields
    assert result["error_type"] == "superficial"
    assert result["remedy_strategy"] == "discrimination_transfer"
    # Story 2.5 D 方案双标签
    # SUPERFICIAL + sub_tag transfer_failure + 关键词"迁移" → METACOGNITIVE_ERROR
    assert result["pedagogy_type"] == "metacognitive_error"
    assert "transfer_self_explanation" in result["pedagogy_remedies"]
    assert result["confidence"] == 0.7
    assert result["is_ambiguous"] is False  # 0.7 >= 0.6
    assert result["frontmatter_written"] is True
    assert result["graphiti_status"] == "queued"  # HIGH#5 fix (scheduled→queued)

    # 验证 frontmatter 真的写入
    fm_dict = yaml.safe_load(node_file.read_text().split("---")[1])
    assert "errors" in fm_dict
    err_record = fm_dict["errors"][0]
    assert err_record["type"] == "metacognitive_error"
    assert err_record["legacy_type"] == "superficial"
    assert err_record["tags"] == ["transfer_failure"]
    assert "transfer_self_explanation" in err_record["remedy_strategies"]


@pytest.mark.asyncio
async def test_e2e_record_error_low_confidence_marked_ambiguous(
    tmp_path, monkeypatch
):
    """confidence < 0.6 → is_ambiguous=True (PRD AC #2)."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "节点").mkdir()
    node_file = vault_root / "节点" / "low-conf.md"
    node_file.write_text("---\ntype: concept\n---\n# X\n", encoding="utf-8")

    # canvas_base_path 是 property, 用 patch _resolve_node_file_path 替代
    _ = monkeypatch  # 保留参数签名

    mock_classify = AsyncMock(
        return_value=(ErrorType.PROBLEM_FRAMING, 0.45)
    )
    mock_memory_svc = AsyncMock()
    mock_memory_svc.record_knowledge_entity = AsyncMock(return_value=None)
    mock_guardian = AsyncMock()
    mock_guardian.record_tool_call = AsyncMock()

    from app.mcp.tools.error_tools import record_error
    from app.services.error_classifier import get_error_classifier

    classifier = get_error_classifier()

    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=mock_classify,
    ), patch(
        "app.services.memory_service.get_memory_service",
        new=AsyncMock(return_value=mock_memory_svc),
    ), patch(
        "app.mcp.tools.error_tools.get_audit_guardian",
        return_value=mock_guardian,
    ), patch(
        "app.mcp.tools.error_tools._resolve_node_file_path",
        return_value=str(node_file),
    ):
        result = await record_error(
            node_id="节点/low-conf",
            session_id="s",
            error_description="不确定的错误",
        )

    assert result["confidence"] == 0.45
    assert result["is_ambiguous"] is True
    # frontmatter 仍写入 (即使 ambiguous, 数据保留供后续校正)
    assert result["frontmatter_written"] is True


@pytest.mark.asyncio
async def test_e2e_record_error_graphiti_failure_frontmatter_succeeds(
    tmp_path, monkeypatch
):
    """AC #6 — Graphiti 失败时 frontmatter 仍成功 (本地优先)."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "节点").mkdir()
    node_file = vault_root / "节点" / "graphiti-fail.md"
    node_file.write_text("---\ntype: concept\n---\n# X\n", encoding="utf-8")

    # canvas_base_path 是 property, 用 patch _resolve_node_file_path 替代
    _ = monkeypatch  # 保留参数签名

    mock_classify = AsyncMock(
        return_value=(ErrorType.REASONING_FALLACY, 0.8)
    )
    # memory_service 不可用 → ImportError
    mock_get_memory = AsyncMock(side_effect=ImportError("graphiti down"))

    mock_guardian = AsyncMock()
    mock_guardian.record_tool_call = AsyncMock()

    from app.mcp.tools.error_tools import record_error
    from app.services.error_classifier import get_error_classifier

    classifier = get_error_classifier()

    with patch.object(
        classifier,
        "_llm_classify_with_confidence",
        new=mock_classify,
    ), patch(
        "app.services.memory_service.get_memory_service",
        new=mock_get_memory,
    ), patch(
        "app.mcp.tools.error_tools.get_audit_guardian",
        return_value=mock_guardian,
    ), patch(
        "app.services.error_writer.GRAPHITI_RETRY_INTERVAL_S", 0.001
    ), patch(
        "app.mcp.tools.error_tools._resolve_node_file_path",
        return_value=str(node_file),
    ):
        result = await record_error(
            node_id="节点/graphiti-fail",
            session_id="s",
            error_description="学生因果倒置",
        )

    # frontmatter 成功 (本地优先) — 这是 AC #6 关键验证点
    assert result["frontmatter_written"] is True
    # 双标签仍然写入
    assert result["pedagogy_type"] == "procedural_error"
    assert result["error_type"] == "reasoning_fallacy"
    # frontmatter 写入后 Graphiti 仍尝试 (fire-and-forget scheduled)
    # 但调度后失败不阻断 recorded
    assert result["recorded"] is True
    assert result["graphiti_status"] == "queued"  # 任务被调度,实际失败由后台处理
