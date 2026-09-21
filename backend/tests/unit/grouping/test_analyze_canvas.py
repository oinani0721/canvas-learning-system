# Canvas Learning System - Analyze Canvas Tests
# Split from test_intelligent_grouping_service.py (EPIC-33 P1-6)
"""Tests for analyze_canvas, silhouette score, and subject isolation."""

import copy
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest
from app.models.intelligent_parallel_models import (
    IntelligentParallelResponse,
)
from app.services.intelligent_grouping_service import (
    CanvasNotFoundError,
    IntelligentGroupingService,
)


class TestAnalyzeCanvas:
    """Tests for analyze_canvas method - AC-33.4.1."""

    @pytest.mark.asyncio
    async def test_analyze_canvas_returns_groups(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test that analyze_canvas returns grouped nodes with recommendations."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas(
                    canvas_path="数学/离散数学.canvas",
                    target_color="3",
                )

        assert isinstance(result, IntelligentParallelResponse)
        assert result.total_nodes == 4
        assert len(result.groups) == 2
        assert result.canvas_path == "数学/离散数学.canvas"

    @pytest.mark.asyncio
    async def test_analyze_canvas_not_found(self, service: IntelligentGroupingService):
        """Test that CanvasNotFoundError is raised when canvas doesn't exist."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_resolve.return_value = mock_path

            with pytest.raises(CanvasNotFoundError) as exc_info:
                await service.analyze_canvas("nonexistent.canvas")

            assert "not found" in str(exc_info.value)


class TestSilhouetteScore:
    """Tests for Silhouette Score quality evaluation - AC-33.4.3."""

    @pytest.mark.asyncio
    async def test_silhouette_score_returned(self, service: IntelligentGroupingService, mock_clustering_result: Dict):
        """Test that silhouette_score is correctly returned."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("test.canvas")

        assert result.silhouette_score == 0.72
        assert result.recommended_k == 2

    @pytest.mark.asyncio
    async def test_low_silhouette_score_warning(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict, caplog
    ):
        """Test that low silhouette score triggers a warning."""
        mock_clustering_result = copy.deepcopy(mock_clustering_result)
        mock_clustering_result["optimization_stats"]["clustering_accuracy"] = 0.2

        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("test.canvas")

        assert result.silhouette_score == 0.2
        assert any("Low clustering quality" in record.message for record in caplog.records)


class TestSubjectIsolation:
    """Tests for subject isolation with group_id - AC-33.4.5."""

    @pytest.mark.asyncio
    async def test_group_id_extraction_chinese(self, service: IntelligentGroupingService, mock_clustering_result: Dict):
        """Test group_id extraction for Chinese paths."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("数学/离散数学.canvas")

        assert result.subject == "数学"
        # 契约演进（4104020d, 2026-05-12 "backend p0 multi-vault leak 修复"）：
        # build_group_id(subject, canvas_name) → build_vault_group_id(vault, subject_id, canvas_path)，
        # 格式由 "<subject>:<canvas>" 变为 D16 的 "vault:<vault_id>:<subject_id>"。
        # 旧格式在多 vault 下会碰撞（不同 vault 的同名学科拿到同一 group_id）——这正是该
        # commit 要修的泄漏面，故本条不是退化而是隔离性加强。[CARD-RED-C2]
        assert result.subject_group_id == "vault:default:数学"

    @pytest.mark.asyncio
    async def test_group_id_with_skip_directories(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test group_id extraction skips common root directories."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("笔记库/物理/力学.canvas")

        assert result.subject == "物理"
        # 同上 4104020d：D16 格式 vault:<vault_id>:<subject_id>
        assert result.subject_group_id == "vault:default:物理"

    @pytest.mark.asyncio
    async def test_group_id_uses_vault_scoped_format_not_legacy(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """防退化锚：subject_group_id 必须是 vault 作用域格式，不得退回旧的裸格式。

        4104020d(2026-05-12) 把 build_group_id(subject, canvas_name) 换成
        build_vault_group_id —— 旧格式 "<subject>:<canvas>" 不含 vault 维度，
        不同 vault 的同名学科会拿到同一个 group_id（跨 vault 数据互相看见）。
        上面两条只锁具体字面量，若有人改回旧构造且恰好路径也变了，仍可能同时改绿；
        本条锁**格式属性本身**（必须被 is_vault_group_id 认可、必须以 "vault:" 起头），
        与具体 subject 无关。[CARD-RED-C2]
        """
        from app.core.subject_config import is_vault_group_id

        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("数学/离散数学.canvas")

        gid = result.subject_group_id
        assert gid.startswith("vault:"), f"group_id 退回裸格式: {gid!r}"
        assert is_vault_group_id(gid), f"group_id 不被 vault 格式校验器认可: {gid!r}"
        # 旧格式的特征：只有一个冒号且不以 vault: 起头
        assert gid.count(":") >= 2, f"group_id 缺少 vault 维度: {gid!r}"

    @pytest.mark.asyncio
    async def test_group_id_single_file(self, service: IntelligentGroupingService, mock_clustering_result: Dict):
        """Test group_id extraction for single file (no directory)."""
        with patch.object(service, "_resolve_canvas_path") as mock_resolve:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            with patch.object(service, "_perform_clustering", return_value=mock_clustering_result):
                result = await service.analyze_canvas("离散数学.canvas")

        assert result.subject == "离散数学"
