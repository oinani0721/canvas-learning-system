"""Multi-vault P0-1 (2026-05-10) — /api/v1/chat/enrich-context vault_id 串库防御测试。

5 vault 共存场景的核心保护：plugin 传 vault_id → backend sanitize → build_vault_group_id →
set_current_subject_id 注入 ContextVar。让 downstream wikilink/lancedb/supplementary
都通过 get_current_subject_id() 读到同一 vault_id，并发请求不互相串库。

测试覆盖：
- vault_id 缺失 → 422 (Pydantic 必填校验)
- vault_id 空字符串 → 422 (min_length=1)
- vault_id 提供 → sanitize + build_vault_group_id + set_current_subject_id 全链路调用
- 中文 vault_id 不被坍缩 'default'（Phase B0.1 sanitize 已修，本测试保护回归）
- 两个 vault 并发请求 → ContextVar 各自独立（asyncio.gather 同时跑不串库）
- subject_id 可选（向后兼容）
"""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.services.wikilink_context_service import EnrichmentResult


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _payload(
    vault_id: str | None = "test_vault",
    subject_id: str | None = None,
) -> dict[str, Any]:
    p: dict[str, Any] = {
        "node_path": "节点/Eigenvalues.md",
        "current_note_content": "特征值是核心概念。",
        "current_note_frontmatter": {"type": "concept"},
        "max_hops": 2,
    }
    if vault_id is not None:
        p["vault_id"] = vault_id
    if subject_id is not None:
        p["subject_id"] = subject_id
    return p


# ─────────────────────────────────────────────────────────────
# Pydantic 必填校验
# ─────────────────────────────────────────────────────────────


def test_vault_id_missing_rejected_422(client):
    """vault_id 字段缺失 → Pydantic 必填校验 422。

    防御目标：plugin 旧版本（未更新）不能 silently fallback 到 settings.vault_id
    而把数据写到错 vault → 显式 422 让用户知道要重新 build plugin。
    """
    resp = client.post(
        "/api/v1/chat/enrich-context",
        json=_payload(vault_id=None),
    )
    assert resp.status_code == 422
    assert "vault_id" in resp.text


def test_vault_id_empty_string_rejected_422(client):
    """vault_id='' 也应被 min_length=1 拒绝（防 plugin 传空字符串绕过 None 检查）。"""
    resp = client.post(
        "/api/v1/chat/enrich-context",
        json=_payload(vault_id=""),
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# Sanitize + ContextVar 注入全链路
# ─────────────────────────────────────────────────────────────


def test_vault_id_provided_triggers_context_var_injection(client):
    """vault_id 提供 → handler 调 sanitize_vault_id + build_vault_group_id +
    set_current_subject_id 全链路。

    防御目标：5 vault 并发时 downstream 必须通过 ContextVar 拿到当前 request 的
    vault_id，否则就是 process-level 全局变量串库。
    """
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch("app.core.subject_config.set_current_subject_id") as mock_set_subj,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(vault_id="CS 61B"),
        )

    assert resp.status_code == 200
    mock_set_subj.assert_called_once()
    # build_vault_group_id 应该传入 sanitized "cs_61b"
    injected_group_id = mock_set_subj.call_args.args[0]
    assert "cs_61b" in injected_group_id, (
        f"set_current_subject_id 应注入 sanitize 后含 'cs_61b' 的 group_id，"
        f"实际 {injected_group_id}"
    )


def test_chinese_vault_id_not_collapsed_to_default(client):
    """中文 vault_id 必须保留 — Phase B0.1 sanitize 已修，回归保护。

    旧版 sanitize_vault_id 把任何非 ASCII 字符全部 strip → '数学101' → 'default'
    → 两个中文 vault 共用 default 表 → 数据物理混库。
    """
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch("app.core.subject_config.set_current_subject_id") as mock_set_subj,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(vault_id="数学101"),
        )

    assert resp.status_code == 200
    injected_group_id = mock_set_subj.call_args.args[0]
    assert "数学101" in injected_group_id, (
        f"中文 vault_id 必须保留，不能坍缩 default。实际 {injected_group_id}"
    )
    assert injected_group_id != "default", (
        "中文 vault_id 坍缩 default → 多中文 vault 数据泄漏 P0"
    )


def test_subject_id_optional_backward_compat(client):
    """subject_id 不传 → build_vault_group_id 用默认 fallback，不报错。

    一 vault 一学科场景（如 cs_61b vault）subject_id 是冗余的。
    """
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(vault_id="cs_61b"),  # 不传 subject_id
        )
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# 并发隔离 — 最致命场景
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_concurrent_two_vaults_dont_share_context_var():
    """两个 vault 并发请求 → ContextVar 各自独立，不互相串库。

    这是多 vault P0-1 的核心防御场景：
    - 用户 A 在 vault='cs_61b' 请求中
    - 用户 B（或后台 task）在 vault='数学' 同时请求
    - asyncio ContextVar 设计上保证两个协程有各自独立的值
    - 如果 backend 用 process-level 全局变量（旧 ACTIVE_VAULT 模式），
      会发生 A 看到 B 的 vault_id → 跨 vault 数据泄漏
    """
    from app.core.subject_config import get_current_subject_id, set_current_subject_id

    captured: dict[str, str] = {}

    async def request_a():
        set_current_subject_id("vault:cs_61b:_:eigenvalues")
        await asyncio.sleep(0.01)  # 让出 event loop，模拟 IO 等待
        captured["a_after_yield"] = get_current_subject_id()

    async def request_b():
        set_current_subject_id("vault:数学:_:integral")
        await asyncio.sleep(0.01)
        captured["b_after_yield"] = get_current_subject_id()

    # 并发跑：如果 ContextVar 真隔离，两个 task 各自看到自己写的值
    await asyncio.gather(request_a(), request_b())

    assert captured["a_after_yield"] == "vault:cs_61b:_:eigenvalues", (
        f"request A 应看到自己的 vault，实际 {captured['a_after_yield']}"
    )
    assert captured["b_after_yield"] == "vault:数学:_:integral", (
        f"request B 应看到自己的 vault，实际 {captured['b_after_yield']}"
    )
    assert captured["a_after_yield"] != captured["b_after_yield"], (
        "两个 vault 并发请求 ContextVar 串库 — P0 数据泄漏"
    )


# ─────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────


def test_vault_id_with_special_chars_sanitized(client):
    """vault_id 含 ../ path traversal 字符必须被 sanitize 净化。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch("app.core.subject_config.set_current_subject_id") as mock_set_subj,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(vault_id="../etc/passwd"),
        )

    assert resp.status_code == 200
    injected_group_id = mock_set_subj.call_args.args[0]
    # sanitize_vault_id 把 ../ 转成 _，不能让原始路径分隔符进 group_id
    assert "../" not in injected_group_id
    assert "/etc/" not in injected_group_id


def test_vault_id_emoji_stripped(client):
    """emoji 不出现在 vault_id 中（sanitize_vault_id 行为）。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch("app.core.subject_config.set_current_subject_id") as mock_set_subj,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(vault_id="📚 笔记本"),
        )

    assert resp.status_code == 200
    injected_group_id = mock_set_subj.call_args.args[0]
    assert "📚" not in injected_group_id
    assert "笔记本" in injected_group_id
