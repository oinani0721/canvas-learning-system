"""Story 2.5.Y Task 2 — PostTurnExtractRequest vault_id 必填校验.

覆盖 AC #1:
- vault_id 缺失 → Pydantic ValidationError (FastAPI 转 422)
- vault_id 空字符串 → 422
- subject_id / canvas_path 可选 (None 默认)
- 完整字段构造成功

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.endpoints.chat import (
    PostTurnExtractRequest,
    PostTurnMessage,
)


def _make_messages():
    return [PostTurnMessage(role="user", content="test", turn_index=0)]


def test_post_turn_request_vault_id_required():
    """AC #1: vault_id 必填 → 缺失抛 ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PostTurnExtractRequest(
            node_id="节点/x.md",
            session_id="s-1",
            messages=_make_messages(),
        )
    errors = exc_info.value.errors()
    assert any("vault_id" in str(e.get("loc", ())) for e in errors)


def test_post_turn_request_vault_id_empty_string_rejected():
    """空字符串 vault_id → ValidationError (min_length=1)."""
    with pytest.raises(ValidationError):
        PostTurnExtractRequest(
            node_id="节点/x.md",
            session_id="s-1",
            messages=_make_messages(),
            vault_id="",
        )


def test_post_turn_request_with_vault_id_only():
    """仅 vault_id (无 subject_id / canvas_path) → 通过."""
    req = PostTurnExtractRequest(
        node_id="节点/x.md",
        session_id="s-1",
        messages=_make_messages(),
        vault_id="cs_61b",
    )
    assert req.vault_id == "cs_61b"
    assert req.subject_id is None
    assert req.canvas_path is None


def test_post_turn_request_full_fields():
    """vault_id + subject_id + canvas_path 全填."""
    req = PostTurnExtractRequest(
        node_id="节点/x.md",
        session_id="s-1",
        messages=_make_messages(),
        vault_id="cs_61b",
        subject_id="algorithms",
        canvas_path="节点/admissibility.md",
    )
    assert req.vault_id == "cs_61b"
    assert req.subject_id == "algorithms"
    assert req.canvas_path == "节点/admissibility.md"


def test_post_turn_request_chinese_vault_id():
    """中文 vault_id 通过."""
    req = PostTurnExtractRequest(
        node_id="节点/x.md",
        session_id="s-1",
        messages=_make_messages(),
        vault_id="数学",
    )
    assert req.vault_id == "数学"


def test_post_turn_request_subject_id_optional_canvas_path_optional():
    """subject_id / canvas_path 可选, 默认 None."""
    req = PostTurnExtractRequest(
        node_id="节点/x.md",
        session_id="s-1",
        messages=_make_messages(),
        vault_id="cs_61b",
        # 不传 subject_id / canvas_path
    )
    assert req.subject_id is None
    assert req.canvas_path is None


def test_post_turn_request_existing_validators_still_work():
    """v1.0 校验 (messages min/max + total chars) 仍生效."""
    # 空 messages → 422
    with pytest.raises(ValidationError):
        PostTurnExtractRequest(
            node_id="节点/x.md",
            session_id="s-1",
            messages=[],
            vault_id="cs_61b",
        )

    # 总字符超 48000 → 422 (existing v1.0 validator)
    long_msg = PostTurnMessage(
        role="user", content="a" * 8000, turn_index=0
    )
    with pytest.raises(ValidationError):
        PostTurnExtractRequest(
            node_id="节点/x.md",
            session_id="s-1",
            messages=[long_msg] * 7,  # 7 × 8000 = 56000 > 48000
            vault_id="cs_61b",
        )
