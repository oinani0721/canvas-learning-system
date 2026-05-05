"""Story 2.5.X Task 1 — Candidate writer 单元测试 (C+ 渐进式确认).

覆盖:
- AC #1: candidate 写入 frontmatter `error_candidates[]` (不进 errors[])
- AC #1: candidate 含 6 状态机初始 status=pending + source=ai_suggested
- AC #1: candidate 阶段不调用 Graphiti (graphiti = "skipped_candidate_mode")
- AC #3: dedupe 不重复添加 (同 pedagogy_type+description+node_id 已存在则 update last_seen_at + seen_count + seen_sessions)
- AC #3: dedupe hash 不含 session_id (跨 session 同错应 update 不 append)
- write_error_dual mode 路由 (candidate_only 默认 / write_confirmed legacy)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import yaml

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_writer import (
    CANDIDATE_INITIAL_STATUS,
    CANDIDATE_SOURCE_AI,
    write_candidate_to_frontmatter,
    write_candidate_to_frontmatter_async,
    write_error_dual,
)


def _make_error(**overrides) -> ClassifiedError:
    """构造测试用 ClassifiedError (复用 v1.0 测试 fixture 风格)."""
    base = {
        "legacy_type": ErrorType.KNOWLEDGE_GAP,
        "pedagogy_type": PedagogyErrorType.CONCEPTUAL_CONFUSION,
        "description": "学生混淆了 admissibility 和 consistency",
        "context": "对话第 3 轮",
        "confidence": 0.85,
        "legacy_remedy": RemedyStrategy.BACKTRACK_DEFINITION,
        "pedagogy_remedies": [RemedyStrategy.DISCRIMINATION_COMPARISON],
        "sub_tags": ["synonym_confusion"],
    }
    base.update(overrides)
    return ClassifiedError(**base)


def _make_md_with_frontmatter(tmp_path, body: str = "# Body\n") -> "Path":
    """创建测试节点 .md 含基础 frontmatter (无 errors / candidates)."""
    f = tmp_path / "test_node.md"
    f.write_text(
        "---\n"
        "type: concept\n"
        "board_name: UAT\n"
        "mastery_score: 0.30\n"
        "---\n" + body,
        encoding="utf-8",
    )
    return f


# ════════════════════════════════════════════════════════════════════
# AC #1 — candidate 写入 frontmatter `error_candidates[]`
# ════════════════════════════════════════════════════════════════════


def test_candidate_writes_to_error_candidates_array(tmp_path):
    """AC #1: candidate 写入 error_candidates[] 不写 errors[]."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    ok, candidate_id = write_candidate_to_frontmatter(
        f,
        error,
        node_id="节点/test_node.md",
        session_id="s-2026-05-04-001",
        group_id="cs_61b:main",
    )

    assert ok is True
    assert candidate_id is not None

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])

    # error_candidates[] 写入
    assert "error_candidates" in fm_dict
    assert len(fm_dict["error_candidates"]) == 1
    cand = fm_dict["error_candidates"][0]

    # 6 状态机初始字段 (AC #2 配套)
    assert cand["status"] == CANDIDATE_INITIAL_STATUS == "pending"
    assert cand["source"] == CANDIDATE_SOURCE_AI == "ai_suggested"

    # candidate 必填字段 (Story 2.5.X spec AC #1)
    assert cand["id"] == candidate_id
    assert cand["pedagogy_type"] == "conceptual_confusion"
    assert cand["legacy_type"] == "knowledge_gap"
    assert cand["description"] == "学生混淆了 admissibility 和 consistency"
    assert cand["confidence"] == 0.85
    assert cand["confidence_source"] == "llm"
    assert cand["session_id"] == "s-2026-05-04-001"
    assert cand["group_id"] == "cs_61b:main"
    assert cand["node_id"] == "节点/test_node.md"
    assert cand["seen_sessions"] == ["s-2026-05-04-001"]
    assert cand["seen_count"] == 1
    assert "candidate_dedupe_hash" in cand
    assert cand["status_changed_at"] is None  # AC #2: 初始未变更

    # AC #1: errors[] 不应被写入
    assert "errors" not in fm_dict or fm_dict.get("errors") in (None, [])


def test_candidate_writes_optional_metadata_fields(tmp_path):
    """AC #1: ai_reason / evidence_turns / raw_dialog_excerpt 字段可选写入 (Task 5 升级 LLM 后填)."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    ok, _ = write_candidate_to_frontmatter(
        f,
        error,
        node_id="节点/test_node.md",
        session_id="s-1",
        ai_reason="用户混淆了 X 与 Y",
        evidence_turns=[3, 5],
        raw_dialog_excerpt="学习者: X 就是 Y 吧\nAI: 不对...",
    )

    assert ok is True
    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    cand = fm_dict["error_candidates"][0]
    assert cand["ai_reason"] == "用户混淆了 X 与 Y"
    assert cand["evidence_turns"] == [3, 5]
    assert cand["raw_dialog_excerpt"] == "学习者: X 就是 Y 吧\nAI: 不对..."


def test_candidate_optional_metadata_defaults_to_none_or_empty(tmp_path):
    """AC #1: 未提供可选字段时, ai_reason/raw_dialog_excerpt = None, evidence_turns = []."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    ok, _ = write_candidate_to_frontmatter(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )
    assert ok is True
    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    cand = fm_dict["error_candidates"][0]
    assert cand["ai_reason"] is None
    assert cand["evidence_turns"] == []
    assert cand["raw_dialog_excerpt"] is None


# ════════════════════════════════════════════════════════════════════
# AC #3 — dedupe 不重复添加 (复用 errors[] hash, 不含 session_id)
# ════════════════════════════════════════════════════════════════════


def test_candidate_dedupe_updates_existing_not_append(tmp_path):
    """AC #3: 同 pedagogy_type+description+node_id 已存在 → update last_seen_at/seen_count, 不 append."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    # 第 1 次写入
    ok1, id1 = write_candidate_to_frontmatter(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )
    assert ok1 is True

    # 第 2 次同样的错误 (同 session)
    ok2, id2 = write_candidate_to_frontmatter(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )
    assert ok2 is True
    assert id2 == id1  # AC #3: 返回同一 id

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    candidates = fm_dict["error_candidates"]

    # AC #3: 仍然只有 1 条 (update 不 append)
    assert len(candidates) == 1
    assert candidates[0]["seen_count"] == 2
    assert candidates[0]["seen_sessions"] == ["s-1"]  # 同 session 不重复加入


def test_candidate_dedupe_hash_excludes_session_id(tmp_path):
    """AC #3: 跨 session 同错误应 update + 加入 seen_sessions[], 不 append."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    # session A 写一次
    ok1, id1 = write_candidate_to_frontmatter(
        f, error, node_id="节点/test_node.md", session_id="s-A"
    )
    assert ok1 is True

    # session B 写同样错误 (跨 session)
    ok2, id2 = write_candidate_to_frontmatter(
        f, error, node_id="节点/test_node.md", session_id="s-B"
    )
    assert ok2 is True
    assert id2 == id1  # 仍是同一 candidate

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    candidates = fm_dict["error_candidates"]

    # 仍然只有 1 条
    assert len(candidates) == 1
    assert candidates[0]["seen_count"] == 2
    # AC #3: 两个 session 都加入 seen_sessions
    assert set(candidates[0]["seen_sessions"]) == {"s-A", "s-B"}


def test_candidate_dedupe_takes_max_confidence(tmp_path):
    """ChatGPT Round-2 修正: dedupe 时 confidence 取 max (新>旧才更新)."""
    f = _make_md_with_frontmatter(tmp_path)
    error_low = _make_error(confidence=0.65)
    error_high = _make_error(confidence=0.92)

    write_candidate_to_frontmatter(
        f, error_low, node_id="节点/test_node.md", session_id="s-1"
    )
    write_candidate_to_frontmatter(
        f, error_high, node_id="节点/test_node.md", session_id="s-2"
    )

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    cand = fm_dict["error_candidates"][0]
    assert cand["confidence"] == 0.92  # 取 max


def test_candidate_different_descriptions_append_separately(tmp_path):
    """AC #3 反例: 不同 description → 不同 hash → append 新条 (非 dedupe)."""
    f = _make_md_with_frontmatter(tmp_path)
    error_a = _make_error(description="错误 A")
    error_b = _make_error(description="错误 B")

    write_candidate_to_frontmatter(
        f, error_a, node_id="节点/test_node.md", session_id="s-1"
    )
    write_candidate_to_frontmatter(
        f, error_b, node_id="节点/test_node.md", session_id="s-1"
    )

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    assert len(fm_dict["error_candidates"]) == 2  # 两条独立 candidate


# ════════════════════════════════════════════════════════════════════
# write_error_dual mode 路由 (Task 1.1 + 1.2)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dual_mode_default_is_candidate_only(tmp_path):
    """Task 1.2: write_error_dual 默认 mode = 'candidate_only'."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    result = await write_error_dual(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )

    assert result["mode"] == "candidate_only"
    assert result["frontmatter"] is True
    assert result["graphiti"] == "skipped_candidate_mode"  # AC #1: candidate 阶段不进 Graphiti
    assert "candidate_id" in result
    assert result["candidate_id"] is not None


@pytest.mark.asyncio
async def test_dual_mode_candidate_only_writes_candidates_not_errors(tmp_path):
    """AC #1: candidate_only 模式写入 error_candidates[], 不写 errors[]."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    await write_error_dual(
        f, error, node_id="节点/test_node.md", session_id="s-1", mode="candidate_only"
    )

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    assert "error_candidates" in fm_dict
    assert len(fm_dict["error_candidates"]) == 1
    # errors[] 不应有写入
    assert "errors" not in fm_dict or fm_dict.get("errors") in (None, [])


@pytest.mark.asyncio
async def test_dual_mode_candidate_only_does_not_call_graphiti(tmp_path):
    """AC #1: candidate_only 模式不应启动 Graphiti async task."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    with patch("app.services.error_writer.write_error_to_graphiti") as mock_graphiti:
        result = await write_error_dual(
            f,
            error,
            node_id="节点/test_node.md",
            session_id="s-1",
            mode="candidate_only",
        )

    # candidate_only 模式下 graphiti 函数不应被调用
    assert mock_graphiti.call_count == 0
    assert result["graphiti"] == "skipped_candidate_mode"


@pytest.mark.asyncio
async def test_dual_mode_write_confirmed_legacy_behavior(tmp_path):
    """write_confirmed 模式保持 Story 2.5 v1.0 行为 (写 errors[] + Graphiti)."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    with patch(
        "app.services.error_writer.write_error_to_graphiti"
    ) as mock_graphiti:
        # asyncio.create_task 内部调用 write_error_to_graphiti
        # 测试只验证 mode 路由正确, 不验证 fire-and-forget 实际触发
        result = await write_error_dual(
            f,
            error,
            node_id="节点/test_node.md",
            session_id="s-1",
            mode="write_confirmed",
        )

    assert result["mode"] == "write_confirmed"
    assert result["frontmatter"] is True
    assert result["graphiti"] == "queued"  # fire-and-forget 调度
    assert "error_id" in result

    # write_confirmed 写 errors[] 不写 error_candidates[]
    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    assert "errors" in fm_dict
    assert len(fm_dict["errors"]) == 1
    # error_candidates[] 不应被写入
    assert (
        "error_candidates" not in fm_dict
        or fm_dict.get("error_candidates") in (None, [])
    )


@pytest.mark.asyncio
async def test_dual_mode_write_confirmed_returns_error_id_not_candidate_id(tmp_path):
    """write_confirmed 模式返回 'error_id' 字段, 不是 'candidate_id'."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    result = await write_error_dual(
        f, error, node_id="节点/test_node.md", session_id="s-1", mode="write_confirmed"
    )

    assert "error_id" in result
    assert "candidate_id" not in result
    assert result["error_id"] is not None


@pytest.mark.asyncio
async def test_dual_mode_candidate_only_returns_candidate_id_not_error_id(tmp_path):
    """candidate_only 模式返回 'candidate_id', 不是 'error_id'."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    result = await write_error_dual(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )

    assert "candidate_id" in result
    assert "error_id" not in result


# ════════════════════════════════════════════════════════════════════
# Per-file lock async wrapper
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_async_wrapper_uses_per_file_lock(tmp_path):
    """async wrapper 应复用 _get_file_lock per-file 锁防并发数据丢失."""
    f = _make_md_with_frontmatter(tmp_path)
    error = _make_error()

    ok, candidate_id = await write_candidate_to_frontmatter_async(
        f, error, node_id="节点/test_node.md", session_id="s-1"
    )

    assert ok is True
    assert candidate_id is not None
    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    assert len(fm_dict["error_candidates"]) == 1


# ════════════════════════════════════════════════════════════════════
# 边界 / 失败路径
# ════════════════════════════════════════════════════════════════════


def test_candidate_file_not_found_returns_false(tmp_path):
    """文件不存在 → 返回 (False, None) + warning log."""
    f = tmp_path / "missing.md"  # 不创建
    error = _make_error()

    ok, candidate_id = write_candidate_to_frontmatter(
        f, error, node_id="节点/missing.md"
    )
    assert ok is False
    assert candidate_id is None


def test_candidate_appends_to_existing_errors_array_independently(tmp_path):
    """已有 errors[] 时, 新加 error_candidates[] 不影响 errors[]."""
    f = tmp_path / "node.md"
    f.write_text(
        "---\n"
        "type: concept\n"
        "errors:\n"
        "  - type: careless_slip\n"
        "    description: 老错误\n"
        "    corrected_at: null\n"
        "---\n"
        "# Body\n",
        encoding="utf-8",
    )
    error = _make_error()

    ok, _ = write_candidate_to_frontmatter(
        f, error, node_id="节点/node.md", session_id="s-1"
    )
    assert ok is True

    text = f.read_text(encoding="utf-8")
    fm_dict = yaml.safe_load(text.split("---")[1])
    # 原 errors[] 保留 + 新 error_candidates[] 加入
    assert len(fm_dict["errors"]) == 1
    assert fm_dict["errors"][0]["description"] == "老错误"
    assert len(fm_dict["error_candidates"]) == 1
    assert fm_dict["error_candidates"][0]["description"] == "学生混淆了 admissibility 和 consistency"
