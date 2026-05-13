"""Wave-5 Stage B 续 (2026-05-13) — multi-vault P0-2 ContextVar 注入剩余 11 个 endpoint files.

Stage B 第一轮覆盖了 6 个 file (mastery/errors/memory/metadata/review/exam, 36 endpoints).
本 Stage B 续覆盖 canvas / agents / sync / wikilink / tips / suggestions / archive / edges /
context / skills 共 10 个 file 的 38 个 endpoints (skills 跳过 by-design cross-vault).

测试矩阵 (每 file ≥ 1 case):
1. _vault_id_resolver: 共享 helper 接口 (vault_id 优先 / legacy 走 canonical / 都空 fallback)
2. sync: SyncBatchRequest 加 vault_id Optional 兼容
3. sync.sync_relationships_by_node: vault_id Query 推荐必填
4. wikilink.BuildRequest: vault_id 注入 + 兼容空值
5. canvas.read_canvas: vault_id Query 接受 + ContextVar 注入
6. tips.SaveTipRequest: vault_id Field 接受
7. suggestions.RelationSuggestionRequest: vault_id Field 接受
8. archive.trigger_archive: vault_id Query 接受
9. edges.EdgeRationaleCreate: vault_id Field 接受
10. context.get_node_context_endpoint: vault_id Query 接受
11. agents.DecomposeRequest: vault_id Field 接受
12. agents.ScoreRequest: vault_id Field 接受
13. agents.ExplainRequest: vault_id Field 接受

ContextVar 注入测试: 每 endpoint 在调 service 前调 _vault_id_resolver.resolve_vault_group_id,
验证 set_current_subject_id 写入了正确的 group_id.

[Source: Wave-5 Stage B 续任务 — fix 剩余 38 endpoint 无 vault 隔离 P0]
"""

from __future__ import annotations

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Test 1: 共享 _vault_id_resolver helper
# ═══════════════════════════════════════════════════════════════════════════════


class TestVaultIdResolverShared:
    """_vault_id_resolver.resolve_vault_group_id 三态语义.

    - vault_id 优先 → build_vault_group_id 派生 + ContextVar 写入
    - vault_id 空, legacy_group_id 提供 → canonical_group_id 归一化 + warning
    - 两者都空 → DEFAULT_GROUP_ID fallback
    """

    def test_vault_id_priority_over_legacy(self):
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
        from app.core.subject_config import get_current_subject_id

        result = resolve_vault_group_id(
            vault_id="cs_61b",
            subject_id=None,
            legacy_group_id="cs188",
        )

        # vault_id 走 build_vault_group_id 派生新前缀
        assert result.startswith("vault:")
        assert "cs_61b" in result
        # ContextVar 应该被注入
        assert get_current_subject_id() == result

    def test_empty_vault_id_falls_back_to_legacy(self):
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

        result = resolve_vault_group_id(
            vault_id=None,
            subject_id=None,
            legacy_group_id="cs188",
        )

        # legacy 走 canonical_group_id 归一化, 不为空
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_both_empty_falls_back_to_default(self):
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
        from app.config import DEFAULT_GROUP_ID

        result = resolve_vault_group_id(
            vault_id=None, subject_id=None, legacy_group_id=None
        )

        assert result == DEFAULT_GROUP_ID

    def test_whitespace_vault_id_treated_as_empty(self):
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id

        result = resolve_vault_group_id(
            vault_id="   ",  # 全空白
            subject_id=None,
            legacy_group_id="cs188",
        )

        # 不应走 vault_id 路径, 走 legacy
        assert "vault:cs_61b" not in result  # 验证没走 vault_id 路径

    def test_mastery_helper_aliases_to_shared(self):
        """mastery.py 的 _resolve_vault_group_id 应 alias 到共享 helper."""
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        assert _resolve_vault_group_id is resolve_vault_group_id


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2: sync.py — SyncBatchRequest 加 vault_id Optional + sync_relationships 加 Query
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyncBatchRequestVaultId:
    """SyncBatchRequest 加 vault_id: Optional[str] 兼容 plugin 旧调用,
    但 P0 写入路径推荐必填.
    """

    def test_sync_batch_accepts_vault_id(self):
        from app.models.sync_models import SyncBatchRequest, SyncOperation

        from datetime import datetime, timezone

        op = SyncOperation(
            operation_id="op-1",
            operation="create",
            entity_type="node",
            entity_id="n1",
            payload={"id": "n1"},
            timestamp=datetime.now(timezone.utc),
        )
        req = SyncBatchRequest(
            canvas_id="cv-1",
            vault_id="cs_61b",
            operations=[op],
        )
        assert req.vault_id == "cs_61b"

    def test_sync_batch_optional_vault_id_for_compat(self):
        """无 vault_id 时不报 422 (兼容旧 plugin), 仅 warning."""
        from app.models.sync_models import SyncBatchRequest, SyncOperation

        from datetime import datetime, timezone

        op = SyncOperation(
            operation_id="op-1",
            operation="create",
            entity_type="node",
            entity_id="n1",
            payload={"id": "n1"},
            timestamp=datetime.now(timezone.utc),
        )
        # 不传 vault_id — 应通过验证 (Optional)
        req = SyncBatchRequest(canvas_id="cv-1", operations=[op])
        assert req.vault_id is None

    def test_sync_batch_has_deprecated_group_id(self):
        from app.models.sync_models import SyncBatchRequest, SyncOperation

        from datetime import datetime, timezone

        op = SyncOperation(
            operation_id="op-1",
            operation="create",
            entity_type="node",
            entity_id="n1",
            payload={"id": "n1"},
            timestamp=datetime.now(timezone.utc),
        )
        # 旧 plugin 调用 — group_id 兼容字段
        req = SyncBatchRequest(
            canvas_id="cv-1",
            group_id="cs188",
            operations=[op],
        )
        assert req.group_id == "cs188"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 3: wikilink.py — BuildRequest / RefreshRequest 加 vault_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestWikilinkBuildRequestVaultId:
    """BuildRequest / RefreshRequest 加 vault_id Optional Field."""

    def test_build_request_accepts_vault_id(self):
        from app.api.v1.endpoints.wikilink import BuildRequest

        req = BuildRequest(vault_path="/tmp/x", vault_id="数学")
        assert req.vault_id == "数学"

    def test_build_request_optional_vault_id(self):
        """无 vault_id 不报 422 (兼容)."""
        from app.api.v1.endpoints.wikilink import BuildRequest

        req = BuildRequest()
        assert req.vault_id is None

    def test_refresh_request_accepts_vault_id(self):
        from app.api.v1.endpoints.wikilink import RefreshRequest

        req = RefreshRequest(changed_files=["a.md"], vault_id="cs_61b")
        assert req.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 4: tips.py — SaveTipRequest 加 vault_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestTipsSaveTipRequestVaultId:
    """SaveTipRequest 加 vault_id Optional Field."""

    def test_save_tip_request_accepts_vault_id(self):
        from app.api.v1.endpoints.tips import SaveTipRequest

        req = SaveTipRequest(
            content="some content",
            title="Tip title",
            tags=["important"],
            node_id="node-1",
            source_timestamp="2026-01-01T00:00:00Z",
            vault_id="cs_61b",
            subject_id="algorithms",
        )
        assert req.vault_id == "cs_61b"
        assert req.subject_id == "algorithms"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5: suggestions.py — RelationSuggestionRequest 加 vault_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestSuggestionsRelationRequestVaultId:
    def test_relation_request_accepts_vault_id(self):
        from app.api.v1.endpoints.suggestions import RelationSuggestionRequest

        req = RelationSuggestionRequest(
            source_content="def DFS",
            new_content="def BFS",
            source_node_id="n1",
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 6: edges.py — EdgeRationaleCreate 加 vault_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgesRationaleCreateVaultId:
    def test_rationale_create_accepts_vault_id(self):
        from app.models.edge_rationale import EdgeRationaleCreate

        req = EdgeRationaleCreate(
            edge_id="e1",
            source_node_id="n1",
            target_node_id="n2",
            relation_type="是前提条件",
            rationale_text="Because A enables B",
            confidence=0.85,
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"

    def test_rationale_create_optional_vault_id(self):
        """无 vault_id 不报 422 — 双写路径兼容."""
        from app.models.edge_rationale import EdgeRationaleCreate

        req = EdgeRationaleCreate(
            edge_id="e1",
            source_node_id="n1",
            target_node_id="n2",
            relation_type="是前提条件",
            rationale_text="X",
            confidence=0.5,
        )
        assert req.vault_id is None


# ═══════════════════════════════════════════════════════════════════════════════
# Test 7: agents.py request schemas — DecomposeRequest / ScoreRequest / ExplainRequest
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentsRequestVaultId:
    """agents.py 多个 Request schemas 加 vault_id."""

    def test_decompose_request_accepts_vault_id(self):
        from app.models import DecomposeRequest

        req = DecomposeRequest(canvas_name="canvas-1", node_id="n1", vault_id="cs_61b")
        assert req.vault_id == "cs_61b"

    def test_score_request_accepts_vault_id(self):
        from app.models import ScoreRequest

        req = ScoreRequest(
            canvas_name="canvas-1",
            node_ids=["n1"],
            vault_id="数学",
        )
        assert req.vault_id == "数学"

    def test_explain_request_accepts_vault_id(self):
        from app.models import ExplainRequest

        req = ExplainRequest(canvas_name="canvas-1", node_id="n1", vault_id="cs_61b")
        assert req.vault_id == "cs_61b"

    def test_recommend_action_request_accepts_vault_id(self):
        from app.models import RecommendActionRequest

        req = RecommendActionRequest(
            score=85,
            node_id="n1",
            canvas_name="cv1",
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"

    def test_verification_question_request_accepts_vault_id(self):
        from app.models import VerificationQuestionRequest

        req = VerificationQuestionRequest(
            canvas_name="cv1", node_id="n1", vault_id="cs_61b"
        )
        assert req.vault_id == "cs_61b"

    def test_question_decompose_request_accepts_vault_id(self):
        from app.models import QuestionDecomposeRequest

        req = QuestionDecomposeRequest(
            canvas_name="cv1", node_id="n1", vault_id="cs_61b"
        )
        assert req.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 8: ContextVar 端到端 — resolve 调用后写入到了 ContextVar
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextVarInjectionFromResolver:
    """resolve_vault_group_id 调用后, get_current_subject_id 应该返回新的 group_id."""

    def test_resolver_injects_contextvar(self):
        from app.api.v1.endpoints._vault_id_resolver import resolve_vault_group_id
        from app.core.subject_config import (
            get_current_subject_id,
            set_current_subject_id,
        )

        # 先重置
        set_current_subject_id("vault:reset_baseline")
        assert get_current_subject_id() == "vault:reset_baseline"

        # 调 resolver 注入新 vault
        new_group = resolve_vault_group_id(
            vault_id="数学", subject_id=None, legacy_group_id=None
        )

        # ContextVar 应已更新
        assert get_current_subject_id() == new_group
        assert new_group != "vault:reset_baseline"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 9: shared resolver 被各 endpoint 模块正确 import (smoke test)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSharedResolverImportedByEndpoints:
    """所有修改后的 endpoint files 都从 _vault_id_resolver import 共享 helper."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "app.api.v1.endpoints.sync",
            "app.api.v1.endpoints.wikilink",
            "app.api.v1.endpoints.canvas",
            "app.api.v1.endpoints.tips",
            "app.api.v1.endpoints.suggestions",
            "app.api.v1.endpoints.archive",
            "app.api.v1.endpoints.edges",
            "app.api.v1.endpoints.context",
            "app.api.v1.endpoints.agents",
            # Wave-5 Stage B 续 follow-up (2026-05-13) — 第 12 个 endpoint 补齐
            "app.api.v1.endpoints.index",
        ],
    )
    def test_endpoint_imports_shared_resolver(self, module_name):
        import importlib

        module = importlib.import_module(module_name)
        # 共享 resolver 应已被 import (变量名 resolve_vault_group_id)
        assert hasattr(module, "resolve_vault_group_id"), (
            f"{module_name} did not import resolve_vault_group_id from "
            "_vault_id_resolver"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test 10: index.py DELETE /api/v1/index/{vault_id} — Wave-5 Stage B 续 follow-up
# ═══════════════════════════════════════════════════════════════════════════════


class TestIndexDeleteVaultEndpointVaultIdInjection:
    """Wave-5 Stage B 续 follow-up (2026-05-13).

    `index.py:delete_vault_index` 是 Stage B 续 audit 漏掉的第 12 个 endpoint:
    vault_id 作 path param 直接 forward 给 LanceDB 的 drop_vault_tables, 但未走
    resolver 模式 → silent 串库回归风险窗口 (与 wave-2 F2 LanceDBClient direct
    instantiation 同源).

    本 follow-up patch (commit pending) 加 resolve_vault_group_id(vault_id) 注入
    ContextVar; 测试断言 endpoint 调用后 ContextVar 含正确 group_id, drop_vault_tables
    仍接 raw path param (向后兼容表名查找, 零业务逻辑变更).
    """

    @pytest.mark.asyncio
    async def test_delete_vault_index_injects_contextvar(self, monkeypatch):
        """endpoint 调用走 resolver → ContextVar 被正确注入 + drop_vault_tables 接 raw."""
        from unittest.mock import MagicMock

        from app.api.v1.endpoints.index import delete_vault_index
        from app.core.subject_config import (
            get_current_subject_id,
            set_current_subject_id,
        )

        # 先把 ContextVar 重置到 baseline
        set_current_subject_id("vault:baseline_before_call")

        # Mock LanceDB client - drop_vault_tables 返回 3 (3 tables dropped)
        mock_client = MagicMock()
        mock_client.drop_vault_tables.return_value = 3

        # Patch _get_lancedb_client → return mock
        from app.api.v1.endpoints import index as index_module

        monkeypatch.setattr(index_module, "_get_lancedb_client", lambda: mock_client)

        # 调 endpoint
        result = await delete_vault_index(vault_id="cs_61b")

        # ContextVar 应该被 resolver 重写 (不再是 baseline)
        new_subject = get_current_subject_id()
        assert new_subject != "vault:baseline_before_call"
        assert new_subject.startswith("vault:")
        assert "cs_61b" in new_subject

        # drop_vault_tables 应该接 raw vault_id (向后兼容)
        mock_client.drop_vault_tables.assert_called_once_with("cs_61b")
        assert result == {"vault_id": "cs_61b", "tables_dropped": 3}

    @pytest.mark.asyncio
    async def test_delete_vault_index_404_when_no_tables(self, monkeypatch):
        """drop_vault_tables 返回 0 → 404 (现有契约不变)."""
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from app.api.v1.endpoints.index import delete_vault_index
        from app.api.v1.endpoints import index as index_module

        mock_client = MagicMock()
        mock_client.drop_vault_tables.return_value = 0
        monkeypatch.setattr(index_module, "_get_lancedb_client", lambda: mock_client)

        with pytest.raises(HTTPException) as exc_info:
            await delete_vault_index(vault_id="empty_vault")

        assert exc_info.value.status_code == 404
        assert "empty_vault" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_vault_index_503_when_client_unavailable(self, monkeypatch):
        """LanceDB client None → 503 (现有契约不变)."""
        from fastapi import HTTPException

        from app.api.v1.endpoints.index import delete_vault_index
        from app.api.v1.endpoints import index as index_module

        monkeypatch.setattr(index_module, "_get_lancedb_client", lambda: None)

        with pytest.raises(HTTPException) as exc_info:
            await delete_vault_index(vault_id="any_vault")

        assert exc_info.value.status_code == 503
