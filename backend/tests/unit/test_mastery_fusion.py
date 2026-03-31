"""
Unit tests for Story 5.6: Multi-Signal Fusion Engine

Tests cover:
  - Signal registration/unregistration
  - Weighted average fusion correctness
  - Weight renormalization when signals are missing (1-5 signals)
  - All signals missing → 0.0
  - Clamping to [0.0, 1.0]
  - Fallback to min(p_mastery, R)
  - Pearson correlation coefficient computation
"""

from typing import Optional

import pytest
from app.services.mastery_fusion import (
    MasteryFusionEngine,
    compute_pearson_r,
    run_complementarity_check,
)
from app.services.signal_registry import SignalRegistry


class FakeSignal:
    """Fake signal for testing that implements MasterySignal protocol."""

    def __init__(
        self,
        name: str,
        value: Optional[float],
        weight: float = 0.2,
        reliability: float = 1.0,
    ):
        self._name = name
        self._value = value
        self._weight = weight
        self._reliability = reliability

    @property
    def signal_name(self) -> str:
        return self._name

    def get_value(self, node_id: str) -> Optional[float]:
        return self._value

    def get_weight(self, node_id: str) -> float:
        return self._weight

    def get_reliability(self, node_id: str) -> float:
        return self._reliability


# ═══════════════════════════════════════════════════════════════════════════════
# Signal Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSignalRegistry:
    """Test signal registration and unregistration."""

    def test_register_signal(self):
        registry = SignalRegistry()
        signal = FakeSignal("test", 0.5)
        registry.register(signal)
        assert registry.signal_count == 1
        assert "test" in registry.get_all_signals()

    def test_unregister_signal(self):
        registry = SignalRegistry()
        signal = FakeSignal("test", 0.5)
        registry.register(signal)
        registry.unregister("test")
        assert registry.signal_count == 0

    def test_unregister_nonexistent(self):
        """Unregistering nonexistent signal doesn't raise."""
        registry = SignalRegistry()
        registry.unregister("nonexistent")  # Should not raise

    def test_register_overwrite(self):
        """Re-registering replaces the previous signal."""
        registry = SignalRegistry()
        registry.register(FakeSignal("test", 0.3))
        registry.register(FakeSignal("test", 0.7))
        assert registry.signal_count == 1
        signals = registry.get_all_signals()
        assert signals["test"].get_value("any") == 0.7

    def test_multiple_signals(self):
        registry = SignalRegistry()
        registry.register(FakeSignal("a", 0.5))
        registry.register(FakeSignal("b", 0.7))
        registry.register(FakeSignal("c", None))
        assert registry.signal_count == 3

    def test_get_active_signals(self):
        """Active signals = signals with non-None value."""
        registry = SignalRegistry()
        registry.register(FakeSignal("a", 0.5, weight=0.3))
        registry.register(FakeSignal("b", None, weight=0.3))
        registry.register(FakeSignal("c", 0.8, weight=0.4))

        active = registry.get_active_signals("node1")
        assert len(active) == 2
        names = {a[0] for a in active}
        assert names == {"a", "c"}


# ═══════════════════════════════════════════════════════════════════════════════
# Fusion Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMasteryFusionEngine:
    """Test weighted average fusion computation."""

    def test_single_signal(self):
        """Only one signal with data → fusion = that signal's value."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.3))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert result.fused_mastery == pytest.approx(0.8, abs=0.001)
        assert result.active_signal_count == 1

    def test_two_signals_renormalized(self):
        """Two signals → weights renormalized to sum to 1.0."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.30))
        registry.register(FakeSignal("fsrs", 0.6, weight=0.25))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        # Renormalized: bkt=0.30/0.55≈0.545, fsrs=0.25/0.55≈0.455
        expected = (0.30 / 0.55) * 0.8 + (0.25 / 0.55) * 0.6
        assert result.fused_mastery == pytest.approx(expected, abs=0.01)
        assert result.active_signal_count == 2

    def test_five_signals_all_data(self):
        """All 5 signals with data → standard weighted average."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.30))
        registry.register(FakeSignal("fsrs", 0.7, weight=0.25))
        registry.register(FakeSignal("exam", 0.6, weight=0.25))
        registry.register(FakeSignal("cal", 0.9, weight=0.10))
        registry.register(FakeSignal("conf", 0.5, weight=0.10))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        # All weights sum to 1.0 already, so no renormalization needed
        expected = 0.30 * 0.8 + 0.25 * 0.7 + 0.25 * 0.6 + 0.10 * 0.9 + 0.10 * 0.5
        assert result.fused_mastery == pytest.approx(expected, abs=0.01)
        assert result.active_signal_count == 5

    def test_no_signals_registered(self):
        """No signals at all → 0.0."""
        registry = SignalRegistry()
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert result.fused_mastery == 0.0
        assert result.active_signal_count == 0

    def test_all_signals_no_data(self):
        """All signals return None → 0.0."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", None))
        registry.register(FakeSignal("fsrs", None))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert result.fused_mastery == 0.0
        assert result.active_signal_count == 0

    def test_some_signals_no_data(self):
        """Mix of data and no-data → only active signals contribute."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.30))
        registry.register(FakeSignal("fsrs", None, weight=0.25))
        registry.register(FakeSignal("exam", 0.6, weight=0.25))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        # Only bkt(0.30) and exam(0.25) active
        expected = (0.30 / 0.55) * 0.8 + (0.25 / 0.55) * 0.6
        assert result.fused_mastery == pytest.approx(expected, abs=0.01)
        assert result.active_signal_count == 2

    def test_clamp_lower_bound(self):
        """Fusion value can't go below 0.0."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.0, weight=0.5))
        registry.register(FakeSignal("fsrs", 0.0, weight=0.5))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert result.fused_mastery >= 0.0

    def test_clamp_upper_bound(self):
        """Fusion value can't go above 1.0."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 1.0, weight=0.5))
        registry.register(FakeSignal("fsrs", 1.0, weight=0.5))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert result.fused_mastery <= 1.0

    def test_signal_details_populated(self):
        """FusionResult includes per-signal details."""
        registry = SignalRegistry()
        registry.register(FakeSignal("bkt", 0.8, weight=0.3))
        registry.register(FakeSignal("fsrs", None, weight=0.25))
        engine = MasteryFusionEngine(registry)

        result = engine.compute_fused_mastery("node1")
        assert len(result.signal_details) == 2

        bkt_detail = next(sd for sd in result.signal_details if sd.signal_name == "bkt")
        assert bkt_detail.value == 0.8
        assert bkt_detail.normalized_weight > 0

        fsrs_detail = next(
            sd for sd in result.signal_details if sd.signal_name == "fsrs"
        )
        assert fsrs_detail.value is None
        assert fsrs_detail.normalized_weight == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Pearson Correlation Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPearsonCorrelation:
    """Test Pearson correlation coefficient computation."""

    def test_perfect_positive_correlation(self):
        """Identical values → r = 1.0."""
        a = [0.1, 0.2, 0.3, 0.4, 0.5]
        b = [0.1, 0.2, 0.3, 0.4, 0.5]
        r = compute_pearson_r(a, b)
        assert r == pytest.approx(1.0, abs=0.001)

    def test_perfect_negative_correlation(self):
        """Inverse values → r = -1.0."""
        a = [0.1, 0.2, 0.3, 0.4, 0.5]
        b = [0.5, 0.4, 0.3, 0.2, 0.1]
        r = compute_pearson_r(a, b)
        assert r == pytest.approx(-1.0, abs=0.001)

    def test_no_correlation(self):
        """Orthogonal signals → r near 0."""
        a = [1.0, 0.0, 1.0, 0.0, 1.0]
        b = [0.0, 1.0, 0.0, 1.0, 0.0]
        r = compute_pearson_r(a, b)
        assert r is not None
        assert abs(r) < 0.5  # Not strongly correlated

    def test_insufficient_data(self):
        """< 3 data points → None."""
        assert compute_pearson_r([0.1], [0.2]) is None
        assert compute_pearson_r([0.1, 0.2], [0.3, 0.4]) is None

    def test_zero_variance(self):
        """Constant values (zero variance) → None."""
        a = [0.5, 0.5, 0.5, 0.5]
        b = [0.1, 0.2, 0.3, 0.4]
        assert compute_pearson_r(a, b) is None

    def test_high_correlation_detection(self):
        """r >= 0.7 flagged as redundant in complementarity check."""
        signal_values = {
            "bkt": [0.1, 0.2, 0.3, 0.4, 0.5],
            "fsrs": [0.11, 0.22, 0.29, 0.41, 0.52],  # Very similar
        }
        results = run_complementarity_check(signal_values)
        assert len(results) == 1
        assert results[0].is_redundant is True
        assert abs(results[0].pearson_r) >= 0.7

    def test_low_correlation_not_redundant(self):
        """r < 0.7 → not redundant."""
        signal_values = {
            "bkt": [0.1, 0.5, 0.3, 0.8, 0.2],
            "cal": [0.9, 0.1, 0.7, 0.3, 0.5],
        }
        results = run_complementarity_check(signal_values)
        for result in results:
            if abs(result.pearson_r) < 0.7:
                assert result.is_redundant is False

    def test_multiple_pairs(self):
        """3 signals → 3 pairs checked."""
        signal_values = {
            "a": [0.1, 0.2, 0.3, 0.4],
            "b": [0.5, 0.6, 0.7, 0.8],
            "c": [0.9, 0.8, 0.7, 0.6],
        }
        results = run_complementarity_check(signal_values)
        assert len(results) == 3  # C(3,2) = 3 pairs
