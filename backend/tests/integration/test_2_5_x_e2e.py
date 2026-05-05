"""Story 2.5.X Task 8 + Task 10 — E2E 集成测试.

覆盖完整流程:
1. write_error_dual (mode=candidate_only) → frontmatter error_candidates[]
2. accept_candidate → candidate.status=accepted + errors[] 写入 + Graphiti queued
3. dismiss_candidate → candidate.status=dismissed (不入 errors[])
4. dispute_candidate → candidate.status=disputed + dispute_reason
5. expire_pending_candidates → 老 candidate status=expired
6. rebuild_graphiti_from_frontmatter → 从 errors[] 重建

Task 8 验证: session_id 在 candidate.session_id + seen_sessions[] 透传
Task 10 验证: 跨 service E2E (writer + service + state_machine + rebuild + expiry)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from app.graphiti.entity_types import (
    ErrorType,
    PedagogyErrorType,
    RemedyStrategy,
)
from app.services.candidate_expiry_service import expire_pending_candidates
from app.services.candidate_service import (
    CandidateEdits,
    accept_candidate,
    dismiss_candidate,
    dispute_candidate,
)
from app.services.error_classifier import ClassifiedError
from app.services.error_rebuild_service import rebuild_graphiti_from_frontmatter
from app.services.error_writer import write_error_dual


def _make_classified_error(
    description: str = "学生混淆 admissibility 与 consistency",
) -> ClassifiedError:
    return ClassifiedError(
        legacy_type=ErrorType.KNOWLEDGE_GAP,
        pedagogy_type=PedagogyErrorType.CONCEPTUAL_CONFUSION,
        description=description,
        context="对话第 3 轮",
        confidence=0.85,
        legacy_remedy=RemedyStrategy.BACKTRACK_DEFINITION,
        pedagogy_remedies=[RemedyStrategy.DISCRIMINATION_COMPARISON],
        sub_tags=["synonym_confusion"],
    )


def _make_test_node(tmp_path):
    """创建测试 vault 节点 .md (基础 frontmatter)."""
    nodes = tmp_path / "节点"
    nodes.mkdir(exist_ok=True)
    f = nodes / "admissibility.md"
    fm = {"type": "concept", "board_name": "UAT"}
    fm_str = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    f.write_text(f"---\n{fm_str}---\n# admissibility\n", encoding="utf-8")
    return f


# ════════════════════════════════════════════════════════════════════
# E2E #1 — 完整 accept 流程 (write candidate → accept → errors[])
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_full_accept_flow(tmp_path):
    """write candidate → user accepts → errors[] 写入 + Graphiti queued."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()
    session_id = "s-2026-05-05-001"

    # Step 1: write candidate (candidate_only mode 默认)
    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id=session_id
    )
    assert result1["mode"] == "candidate_only"
    assert result1["frontmatter"] is True
    assert result1["graphiti"] == "skipped_candidate_mode"
    candidate_id = result1["candidate_id"]
    assert candidate_id is not None

    # 验证 frontmatter
    fm = yaml.safe_load(f.read_text().split("---")[1])
    assert "error_candidates" in fm
    assert len(fm["error_candidates"]) == 1
    cand = fm["error_candidates"][0]
    assert cand["status"] == "pending"
    assert cand["session_id"] == session_id  # Task 8: session_id 透传
    assert cand["seen_sessions"] == [session_id]

    # Step 2: user accepts the candidate
    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        result2 = await accept_candidate(
            f, candidate_id=candidate_id, session_id=session_id
        )

    assert result2.status == "accepted"
    assert result2.error_id == candidate_id  # 复用 id
    assert result2.frontmatter_written is True
    assert result2.graphiti_status == "queued"

    # 验证 frontmatter (errors[] + candidate.status)
    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "accepted"
    assert cand["status_changed_by"] == "user"

    err = fm["errors"][0]
    assert err["id"] == candidate_id
    assert err["source"] == "user_confirmed_ai"
    assert err["user_confirmed"] is True
    assert err["from_candidate_id"] == candidate_id


# ════════════════════════════════════════════════════════════════════
# E2E #2 — accept with edits → status=edited + edits 应用
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_accept_with_edits(tmp_path):
    """write candidate → user edits + accepts → status=edited + edits 应用到 errors[]."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    candidate_id = result1["candidate_id"]

    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        result2 = await accept_candidate(
            f,
            candidate_id=candidate_id,
            user_edits=CandidateEdits(
                description="(用户编辑) admissibility 比 consistency 更弱",
                pedagogy_type="metacognitive_error",
            ),
        )

    assert result2.status == "edited"

    fm = yaml.safe_load(f.read_text().split("---")[1])
    err = fm["errors"][0]
    assert err["description"] == "(用户编辑) admissibility 比 consistency 更弱"
    assert err["type"] == "metacognitive_error"


# ════════════════════════════════════════════════════════════════════
# E2E #3 — dismiss path (不入 errors[])
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_dismiss_path_no_errors_written(tmp_path):
    """write candidate → user dismisses → 不入 errors[]."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    candidate_id = result1["candidate_id"]

    result2 = await dismiss_candidate(f, candidate_id=candidate_id)
    assert result2.status == "dismissed"

    fm = yaml.safe_load(f.read_text().split("---")[1])
    assert fm["error_candidates"][0]["status"] == "dismissed"
    # errors[] 不应被写入
    assert "errors" not in fm or fm.get("errors") in (None, [])


# ════════════════════════════════════════════════════════════════════
# E2E #4 — dispute path + dispute_reason 持久化
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_dispute_path_writes_reason(tmp_path):
    """write candidate → user disputes + 写理由 → status=disputed + dispute_reason 持久化."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    candidate_id = result1["candidate_id"]

    result2 = await dispute_candidate(
        f, candidate_id=candidate_id, dispute_reason="我不是说它们等价，只是问关系"
    )
    assert result2.status == "disputed"
    assert result2.dispute_reason == "我不是说它们等价，只是问关系"

    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "disputed"
    assert cand["dispute_reason"] == "我不是说它们等价，只是问关系"
    assert "errors" not in fm or fm.get("errors") in (None, [])


# ════════════════════════════════════════════════════════════════════
# E2E #5 — Task 8: session_id 跨 session dedupe + 累加
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_session_id_accumulates_across_sessions(tmp_path):
    """同一节点同一错误跨 3 个 session → 1 candidate + seen_sessions=[s1,s2,s3]."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    # session 1
    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    # session 2 (同错误)
    result2 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-2"
    )
    # session 3 (同错误)
    result3 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-3"
    )

    # 同一 candidate (dedupe hash 不含 session_id)
    assert result1["candidate_id"] == result2["candidate_id"] == result3["candidate_id"]

    fm = yaml.safe_load(f.read_text().split("---")[1])
    assert len(fm["error_candidates"]) == 1
    cand = fm["error_candidates"][0]
    assert cand["seen_count"] == 3
    assert set(cand["seen_sessions"]) == {"s-1", "s-2", "s-3"}


# ════════════════════════════════════════════════════════════════════
# E2E #6 — Task 9: expired 30 天归档
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_expired_old_pending_after_30_days(tmp_path):
    """老 pending 经 30 天后被 cron 自动 expire."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    # 写候选 (默认 created_at = 当前)
    await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )

    # 模拟 31 天后跑 cron (now 设为 future)
    fm = yaml.safe_load(f.read_text().split("---")[1])
    created_str = fm["error_candidates"][0]["created_at"]
    created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
    future = created_dt + datetime.timedelta(days=31) if False else None

    # 简化: 用 future_now = created + 31 days
    from datetime import timedelta as _timedelta

    future_now = created_dt + _timedelta(days=31)

    stats = await expire_pending_candidates(
        tmp_path, expiry_days=30, now=future_now
    )

    assert stats.total_expired == 1

    fm = yaml.safe_load(f.read_text().split("---")[1])
    cand = fm["error_candidates"][0]
    assert cand["status"] == "expired"
    assert cand["status_changed_by"] == "system"


# ════════════════════════════════════════════════════════════════════
# E2E #7 — Task 5: rebuild_graphiti 从 frontmatter
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_rebuild_graphiti_from_accepted_errors(tmp_path):
    """accept 后 errors[] 已存, rebuild 应能重新写入 Graphiti."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    # write candidate + accept
    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        await accept_candidate(f, candidate_id=result1["candidate_id"])

    # rebuild from frontmatter
    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=False
        )

    assert stats.total_files_scanned == 1
    assert stats.total_errors_scanned == 1
    assert stats.newly_written == 1
    assert stats.failed == 0
    mock_g.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_rebuild_graphiti_dry_run_no_writes(tmp_path):
    """rebuild dry_run=True 仅扫描计数."""
    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        await accept_candidate(f, candidate_id=result1["candidate_id"])

    with patch(
        "app.services.error_rebuild_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ) as mock_g:
        stats = await rebuild_graphiti_from_frontmatter(
            tmp_path, group_id="vault:cs_61b", dry_run=True
        )

    assert stats.total_errors_scanned == 1
    assert stats.newly_written == 0  # dry_run
    mock_g.assert_not_called()


# ════════════════════════════════════════════════════════════════════
# E2E #8 — 状态机阻止反向 + idempotency
# ════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_e2e_double_accept_rejected_idempotency(tmp_path):
    """已 accept 的 candidate 不可再 accept (反向不可逆 → 422)."""
    from fastapi import HTTPException

    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    candidate_id = result1["candidate_id"]

    with patch(
        "app.services.candidate_service.write_error_to_graphiti",
        new=AsyncMock(return_value=True),
    ):
        await accept_candidate(f, candidate_id=candidate_id)
        with pytest.raises(HTTPException) as exc_info:
            await accept_candidate(f, candidate_id=candidate_id)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_e2e_dismiss_then_accept_rejected(tmp_path):
    """已 dismissed → accept 被拒 (终态间不可逆)."""
    from fastapi import HTTPException

    f = _make_test_node(tmp_path)
    error = _make_classified_error()

    result1 = await write_error_dual(
        f, error, node_id="节点/admissibility.md", session_id="s-1"
    )
    candidate_id = result1["candidate_id"]

    await dismiss_candidate(f, candidate_id=candidate_id)
    with pytest.raises(HTTPException) as exc_info:
        await accept_candidate(f, candidate_id=candidate_id)
    assert exc_info.value.status_code == 422
