"""轨道 B (2026-07-20) — 方案 A 双写回显: candidate_callout 单元测试。

覆盖: description 拆分 / 三态渲染 (含 3 条硬要求) / 锚点 upsert 幂等与容错。
"""

from __future__ import annotations

from app.services.candidate_callout import (
    candidate_correction,
    candidate_misconception,
    render_candidate_callout,
    split_description,
    upsert_candidate_callout,
)

_CAND = {
    "id": "cand-fund-001",
    "description": "认为 det(A) > 0 即可推出矩阵正定 — 反例 diag(-1,-1) 行列式为 1 但负定",
    "confidence": 0.88,
    "pedagogy_type": "conceptual_confusion",
    "raw_dialog_excerpt": "",
    "provenance": "seeded",
}


# ── split_description ──


def test_split_em_dash():
    mis, cor = split_description("认为 X — 实际上 Y")
    assert mis == "认为 X"
    assert cor == "实际上 Y"


def test_split_no_marker_returns_full_as_misconception():
    mis, cor = split_description("单句误解无更正")
    assert mis == "单句误解无更正"
    assert cor == ""


def test_split_empty():
    assert split_description("") == ("", "")


def test_field_fallback_chain():
    # 显式字段优先, 缺失回退 description 拆分
    assert (
        candidate_misconception({"misconception": "显式", "description": "a — b"})
        == "显式"
    )
    assert candidate_misconception({"description": "a — b"}) == "a"
    assert candidate_correction({"description": "a — b"}) == "b"


# ── render 三态 + 硬要求 ──


def test_render_pending_hard_requirements():
    out = render_candidate_callout(_CAND, "pending")
    # 硬要求①: 无逐字引语禁止"你说过"句式
    assert "你在会话中说" not in out
    assert "AI 从会话归纳（无逐字引语）" in out
    # 硬要求②: seeded 角标
    assert "测试种子" in out
    # 硬要求③: 卡片主体只展示误解半句, 更正入折叠块
    assert "**认为 det(A) > 0 即可推出矩阵正定**" in out
    assert "[!note]- 更正参考" in out
    # 锚点在场
    assert "%%cand:cand-fund-001%%" in out
    assert out.startswith("> [!error-candidate]+ 🔴 待复盘")


def test_render_pending_with_excerpt_uses_quote():
    cand = {
        **_CAND,
        "raw_dialog_excerpt": "只要 det > 0 就正定",
        "provenance": "distilled",
    }
    out = render_candidate_callout(cand, "pending")
    assert "你在会话中说「只要 det > 0 就正定」" in out
    assert "测试种子" not in out


def test_render_accepted():
    out = render_candidate_callout(_CAND, "accepted", today="2026-07-20")
    assert out.startswith("> [!success]+ ✅ 已确认误区（2026-07-20 复盘）")
    assert "已移入 errors[]" in out
    assert "%%cand:cand-fund-001%%" in out


def test_render_disputed_with_reason_and_strikethrough():
    out = render_candidate_callout(
        _CAND, "disputed", dispute_reason="AI 过度推断", today="2026-07-20"
    )
    assert "⚠️ 已异议（2026-07-20 复盘 · 理由：AI 过度推断）" in out
    assert "~~认为 det(A) > 0 即可推出矩阵正定~~" in out
    assert "不入 errors[]" in out


# ── upsert ──


def test_upsert_append_when_missing():
    body = "# 正文\n\n一些内容\n"
    card = render_candidate_callout(_CAND, "pending")
    new_body, changed = upsert_candidate_callout(
        body, "cand-fund-001", card, append_if_missing=True
    )
    assert changed
    assert card in new_body
    assert new_body.startswith("# 正文")


def test_upsert_replace_in_place_state_transition():
    body = "# 正文\n\n"
    pending = render_candidate_callout(_CAND, "pending")
    body1, _ = upsert_candidate_callout(
        body, "cand-fund-001", pending, append_if_missing=True
    )
    accepted = render_candidate_callout(_CAND, "accepted", today="2026-07-20")
    body2, changed = upsert_candidate_callout(
        body1, "cand-fund-001", accepted, append_if_missing=False
    )
    assert changed
    assert "🔴 待复盘" not in body2
    assert "✅ 已确认误区" in body2
    # 整块替换, 不残留旧行
    assert "AI 从会话归纳" not in body2


def test_upsert_skip_when_user_deleted_card():
    # 容错 (提案风险提示): 锚点缺失且不允许追加 → 原文返回
    body = "# 正文\n用户删掉了卡片\n"
    card = render_candidate_callout(_CAND, "accepted")
    new_body, changed = upsert_candidate_callout(
        body, "cand-fund-001", card, append_if_missing=False
    )
    assert not changed
    assert new_body == body


def test_upsert_does_not_touch_other_candidates():
    other = {**_CAND, "id": "cand-fund-002", "description": "另一条误解"}
    body = "# 正文\n\n"
    body, _ = upsert_candidate_callout(
        body,
        "cand-fund-001",
        render_candidate_callout(_CAND, "pending"),
        append_if_missing=True,
    )
    body, _ = upsert_candidate_callout(
        body,
        "cand-fund-002",
        render_candidate_callout(other, "pending"),
        append_if_missing=True,
    )
    body2, _ = upsert_candidate_callout(
        body,
        "cand-fund-001",
        render_candidate_callout(_CAND, "disputed", dispute_reason="不对"),
        append_if_missing=False,
    )
    assert "%%cand:cand-fund-002%%" in body2
    assert "**另一条误解**" in body2  # 002 卡片完好
    assert "~~认为 det(A) > 0 即可推出矩阵正定~~" in body2  # 001 已变态
