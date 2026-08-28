# CARD-G2-2 (BATCH-2026-08-28-第五批) — 唯一 VaultScope resolver + 409 fail-closed.
"""vault_scope 统一解析契约 + 跨 endpoint 的不一致→409 裁判用例.

覆盖两层:

1. ``app.core.vault_scope`` 单元契约 — 409 语义 (boards.py:70-76 先例)、
   双缺失推导 active vault (memory.py 批次1'① 姿势)、legacy 路径不 409
   (本卡显式裁定)、hook-cwd 合法例外、current_group_id()/current_vault_id()
   统一读取口。
2. 端点面 409 行为 — sync/mastery/memory/exam_sessions/boards 五个此前
   各自克隆 resolver 的文件, 显式 vault_id 与进程 active vault 不一致时
   必须 409 (而非静默为他 vault 构组写读)。

Patch-target 注记: vault_scope 全部延迟 import — 必须 patch
``app.config.get_current_vault_id`` 源命名空间 (C6 同款坑)。
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    _current_subject_id,
    get_current_subject_id,
    set_current_subject_id,
)
from app.core.vault_scope import (
    current_group_id,
    current_vault_id,
    resolve_hook_cwd_scope,
    resolve_vault_scope,
)

ACTIVE = "active_vault"
OTHER = "other_vault"


class _ContextVarHygiene:
    """Token-based ContextVar restore (C6 同款): teardown 恢复外层值."""

    def setup_method(self):
        self._cv_token = _current_subject_id.set(DEFAULT_SUBJECT_ID)

    def teardown_method(self):
        _current_subject_id.reset(self._cv_token)


# ═══════════════════════════════════════════════════════════════════════════
# 1. resolve_vault_scope 单元契约
# ═══════════════════════════════════════════════════════════════════════════


class TestResolveVaultScope(_ContextVarHygiene):
    def test_explicit_mismatch_raises_409(self):
        """显式 request vault ≠ active vault → 409 (fail-closed 核心语义)."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            with pytest.raises(HTTPException) as exc_info:
                resolve_vault_scope(OTHER)
        assert exc_info.value.status_code == 409
        # 诊断信息必须同时点名两侧 vault (可感知 split-brain)
        assert OTHER in exc_info.value.detail
        assert ACTIVE in exc_info.value.detail

    def test_mismatch_does_not_rewrite_contextvar(self):
        """409 拒绝时禁止静默改写作用域 — ContextVar 保持原值."""
        set_current_subject_id("vault:pre_existing")
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            with pytest.raises(HTTPException):
                resolve_vault_scope(OTHER)
        assert get_current_subject_id() == "vault:pre_existing"

    def test_explicit_match_derives_and_injects(self):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope(ACTIVE, subject_id="algorithms")
        assert scope.group_id == f"vault:{ACTIVE}:algorithms"
        assert scope.vault_id == ACTIVE
        assert scope.source == "request-vault"
        assert get_current_subject_id() == scope.group_id

    def test_mismatch_compare_is_after_sanitize(self):
        """比较在 sanitize 之后 — display name 'Active Vault' == active_vault."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope("Active Vault")
        assert scope.group_id == f"vault:{ACTIVE}"

    def test_legacy_group_id_path_does_not_409(self):
        """本卡显式裁定: deprecated legacy group 路径不做 409 (归一化+warning),
        deprecated 面收敛归 G2-4/G4 消费链."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope(None, legacy_group_id="cs188")
        # canonical_group_id 把 cs188 映射到 vault:default — 与 active 不同也不 409
        assert scope.group_id == "vault:default"
        assert scope.source == "legacy-group"

    def test_double_missing_derives_active_vault(self):
        """双缺失 → 推导 active vault 组, 绝不落 DEFAULT_GROUP_ID 污染桶."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope(None, legacy_group_id=None)
        assert scope.group_id == f"vault:{ACTIVE}"
        assert scope.source == "active-vault"
        assert get_current_subject_id() == f"vault:{ACTIVE}"

    def test_double_missing_keeps_secondary_levels(self):
        """双缺失时二级 (subject_id/canvas_path) 仍透传 (metadata.py G-DEFAULT 超集)."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope(None, canvas_path="dijkstra")
        assert scope.group_id == f"vault:{ACTIVE}:dijkstra"

    def test_whitespace_vault_id_treated_as_missing(self):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_vault_scope("   ")
        assert scope.source == "active-vault"


class TestHookCwdScope(_ContextVarHygiene):
    def test_cwd_vault_differing_from_active_is_legal(self):
        """契约 5: hook cwd 推导出他 vault 是设计内合法, 不 409."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_hook_cwd_scope(OTHER)
        assert scope.group_id == f"vault:{OTHER}"
        assert scope.source == "hook-cwd"
        assert get_current_subject_id() == f"vault:{OTHER}"

    def test_cwd_none_falls_back_to_active(self):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            scope = resolve_hook_cwd_scope(None)
        assert scope.group_id == f"vault:{ACTIVE}"
        assert scope.source == "active-vault"


class TestUnifiedReadGates(_ContextVarHygiene):
    def test_current_group_id_prefers_injected_scope(self):
        set_current_subject_id("vault:ctx_vault:dijkstra")
        assert current_group_id() == "vault:ctx_vault:dijkstra"

    def test_current_group_id_canonicalizes_bare_value(self):
        set_current_subject_id("CS 61B")
        assert current_group_id() == "vault:cs_61b"

    def test_current_group_id_unset_derives_active_vault(self):
        """ContextVar 未注入 → 推导 active vault (DEFAULT_GROUP_ID 兜底退役)."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            assert current_group_id() == f"vault:{ACTIVE}"

    def test_current_vault_id_extracts_segment(self):
        set_current_subject_id("vault:ctx_vault:algorithms")
        assert current_vault_id() == "ctx_vault"

    def test_current_vault_id_unset_falls_back_to_active(self):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            assert current_vault_id() == ACTIVE


# ═══════════════════════════════════════════════════════════════════════════
# 2. 端点面 409 行为 (sync/mastery/memory/exam_sessions/boards)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def client():
    from app.main import app
    from app.security import require_internal_api_key

    app.dependency_overrides[require_internal_api_key] = lambda: None
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.pop(require_internal_api_key, None)


@pytest.fixture
def isolated_event_log(tmp_path, monkeypatch):
    """把 learning_events.jsonl 重定向到 tmp。

    ``learning_event_log._log_path()`` 取 ``settings.CANVAS_BASE_PATH``,
    在本机指向 **live vault** —— 任何写事件的测试若不隔离, 都会往真实
    学习事件账本追加脏行 (公共纪律: 不碰 live vault)。
    """
    from app.services import learning_event_log

    log_file = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(learning_event_log, "_log_path", lambda: log_file)
    log_file.write_text("", encoding="utf-8")
    return log_file


SYNC_PAYLOAD = {
    "canvas_id": "test_canvas",
    "vault_id": OTHER,
    "subject_id": "test_subject",
    "operations": [
        {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "entity_type": "board",
            "entity_id": "test_canvas",
            "operation": "create",
            "payload": {"name": "Test Board"},
            "timestamp": "2026-04-06T00:00:00Z",
        }
    ],
}


class TestEndpointConflict409:
    """五个此前各自克隆 resolver 的端点文件, 统一 409 语义落地验证."""

    def test_sync_batch_mismatch_409(self, client):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/sync/batch", json=SYNC_PAYLOAD)
        assert resp.status_code == 409, resp.text

    def test_mastery_batch_mismatch_409(self, client):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.get("/api/v1/mastery/batch", params={"vault_id": OTHER})
        assert resp.status_code == 409, resp.text

    def test_memory_episodes_mismatch_409(self, client):
        payload = {
            "user_id": "u1",
            "canvas_path": "test.canvas",
            "node_id": "n1",
            "concept": "c1",
            "agent_type": "test",
            "vault_id": OTHER,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/memory/episodes", json=payload)
        assert resp.status_code == 409, resp.text

    def test_exam_sessions_mismatch_409(self, client):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.get("/api/v1/exam_sessions", params={"vault_id": OTHER})
        assert resp.status_code == 409, resp.text

    def test_boards_manifest_mismatch_409(self, client):
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post(
                "/api/v1/boards/manifest",
                json={"vault_id": OTHER, "board_id": "任意板"},
            )
        assert resp.status_code == 409, resp.text

    def test_409_detail_names_both_vaults(self, client):
        """409 响应对用户可感: 同时点名请求 vault 与当前挂载 vault."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.get("/api/v1/exam_sessions", params={"vault_id": OTHER})
        assert resp.status_code == 409
        assert OTHER in resp.text
        assert ACTIVE in resp.text


class TestCodexRound1RectifiedEndpoints:
    """Codex round-1 点名的失守面 — 整改后逐个锁 409 (MEDIUM-14 覆盖缺口).

    每条对应一个 BLOCKER/HIGH: 这些端点此前或自建 resolver 绕过 409,
    或把 409 吞成 200/500, 或在解析前就写了状态。
    """

    def test_chat_enrich_context_mismatch_409(self, client):
        """BLOCKER-1: /enrich-context 曾是第 9 份克隆, 可读异 vault 记忆."""
        payload = {
            "node_path": "x.md",
            "current_note_content": "c",
            "current_note_frontmatter": {},
            "vault_id": OTHER,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/chat/enrich-context", json=payload)
        assert resp.status_code == 409, resp.text

    def test_chat_enrich_context_match_path_executes(self, client):
        """一致 vault 的成功路径必须真的能跑完 —— 收敛 resolver 时若把
        下游仍在用的 `sanitized_vault_id` 变量删掉, 只测 409 分支的用例
        看不出来 (409 在它之前就 raise 了), 生产上是 NameError 500。"""
        payload = {
            "node_path": "x.md",
            "current_note_content": "c",
            "current_note_frontmatter": {},
            "vault_id": ACTIVE,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/chat/enrich-context", json=payload)
        # 200 或业务性 4xx/5xx 均可, 但绝不能是 NameError 引发的崩溃
        assert "sanitized_vault_id" not in resp.text
        assert "NameError" not in resp.text

    def test_chat_post_turn_extract_mismatch_409(self, client):
        """BLOCKER-1: /post-turn-extract 曾可向异 vault 写错误记录."""
        payload = {
            "node_id": "n1",
            "session_id": "s1",
            "messages": [{"role": "user", "content": "hi", "turn_index": 0}],
            "vault_id": OTHER,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/chat/post-turn-extract", json=payload)
        assert resp.status_code == 409, resp.text

    def test_tips_get_mismatch_409_not_empty_200(self, client):
        """BLOCKER-2: GET 曾把 409 吞成 200 + 空列表 (伪装成「没有批注」)."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.get(
                "/api/v1/tips", params={"node_id": "n1", "vault_id": OTHER}
            )
        assert resp.status_code == 409, resp.text

    def test_tips_save_mismatch_409_not_500(self, client):
        """BLOCKER-2: save 曾把 409 改写成 500 (插件无从据此纠正)."""
        payload = {
            "vault_id": OTHER,
            "content": "c",
            "title": "t",
            "node_id": "n1",
            "source_timestamp": "2026-01-01T00:00:00Z",
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/tips", json=payload)
        assert resp.status_code == 409, resp.text

    def test_tips_callout_direct_409_before_idempotency_write(
        self, client, isolated_event_log
    ):
        """BLOCKER-2: callout-direct 曾先落幂等事件再 409 —— 客户端纠正
        vault 后重试会被判 duplicate, 批注永久丢失。现在解析先行。

        事件账本经 ``isolated_event_log`` 重定向到 tmp (append_event 的
        `_log_path()` 读 CANVAS_BASE_PATH, 默认指向 **live vault**;
        本用例必须落盘验证幂等语义, 不隔离就会污染真实学习事件账本)。
        """
        payload = {
            "vault_id": OTHER,
            "callout_id": "c-409-guard",
            "node_id": "n1",
            "callout_type": "question",
            "text": "why?",
            "added_at": "2026-01-01T00:00:00Z",
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/tips/callout-direct", json=payload)
        assert resp.status_code == 409, resp.text

        # 409 时**不得**留下幂等键 (留了就等于把重试机会烧掉)
        assert "c-409-guard" not in isolated_event_log.read_text(encoding="utf-8")

        # 纠正 vault 后同一 callout_id 必须仍可被受理 (未被幂等键拦死)
        payload_fixed = {**payload, "vault_id": ACTIVE}
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp2 = client.post("/api/v1/tips/callout-direct", json=payload_fixed)
        assert resp2.status_code == 200, resp2.text
        assert "duplicate" not in resp2.text

    def test_tips_batch_mismatch_409_not_item_failure(self, client):
        """BLOCKER-2: batch 曾把 409 记成 item failure 并整体返回 200."""
        payload = {
            "vault_id": OTHER,
            "node_id": "n1",
            "source_timestamp": "2026-01-01T00:00:00Z",
            "callouts": [
                {
                    "annotation_id": "a1",
                    "tag": "important",
                    "tag_label": "重要",
                    "content": "c",
                    "content_hash": "deadbeef" * 8,
                }
            ],
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/tips/batch", json=payload)
        assert resp.status_code == 409, resp.text

    def test_memory_archive_session_409_not_200_error(self, client):
        """BLOCKER-3: SessionEnd hook 把任意 2xx 当成功 —— 409 若被吞成
        200 status=error 会删除重试机会并丢整段会话存档."""
        payload = {
            "session_id": "s1",
            "vault_id": OTHER,
            "messages": [{"role": "user", "content": "a"}] * 6,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/memory/archive/session", json=payload)
        assert resp.status_code == 409, resp.text

    def test_memory_archive_session_409_before_trivial_early_return(self, client):
        """BLOCKER-3: 解析必须先于「消息过少」早返 (否则零解析放行)."""
        payload = {
            "session_id": "s1",
            "vault_id": OTHER,
            "messages": [{"role": "user", "content": "a"}],  # < 4 条
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/memory/archive/session", json=payload)
        assert resp.status_code == 409, resp.text

    def test_memory_archive_deprecated_group_cannot_override_vault(self, client):
        """BLOCKER-3: 原 `request.group_id or resolver(...)` 让 deprecated
        group 覆盖必填 vault_id 并整个绕过 409."""
        payload = {
            "session_id": "s1",
            "vault_id": OTHER,
            "group_id": "vault:whatever",
            "messages": [{"role": "user", "content": "a"}] * 6,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/memory/archive/session", json=payload)
        assert resp.status_code == 409, resp.text

    def test_memory_episodes_batch_mismatch_409(self, client):
        """BLOCKER-4: /episodes/batch 曾零解析 (跨存储 split-brain)."""
        payload = {
            "vault_id": OTHER,
            "events": [
                {
                    "event_type": "color_changed",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "canvas_path": "x.canvas",
                    "node_id": "n1",
                }
            ],
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/memory/episodes/batch", json=payload)
        assert resp.status_code == 409, resp.text

    def test_metadata_batch_index_mismatch_409(self, client):
        """HIGH-11 伴随: batch 索引入口解析一次且 409 生效."""
        payload = {"canvas_paths": ["a.canvas"], "vault_id": OTHER}
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/canvas-meta/index/batch", json=payload)
        assert resp.status_code == 409, resp.text

    def test_inheritance_distill_mismatch_409(self, client):
        """HIGH-8: distill 曾把 raw group_id 直通持久化链."""
        payload = {
            "messages": [{"role": "user", "content": "hi"}],
            "vault_id": OTHER,
        }
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post("/api/v1/chat/n1/distill", json=payload)
        assert resp.status_code == 409, resp.text

    def test_errors_rebuild_graphiti_mismatch_409(self, client):
        """HIGH-8: rebuild-graphiti 读 active vault 文件却可写任意 group."""
        with patch("app.config.get_current_vault_id", return_value=ACTIVE):
            resp = client.post(
                "/api/v1/errors/rebuild-graphiti",
                params={"vault_id": OTHER, "dry_run": True},
            )
        assert resp.status_code == 409, resp.text


class TestVaultAliasTolerance:
    """HIGH-10: 稳定 ID ≠ 目录名的合法配置不得被误 409."""

    def test_directory_name_alias_accepted(self):
        """插件传目录名 (canvas-vault), 后端稳定 ID 是 yaml 里的
        stable_id —— 必须放行且归一到稳定 ID, 不 409。"""
        from unittest.mock import MagicMock

        fake_settings = MagicMock()
        fake_settings.ACTIVE_VAULT = "canvas-vault"
        fake_settings.CANVAS_BASE_PATH = "/vaults/canvas-vault"

        with (
            patch("app.config.get_current_vault_id", return_value="stable_id"),
            patch("app.config.get_settings", return_value=fake_settings),
        ):
            scope = resolve_vault_scope("canvas-vault")
        # 放行, 且 group 归一到稳定 ID (不因入口不同分裂成两个桶)
        assert scope.group_id == "vault:stable_id"

    def test_genuinely_foreign_vault_still_409(self):
        """别名容忍不得削弱 fail-closed: 真正的他 vault 仍 409."""
        from unittest.mock import MagicMock

        fake_settings = MagicMock()
        fake_settings.ACTIVE_VAULT = "canvas-vault"
        fake_settings.CANVAS_BASE_PATH = "/vaults/canvas-vault"

        with (
            patch("app.config.get_current_vault_id", return_value="stable_id"),
            patch("app.config.get_settings", return_value=fake_settings),
        ):
            with pytest.raises(HTTPException) as exc_info:
                resolve_vault_scope("完全另一个vault")
        assert exc_info.value.status_code == 409

    def test_hook_cwd_alias_normalizes_to_stable_id(self):
        """HIGH-10 后半: hook 从 cwd 拿到目录名, 必须归一到稳定 ID,
        否则 hook 路径与 API 路径写进两个 group 互相查不到。"""
        from unittest.mock import MagicMock

        fake_settings = MagicMock()
        fake_settings.ACTIVE_VAULT = "canvas-vault"
        fake_settings.CANVAS_BASE_PATH = "/vaults/canvas-vault"

        with (
            patch("app.config.get_current_vault_id", return_value="stable_id"),
            patch("app.config.get_settings", return_value=fake_settings),
        ):
            scope = resolve_hook_cwd_scope("canvas_vault")
        assert scope.group_id == "vault:stable_id"
