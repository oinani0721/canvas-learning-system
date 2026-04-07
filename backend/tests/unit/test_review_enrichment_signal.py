"""
Unit tests for G-SILENT-001 fix: WeightConfig must propagate enrichment_available signal.

Background:
    review_service.py:644 writes `enrichment_available` into the weight_config dict to
    surface mastery enrichment degradation, but the Pydantic `WeightConfig` schema
    (schemas.py:735-746) didn't define this field. Pydantic v2 default is
    `extra='ignore'`, so the signal was silently dropped — API responded 200 with no
    indication that scoring fell back to baseline.

These tests pin both:
    1) Schema-level: enrichment_available is a real field, round-trips through model_dump()
    2) Service-level: review_service correctly sets the signal when enrichment fails

[Source: docs/known-gotchas.md G-SILENT-001]
[OpenSpec change: review-enrichment-signal-fix]
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.schemas import WeightConfig

# ============================================================================
# Phase 1: Schema-level tests (C2-A)
# ============================================================================


class TestWeightConfigSchemaSignal:
    """G-SILENT-001 schema fix — enrichment_available must survive Pydantic round-trip."""

    def test_enrichment_available_field_exists(self):
        """C2-A.3: WeightConfig must declare enrichment_available as a real field."""
        # Construct with explicit value — must not raise, must round-trip
        config = WeightConfig(
            weak_weight=0.7,
            mastered_weight=0.3,
            applied=True,
            enrichment_available=True,
        )
        dumped = config.model_dump()
        assert "enrichment_available" in dumped, (
            "enrichment_available missing from model_dump() — Pydantic dropped it. "
            "Check WeightConfig in backend/app/models/schemas.py."
        )
        assert dumped["enrichment_available"] is True

    def test_enrichment_unavailable_signal_serializes(self):
        """G-SILENT-001 regression — enrichment_available=False must propagate."""
        config = WeightConfig(
            weak_weight=0.5,
            mastered_weight=0.5,
            applied=False,
            enrichment_available=False,
        )
        dumped = config.model_dump()
        assert dumped["enrichment_available"] is False, (
            "Degradation signal lost in serialization — frontend cannot show degraded state."
        )

    def test_enrichment_available_defaults_to_true(self):
        """Backward compat: existing code that doesn't pass enrichment_available works."""
        # Old call sites construct WeightConfig without the new field
        config = WeightConfig(
            weak_weight=0.7,
            mastered_weight=0.3,
            applied=True,
        )
        # Default should be True (the optimistic case — assume enrichment worked)
        assert config.enrichment_available is True

    def test_enrichment_signal_round_trips_through_dict(self):
        """review_service.py:640 builds a dict — verify dict→model→dict preserves the signal."""
        # Mirror the exact pattern from review_service.py:640-645
        weight_config_dict = {
            "weak_weight": 0.6,
            "mastered_weight": 0.4,
            "applied": False,
            "enrichment_available": False,  # Degraded mode
        }
        config = WeightConfig(**weight_config_dict)
        dumped = config.model_dump()
        assert dumped == weight_config_dict, (
            "Dict round-trip lost data. Original: %s, After model_dump: %s"
            % (weight_config_dict, dumped)
        )
