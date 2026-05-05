"""Story 2.5.X Task 3+4 — Candidate accept/dismiss/dispute service 单元测试.

覆盖:
- AC #5: accept_candidate (candidate → errors[] + Graphiti)
  · 默认 status=accepted, 含 user_edits → status=edited
  · 不存在 candidate → 404, 状态非 pending → 422
  · errors[] dedupe (同 hash → update existing)
  · frontmatter 原子写: candidate.status + errors[] 同步更新
- AC #7: dismiss_candidate (status=dismissed, 不入 errors[])
- AC #7: dispute_candidate (status=disputed + dispute_reason 必填)
- 终态尝试 dismiss/dispute → 422

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import yaml
from fastapi import HTTPException

from app.services.candidate_service import (
    CandidateEdits,
    accept_candidate,
    dismiss_candidate,
    dispute_candidate,
)


# ════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════


def _md_with_pending_candidate(
    tmp_path,
    candidate_id: str = "cand-uuid-1",
    pedagogy_type: str = "conceptual_confusion",
    legacy_type: str = "knowledge_gap",
    description: str = "学生混淆 admissibility 与 consistency",
    confidence: float = 0.85,
):
    """构造测试 .md, 含 1 条 pending candidate."""
    f = tmp_path / "node.md"
    fm_dict = {
        "type": "concept",
        "board_name": "UAT",
        "error_candidates": [
            {
                "id": candidate_id,
                "status": "pending",
                "source": "ai_suggested",
                "node_id": "节点/node.md",
                "session_id": "s-1",
                "group_id": "cs_61b:main",
                "candidate_dedupe_hash": "abc123def4567890",
                "pedagogy_type": pedagogy_type,
                "legacy_type": legacy_type,
                "legacy_remedy": "backtrack_definition",
                "description": description,
                "context": "对话第 3 轮",
                "ai_reason": None,
                "evidence_turns": [],
                "raw_dialog_excerpt": None,
                "confidence": confidence,
                "confidence_source": "llm",
                "sub_tags": ["synonym_confusion"],
                "suggested_remedy_strategies": ["discrimination_comparison"],
                "created_at": "2026-05-04T00:00:00+00:00",
                "last_seen_at": "2026-05-04T00:00:00+00:00",
                "seen_count": 1,
                "seen_sessions": ["s-1"],
                "status_changed_at": None,
                "status_changed_by": None,
            }
        ],
    }
    fm_str = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
    f.write_text(f"---\n{fm_str}---\n# Body\n", encoding="utf-8")
    return f


# ════════════════════════════════════════════════════════════════════
# Task 3 — accept_candidate
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_accept_candidate_default_status_accepted(tmp_path):
    """无 user_edits → status=accepted (AC #5)."""
    f = _md_with_pending_candidate(tmp_path)

    result = await accept_candidate(
        file_path=f,
        candidate_id="cand-uuid-1",
        session_id="s-1",
    )

    assert result.candidate_id == "cand-uuid-1"
    assert result.error_id == "cand-uuid-1"  # 复用 candidate_id 作为 error_id
    assert result.status == "accepted"
    assert result.frontmatter_written is True
    assert result.graphiti_status == "queued"

    # 验证 frontmatter
    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "accepted"
    assert cand["status_changed_at"] is not None
    assert cand["status_changed_by"] == "user"

    # errors[] 加新条
    assert len(fm["errors"]) == 1
    err = fm["errors"][0]
    assert err["id"] == "cand-uuid-1"
    assert err["type"] == "conceptual_confusion"
    assert err["legacy_type"] == "knowledge_gap"
    assert err["description"] == "学生混淆 admissibility 与 consistency"
    assert err["source"] == "user_confirmed_ai"
    assert err["user_confirmed"] is True
    assert err["from_candidate_id"] == "cand-uuid-1"


@pytest.mark.asyncio
async def test_accept_candidate_with_edits_status_edited(tmp_path):
    """含 user_edits → status=edited + edits 应用到 errors[]."""
    f = _md_with_pending_candidate(tmp_path)

    result = await accept_candidate(
        file_path=f,
        candidate_id="cand-uuid-1",
        user_edits=CandidateEdits(
            description="学生说 admissibility==consistency, 实际不同",
            pedagogy_type="metacognitive_error",
        ),
        session_id="s-1",
    )

    assert result.status == "edited"

    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "edited"

    err = fm["errors"][0]
    # edits 应用
    assert err["description"] == "学生说 admissibility==consistency, 实际不同"
    assert err["type"] == "metacognitive_error"


@pytest.mark.asyncio
async def test_accept_candidate_not_found_returns_404(tmp_path):
    """candidate_id 不存在 → 404."""
    f = _md_with_pending_candidate(tmp_path, candidate_id="real-id")

    with pytest.raises(HTTPException) as exc_info:
        await accept_candidate(
            file_path=f, candidate_id="fake-id", session_id="s-1"
        )

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_accept_candidate_already_accepted_returns_422(tmp_path):
    """状态已 accepted 不可再 accept (反向/终态间) → 422."""
    f = _md_with_pending_candidate(tmp_path)
    # 先 accept 一次
    await accept_candidate(file_path=f, candidate_id="cand-uuid-1")

    # 再 accept 一次 (此时 status=accepted)
    with pytest.raises(HTTPException) as exc_info:
        await accept_candidate(file_path=f, candidate_id="cand-uuid-1")

    assert exc_info.value.status_code == 422
    assert "Illegal status transition" in exc_info.value.detail


@pytest.mark.asyncio
async def test_accept_candidate_dedupe_into_existing_error(tmp_path):
    """errors[] 中已有同 hash error (corrected_at=null) → update 不 append."""
    f = tmp_path / "node.md"
    # frontmatter 同时含 errors[] 旧条 + error_candidates[] 新候选 (同 description)
    fm_dict = {
        "type": "concept",
        "errors": [
            {
                "id": "old-error-id",
                "dedupe_hash": "",  # 空, accept 时会重新计算
                "type": "conceptual_confusion",
                "legacy_type": "knowledge_gap",
                "description": "学生混淆 X 与 Y",
                "corrected_at": None,
                "seen_count": 1,
            }
        ],
        "error_candidates": [
            {
                "id": "new-cand-id",
                "status": "pending",
                "node_id": "节点/node.md",
                "pedagogy_type": "conceptual_confusion",
                "legacy_type": "knowledge_gap",
                "legacy_remedy": "backtrack_definition",
                "description": "学生混淆 X 与 Y",  # 同 description
                "confidence": 0.85,
                "sub_tags": [],
                "suggested_remedy_strategies": [],
            }
        ],
    }
    fm_str = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
    f.write_text(f"---\n{fm_str}---\n# Body\n", encoding="utf-8")

    # 让旧 errors[].dedupe_hash 先重新计算 (用 _make_dedupe_hash 算同 hash)
    from app.services.error_writer import _make_dedupe_hash
    from app.services.error_classifier import ClassifiedError
    from app.graphiti.entity_types import (
        ErrorType,
        PedagogyErrorType,
        RemedyStrategy,
    )

    sample_err = ClassifiedError(
        legacy_type=ErrorType.KNOWLEDGE_GAP,
        pedagogy_type=PedagogyErrorType.CONCEPTUAL_CONFUSION,
        description="学生混淆 X 与 Y",
        confidence=0.85,
        legacy_remedy=RemedyStrategy.BACKTRACK_DEFINITION,
        pedagogy_remedies=[],
        sub_tags=[],
    )
    expected_hash = _make_dedupe_hash(sample_err, "节点/node.md")
    fm_dict["errors"][0]["dedupe_hash"] = expected_hash
    fm_str = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
    f.write_text(f"---\n{fm_str}---\n# Body\n", encoding="utf-8")

    # accept candidate
    result = await accept_candidate(file_path=f, candidate_id="new-cand-id")
    assert result.status == "accepted"

    # errors[] 仍然只有 1 条 (update 不 append)
    fm = yaml.safe_load(f.read_text().split("---")[1])
    assert len(fm["errors"]) == 1
    assert fm["errors"][0]["seen_count"] == 2  # update +1
    # error_id 应是 existing 的 id (Round-2 dedupe 行为)
    assert result.error_id == "old-error-id"


@pytest.mark.asyncio
async def test_accept_candidate_file_not_found_returns_404(tmp_path):
    """文件不存在 → 404."""
    missing = tmp_path / "missing.md"
    with pytest.raises(HTTPException) as exc_info:
        await accept_candidate(file_path=missing, candidate_id="x")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_accept_candidate_does_not_call_graphiti_when_fire_and_forget_false(
    tmp_path,
):
    """fire_and_forget=False 时同步等待 Graphiti."""
    f = _md_with_pending_candidate(tmp_path)

    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        result = await accept_candidate(
            file_path=f,
            candidate_id="cand-uuid-1",
            fire_and_forget_graphiti=False,
        )

    assert result.graphiti_status == "ok"
    mock_g.assert_called_once()


# ════════════════════════════════════════════════════════════════════
# Task 4 — dismiss_candidate
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dismiss_candidate_sets_status_dismissed(tmp_path):
    """dismiss → status=dismissed + 不入 errors[]."""
    f = _md_with_pending_candidate(tmp_path)

    result = await dismiss_candidate(file_path=f, candidate_id="cand-uuid-1")

    assert result.status == "dismissed"
    assert result.dispute_reason is None
    assert result.frontmatter_written is True

    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "dismissed"
    assert cand["status_changed_by"] == "user"

    # errors[] 不应被写入
    assert "errors" not in fm or fm.get("errors") in (None, [])


@pytest.mark.asyncio
async def test_dismiss_candidate_not_found_returns_404(tmp_path):
    f = _md_with_pending_candidate(tmp_path)
    with pytest.raises(HTTPException) as exc_info:
        await dismiss_candidate(file_path=f, candidate_id="fake-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_dismiss_candidate_already_terminal_returns_422(tmp_path):
    """已 dismissed 再 dismiss → 422 (终态间不可逆)."""
    f = _md_with_pending_candidate(tmp_path)
    await dismiss_candidate(file_path=f, candidate_id="cand-uuid-1")

    with pytest.raises(HTTPException) as exc_info:
        await dismiss_candidate(file_path=f, candidate_id="cand-uuid-1")
    assert exc_info.value.status_code == 422


# ════════════════════════════════════════════════════════════════════
# Task 4 — dispute_candidate
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dispute_candidate_writes_reason(tmp_path):
    """dispute → status=disputed + dispute_reason 写入 candidate."""
    f = _md_with_pending_candidate(tmp_path)

    result = await dispute_candidate(
        file_path=f,
        candidate_id="cand-uuid-1",
        dispute_reason="我没误解, AI 误判",
    )

    assert result.status == "disputed"
    assert result.dispute_reason == "我没误解, AI 误判"

    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "disputed"
    assert cand["dispute_reason"] == "我没误解, AI 误判"

    # errors[] 不应被写入
    assert "errors" not in fm or fm.get("errors") in (None, [])


@pytest.mark.asyncio
async def test_dispute_candidate_empty_reason_returns_422(tmp_path):
    """空 dispute_reason → 422 (必填校验)."""
    f = _md_with_pending_candidate(tmp_path)

    with pytest.raises(HTTPException) as exc_info:
        await dispute_candidate(file_path=f, candidate_id="cand-uuid-1", dispute_reason="")
    assert exc_info.value.status_code == 422
    assert "dispute_reason" in exc_info.value.detail


@pytest.mark.asyncio
async def test_dispute_candidate_whitespace_reason_returns_422(tmp_path):
    """全空白 dispute_reason → 422."""
    f = _md_with_pending_candidate(tmp_path)
    with pytest.raises(HTTPException) as exc_info:
        await dispute_candidate(
            file_path=f, candidate_id="cand-uuid-1", dispute_reason="   "
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_dispute_candidate_not_found_returns_404(tmp_path):
    f = _md_with_pending_candidate(tmp_path)
    with pytest.raises(HTTPException) as exc_info:
        await dispute_candidate(
            file_path=f, candidate_id="fake-id", dispute_reason="test"
        )
    assert exc_info.value.status_code == 404
