"""
Mastery Domain Gateway — 精通度与复习统一入口

Strangler Fig Pattern: 所有外部调用应通过此 gateway 访问 mastery 领域。

包含: mastery_engine, mastery_store, mastery_fusion, review_service,
       weight_calculator, signal_registry
"""

from __future__ import annotations

# ── 精通度计算（BKT + FSRS） ──
from app.services.mastery_engine import MasteryEngine, get_mastery_engine

# ── 精通度持久化（Neo4j） ──
from app.services.mastery_store import MasteryStore, get_mastery_store

# ── 5 信号融合 ──
from app.services.mastery_fusion import MasteryFusionEngine

# ── 复习调度（FSRS-4.5） ──
from app.services.review_service import (
    ReviewService,
    get_review_service,
    FSRS_AVAILABLE,
    FSRS_RUNTIME_OK,
    MAX_HISTORY_RECORDS,
)

# ── 弱点权重 ──
from app.services.weight_calculator import WeightCalculator

# ── 信号注册表 ──
from app.services.signal_registry import SignalRegistry

__all__ = [
    "MasteryEngine",
    "get_mastery_engine",
    "MasteryStore",
    "get_mastery_store",
    "MasteryFusionEngine",
    "ReviewService",
    "get_review_service",
    "FSRS_AVAILABLE",
    "FSRS_RUNTIME_OK",
    "MAX_HISTORY_RECORDS",
    "WeightCalculator",
    "SignalRegistry",
]
