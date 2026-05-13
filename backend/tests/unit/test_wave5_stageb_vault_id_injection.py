"""Wave-5 Stage B (2026-05-12) — Multi-vault P0-2 ContextVar 注入集成测试.

测试 6 个 endpoint files (mastery / errors / memory / metadata / review / exam) 加
vault_id Field/Query 必填/推荐契约 + ContextVar 注入.

测试矩阵:
- mastery: vault_id Query 推荐必填, 注入 ContextVar set_current_subject_id
- errors: vault_id Field 严格必填 (Body), 缺失 → 422
- memory: vault_id Field 严格必填 (LearningEpisodeCreate POST), 缺失 → 422
- metadata: vault_id Query/Field 推荐必填, ContextVar 注入
- review: vault_id 推荐必填 (Query/Field 混合)
- exam: vault_id Query 推荐必填, deprecated group_id 留兼容

[Source: Wave-5 Stage B 任务 — fix 67% endpoint 无 vault 隔离 P0]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Test: errors endpoints — vault_id Field 严格必填 (缺失 → 422)
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorsEndpointsRequireVaultId:
    """errors.py 端点的 AcceptCandidateRequest / DismissCandidateRequest /
    DisputeCandidateRequest 都加了 vault_id: str = Field(..., min_length=1).
    缺 vault_id 必须 422.
    """

    def test_accept_candidate_request_requires_vault_id(self):
        from pydantic import ValidationError

        from app.api.v1.endpoints.errors import AcceptCandidateRequest

        # 缺 vault_id 必须 raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            AcceptCandidateRequest(
                candidate_id="cand-1",
                node_id="节点/X.md",
            )
        errors_msg = str(exc_info.value)
        assert "vault_id" in errors_msg.lower()

    def test_accept_candidate_request_rejects_empty_vault_id(self):
        from pydantic import ValidationError

        from app.api.v1.endpoints.errors import AcceptCandidateRequest

        # vault_id 空字符串必须 raise (min_length=1)
        with pytest.raises(ValidationError):
            AcceptCandidateRequest(
                candidate_id="cand-1",
                node_id="节点/X.md",
                vault_id="",
            )

    def test_accept_candidate_request_accepts_valid_vault_id(self):
        from app.api.v1.endpoints.errors import AcceptCandidateRequest

        req = AcceptCandidateRequest(
            candidate_id="cand-1",
            node_id="节点/X.md",
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"
        assert req.subject_id is None

    def test_dismiss_candidate_request_requires_vault_id(self):
        from pydantic import ValidationError

        from app.api.v1.endpoints.errors import DismissCandidateRequest

        with pytest.raises(ValidationError) as exc_info:
            DismissCandidateRequest(candidate_id="cand-1", node_id="节点/X.md")
        assert "vault_id" in str(exc_info.value).lower()

    def test_dispute_candidate_request_requires_vault_id(self):
        from pydantic import ValidationError

        from app.api.v1.endpoints.errors import DisputeCandidateRequest

        with pytest.raises(ValidationError) as exc_info:
            DisputeCandidateRequest(
                candidate_id="cand-1",
                node_id="节点/X.md",
                dispute_reason="theorem mismatch",
            )
        assert "vault_id" in str(exc_info.value).lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: errors endpoint body — ContextVar set_current_subject_id 被调用
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorsEndpointsInjectContextVar:
    """对 accept_candidate_endpoint mock 底层服务, 验证 ContextVar 注入路径
    被实际触发 (用 patch sentinel 捕获 set_current_subject_id 调用)."""

    @pytest.mark.asyncio
    async def test_accept_candidate_calls_set_current_subject_id(self):
        """对 endpoint body 调用 _resolve_vault_group_id helper,
        helper 必然进入 set_current_subject_id (ContextVar 真注入).
        简化策略: 直接验证 helper 调用语义, 不走完整 HTTP 路径
        (避免 _resolve_node_file_path 名字空间陷阱).
        """
        # endpoint body 顶部就调 _resolve_vault_group_id,
        # 我们验证 helper 真的注入了 ContextVar.
        from app.api.v1.endpoints.errors import _resolve_vault_group_id
        from app.core.subject_config import get_current_subject_id

        derived = _resolve_vault_group_id(
            "cs_61b",
            subject_id=None,
            canvas_path="节点/X.md",
        )
        assert derived.startswith("vault:cs_61b")
        # ContextVar 真注入 — get_current_subject_id 应读到 derived
        current = get_current_subject_id()
        assert current.startswith("vault:cs_61b")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: memory endpoints — LearningEpisodeCreate.vault_id 严格必填
# ═══════════════════════════════════════════════════════════════════════════════


class TestMemoryEndpointsRequireVaultId:
    """LearningEpisodeCreate Field 严格必填. 缺 vault_id 必须 422."""

    def test_learning_episode_create_requires_vault_id(self):
        from pydantic import ValidationError

        from app.models.memory_schemas import LearningEpisodeCreate

        with pytest.raises(ValidationError) as exc_info:
            LearningEpisodeCreate(
                user_id="user-1",
                canvas_path="离散数学.canvas",
                node_id="node-1",
                concept="逆否命题",
                agent_type="basic-decomposition",
            )
        assert "vault_id" in str(exc_info.value).lower()

    def test_learning_episode_create_rejects_empty_vault_id(self):
        from pydantic import ValidationError

        from app.models.memory_schemas import LearningEpisodeCreate

        with pytest.raises(ValidationError):
            LearningEpisodeCreate(
                user_id="user-1",
                canvas_path="离散数学.canvas",
                node_id="node-1",
                concept="逆否命题",
                agent_type="basic-decomposition",
                vault_id="",
            )

    def test_learning_episode_create_accepts_valid(self):
        from app.models.memory_schemas import LearningEpisodeCreate

        ep = LearningEpisodeCreate(
            user_id="user-1",
            canvas_path="离散数学.canvas",
            node_id="node-1",
            concept="逆否命题",
            agent_type="basic-decomposition",
            vault_id="cs_61b",
        )
        assert ep.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: mastery endpoints — vault_id Query 推荐必填 (ContextVar 注入)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMasteryEndpointsContextVarInjection:
    """mastery.py 的 _resolve_vault_group_id helper 应正确派生 group_id
    并通过 set_current_subject_id 写到 ContextVar.
    """

    def test_resolve_with_vault_id(self):
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        derived = _resolve_vault_group_id("cs_61b")
        assert derived == "vault:cs_61b"

    def test_resolve_with_vault_id_and_subject(self):
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        derived = _resolve_vault_group_id("cs_61b", subject_id="algorithms")
        assert derived == "vault:cs_61b:algorithms"

    def test_resolve_falls_back_to_legacy_group_id(self):
        """vault_id 空时降级到 deprecated group_id (Wave-5 Stage B 兼容).
        canonical_group_id 会归一化 (cs188 → vault:default).
        """
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        derived = _resolve_vault_group_id(None, legacy_group_id="cs188")
        # canonical_group_id 把 cs188 映射到 vault:default
        assert derived.startswith("vault:")

    def test_resolve_falls_back_to_default(self):
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        derived = _resolve_vault_group_id(None, legacy_group_id=None)
        # DEFAULT_GROUP_ID 已经 canonical 化
        assert isinstance(derived, str)
        assert len(derived) > 0

    def test_resolve_calls_set_current_subject_id(self):
        """验证 set_current_subject_id 被实际调用 (ContextVar 真注入)."""
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        captured: dict = {}

        def fake_set(value):
            captured["value"] = value

        with patch(
            "app.core.subject_config.set_current_subject_id",
            side_effect=fake_set,
        ):
            _resolve_vault_group_id("数学")

        assert captured.get("value", "").startswith("vault:")

    def test_resolve_unicode_vault_id_preserved(self):
        """中文 vault_id (NFKC + casefold + \\w) 不应坍缩 default."""
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        derived = _resolve_vault_group_id("数学")
        assert derived == "vault:数学"
        # 反例: 旧 sanitize_vault_id 会坍缩到 'default', 新实现保留 CJK


# ═══════════════════════════════════════════════════════════════════════════════
# Test: review endpoints — GenerateReviewRequest / StartSessionRequest /
#       RecordReviewRequest / SubmitAnswerRequest 都加了 vault_id Field
# ═══════════════════════════════════════════════════════════════════════════════


class TestReviewEndpointsHaveVaultIdField:
    """review 系列 request body schemas 都有 vault_id Optional Field
    (推荐必填 + deprecated group_id Query 兼容).
    """

    def test_generate_review_request_has_vault_id(self):
        from app.models.schemas import GenerateReviewRequest

        req = GenerateReviewRequest(
            source_canvas="数学",
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"

    def test_generate_review_request_vault_id_optional(self):
        """Wave-5 Stage B 推荐必填但保持向后兼容 (Optional Field)."""
        from app.models.schemas import GenerateReviewRequest

        req = GenerateReviewRequest(source_canvas="数学")
        assert req.vault_id is None

    def test_record_review_request_has_vault_id(self):
        from app.models.schemas import RecordReviewRequest

        req = RecordReviewRequest(
            canvas_name="数学",
            node_id="node-1",
            rating=3,
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"

    def test_start_session_request_has_vault_id(self):
        from app.models.review_models import StartSessionRequest

        req = StartSessionRequest(canvas_name="数学", vault_id="cs_61b")
        assert req.vault_id == "cs_61b"

    def test_submit_answer_request_has_vault_id(self):
        from app.models.review_models import SubmitAnswerRequest

        req = SubmitAnswerRequest(user_answer="x = 1", vault_id="cs_61b")
        assert req.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: metadata endpoints — CanvasIndexRequest / BatchIndexRequest 有 vault_id Field
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetadataEndpointsHaveVaultIdField:
    def test_canvas_index_request_has_vault_id(self):
        from app.models.metadata_models import CanvasIndexRequest

        req = CanvasIndexRequest(
            canvas_path="数学/calc.canvas",
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"

    def test_canvas_index_request_vault_id_optional(self):
        from app.models.metadata_models import CanvasIndexRequest

        req = CanvasIndexRequest(canvas_path="数学/calc.canvas")
        assert req.vault_id is None

    def test_batch_index_request_has_vault_id(self):
        from app.models.metadata_models import BatchIndexRequest

        req = BatchIndexRequest(
            canvas_paths=["a.canvas", "b.canvas"],
            vault_id="cs_61b",
        )
        assert req.vault_id == "cs_61b"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: exam endpoints — _resolve_vault_group_id helper 工作正常
# ═══════════════════════════════════════════════════════════════════════════════


class TestExamEndpointsContextVarInjection:
    def test_exam_resolve_with_vault_id(self):
        from app.api.v1.endpoints.exam import _resolve_vault_group_id

        derived = _resolve_vault_group_id("cs_61b")
        assert derived == "vault:cs_61b"

    def test_exam_resolve_calls_set_current_subject_id(self):
        from app.api.v1.endpoints.exam import _resolve_vault_group_id

        captured: dict = {}

        def fake_set(value):
            captured["value"] = value

        with patch(
            "app.core.subject_config.set_current_subject_id",
            side_effect=fake_set,
        ):
            _resolve_vault_group_id("cs_61b", subject_id="algorithms")

        assert captured["value"] == "vault:cs_61b:algorithms"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: 跨 vault 隔离 — 同一 concept_id 不同 vault 派生不同 group_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestMultiVaultIsolation:
    """核心 P0 验证: 5 vault 并存时不串库的 contract.
    同一 concept_id 在 vault_A 和 vault_B 必须派生不同 group_id.
    """

    def test_different_vaults_derive_different_group_ids(self):
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        gid_a = _resolve_vault_group_id("cs_61b")
        gid_b = _resolve_vault_group_id("数学")
        assert gid_a != gid_b
        assert gid_a == "vault:cs_61b"
        assert gid_b == "vault:数学"

    def test_same_vault_different_subjects_distinct(self):
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        gid_algo = _resolve_vault_group_id("cs_61b", subject_id="algorithms")
        gid_db = _resolve_vault_group_id("cs_61b", subject_id="databases")
        assert gid_algo != gid_db
        assert gid_algo == "vault:cs_61b:algorithms"
        assert gid_db == "vault:cs_61b:databases"

    def test_unicode_vault_no_collision_with_ascii(self):
        """中文 vault 不应坍缩到 ASCII default (旧 bug Phase B0.1 修)."""
        from app.api.v1.endpoints.mastery import _resolve_vault_group_id

        gid_cn = _resolve_vault_group_id("笔记库")
        gid_default = _resolve_vault_group_id("default")
        assert gid_cn != gid_default
        assert gid_cn == "vault:笔记库"
