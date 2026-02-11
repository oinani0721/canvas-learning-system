# Canvas Learning System - Grouping Service Shared Fixtures
# Extracted from test_intelligent_grouping_service.py (EPIC-33 P1-6)
"""Shared fixtures for intelligent grouping service tests."""

import sys
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.services.intelligent_grouping_service import IntelligentGroupingService


@pytest.fixture
def service() -> IntelligentGroupingService:
    """Create a service instance for testing."""
    return IntelligentGroupingService(canvas_base_path="/test/path")


@pytest.fixture
def mock_clustering_result() -> Dict[str, Any]:
    """Mock clustering result from canvas_utils.cluster_canvas_nodes()."""
    return {
        "clusters": [
            {
                "id": "cluster-1",
                "label": "逆否命题、充分条件等概念",
                "nodes": ["node-001", "node-002"],
                "node_texts": {
                    "node-001": "逆否命题 vs 否命题有什么区别",
                    "node-002": "充分条件与必要条件的对比",
                },
                "center": {"x": 400, "y": 300},
                "confidence": 0.85,
                "size": 2,
                "top_keywords": ["逆否命题", "充分条件", "对比"],
            },
            {
                "id": "cluster-2",
                "label": "命题、定义等概念",
                "nodes": ["node-003", "node-004"],
                "node_texts": {
                    "node-003": "什么是命题的定义",
                    "node-004": "真值表是什么",
                },
                "center": {"x": 600, "y": 400},
                "confidence": 0.78,
                "size": 2,
                "top_keywords": ["命题", "定义", "真值表"],
            },
        ],
        "optimization_stats": {
            "total_nodes": 4,
            "clusters_created": 2,
            "layout_time_ms": 150,
            "clustering_accuracy": 0.72,
            "algorithm": "K-means with TF-IDF",
            "feature_dimensions": 100,
        },
        "clustering_parameters": {
            "n_clusters": 2,
            "similarity_threshold": 0.3,
            "min_cluster_size": 2,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Safe canvas_utils mock fixtures (P1-4: replaces fragile sys.modules manipulation)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_canvas_utils_fail(monkeypatch):
    """
    Mock canvas_utils that raises ImportError on CanvasBusinessLogic access.

    Uses monkeypatch.setitem for automatic cleanup (safe even if test fails).
    Replaces fragile manual sys.modules save/delete/restore pattern.
    """
    class FailingModule:
        @property
        def CanvasBusinessLogic(self):
            raise ImportError("Failed to import CanvasBusinessLogic")

    monkeypatch.setitem(sys.modules, "canvas_utils", FailingModule())


@pytest.fixture
def mock_canvas_utils_success(monkeypatch):
    """
    Mock canvas_utils with a configurable CanvasBusinessLogic.

    Returns a factory function so tests can configure the mock_logic behavior.
    Uses monkeypatch.setitem for automatic cleanup.
    Replaces 6 redundant nested patch.dict + manual sys.modules assignments.
    """
    def _create(mock_logic):
        mock_module = MagicMock()
        mock_module.CanvasBusinessLogic = MagicMock(return_value=mock_logic)
        monkeypatch.setitem(sys.modules, "canvas_utils", mock_module)
        return mock_module

    return _create
