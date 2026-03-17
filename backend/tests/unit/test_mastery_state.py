"""Tests for mastery_state.py models."""

from datetime import datetime, timezone

import pytest

from app.models.mastery_state import (
    ConceptState,
    DEFAULT_BKT_PARAMS,
    MASTERY_COLORS,
    MASTERY_LABELS,
    MasteryConfig,
    OVERRIDE_LEVEL_MAP,
    SELF_ASSESS_COLOR_MAP,
)


class TestConceptStateDefaults:

    def test_default_p_mastery(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.p_mastery == 0.1

    def test_default_bkt_difficulty(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.bkt_difficulty == "medium"

    def test_default_interaction_count(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.interaction_count == 0

    def test_default_fluent_count(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.fluent_count == 0

    def test_default_override_none(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.override_value is None
        assert c.override_ts is None

    def test_default_self_assess_none(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.self_assess_value is None
        assert c.self_assess_ts is None

    def test_default_fsrs_fields(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        assert c.fsrs_stability == 0.0
        assert c.fsrs_difficulty == 0.0
        assert c.fsrs_state == 0
        assert c.fsrs_reps == 0
        assert c.fsrs_lapses == 0
        assert c.fsrs_card_data is None


class TestToNeo4jProps:

    def test_all_fields_present(self):
        c = ConceptState(concept_id="test-1", topic="Search", name="BFS")
        props = c.to_neo4j_props()
        assert props["mastery_concept_id"] == "test-1"
        assert props["mastery_topic"] == "Search"
        assert props["mastery_name"] == "BFS"
        assert props["p_mastery"] == 0.1
        assert props["bkt_difficulty"] == "medium"
        assert "fsrs_stability" in props
        assert "interaction_count" in props
        assert "fluent_count" in props

    def test_datetime_serialized_as_iso(self):
        ts = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        c = ConceptState(
            concept_id="t", topic="t", name="t",
            last_interaction_ts=ts, override_ts=ts, self_assess_ts=ts,
        )
        props = c.to_neo4j_props()
        assert props["last_interaction_ts"] == ts.isoformat()

    def test_none_datetime_serialized_as_none(self):
        c = ConceptState(concept_id="t", topic="t", name="t")
        props = c.to_neo4j_props()
        assert props["last_interaction_ts"] is None


class TestFromNeo4jProps:

    def test_roundtrip(self):
        original = ConceptState(
            concept_id="test-rt", topic="MDPs", name="Value Iteration",
            p_mastery=0.75, bkt_difficulty="hard",
            interaction_count=10, fluent_count=3,
            last_interaction_ts=datetime(2025, 6, 1, tzinfo=timezone.utc),
            fsrs_stability=5.5, fsrs_difficulty=4.2,
        )
        props = original.to_neo4j_props()
        restored = ConceptState.from_neo4j_props(props)
        assert restored.concept_id == original.concept_id
        assert restored.p_mastery == original.p_mastery
        assert restored.interaction_count == original.interaction_count

    def test_datetime_parsing_from_string(self):
        props = {
            "mastery_concept_id": "t", "mastery_topic": "t", "mastery_name": "t",
            "last_interaction_ts": "2025-01-15T10:30:00+00:00",
        }
        c = ConceptState.from_neo4j_props(props)
        assert isinstance(c.last_interaction_ts, datetime)

    def test_datetime_parsing_from_datetime(self):
        ts = datetime(2025, 1, 15, tzinfo=timezone.utc)
        props = {
            "mastery_concept_id": "t", "mastery_topic": "t", "mastery_name": "t",
            "last_interaction_ts": ts,
        }
        c = ConceptState.from_neo4j_props(props)
        assert c.last_interaction_ts == ts

    def test_missing_fields_use_defaults(self):
        props = {"name": "fallback-name"}
        c = ConceptState.from_neo4j_props(props)
        assert c.concept_id == "fallback-name"
        assert c.p_mastery == 0.1

    def test_fsrs_card_preserved(self):
        props = {
            "mastery_concept_id": "t", "mastery_topic": "t", "mastery_name": "t",
            "fsrs_card_data": '{"stability": 2.0}',
        }
        c = ConceptState.from_neo4j_props(props)
        assert c.fsrs_card_data == '{"stability": 2.0}'


class TestMasteryConfigDefaults:

    def test_override_lambda(self):
        assert MasteryConfig().override_lambda == 0.1

    def test_weight_caps(self):
        cfg = MasteryConfig()
        assert cfg.self_assess_weight_cap == 0.5
        assert cfg.override_weight_cap == 0.8

    def test_thresholds(self):
        cfg = MasteryConfig()
        assert cfg.shaky_threshold == 0.40
        assert cfg.developing_threshold == 0.70
        assert cfg.proficient_threshold == 0.90

    def test_mastered_fluent_min(self):
        assert MasteryConfig().mastered_fluent_min == 2

    def test_default_group_id(self):
        assert MasteryConfig().default_group_id == "default"


class TestBKTParams:

    def test_three_levels(self):
        assert set(DEFAULT_BKT_PARAMS.keys()) == {"easy", "medium", "hard"}

    def test_each_level_has_four_params(self):
        for level in DEFAULT_BKT_PARAMS.values():
            assert set(level.keys()) == {"P_L0", "P_T", "P_G", "P_S"}

    def test_easy_values(self):
        p = DEFAULT_BKT_PARAMS["easy"]
        assert p["P_L0"] == 0.3
        assert p["P_T"] == 0.3
        assert p["P_G"] == 0.25
        assert p["P_S"] == 0.05

    def test_medium_values(self):
        p = DEFAULT_BKT_PARAMS["medium"]
        assert p["P_L0"] == 0.1
        assert p["P_T"] == 0.2
        assert p["P_G"] == 0.20
        assert p["P_S"] == 0.10

    def test_hard_values(self):
        p = DEFAULT_BKT_PARAMS["hard"]
        assert p["P_L0"] == 0.05
        assert p["P_T"] == 0.15
        assert p["P_G"] == 0.15
        assert p["P_S"] == 0.15

    def test_probability_ranges(self):
        for level, params in DEFAULT_BKT_PARAMS.items():
            for key, val in params.items():
                assert 0.0 <= val <= 1.0, f"{level}.{key}={val} out of range"


class TestMappingCompleteness:

    def test_labels_5_levels(self):
        assert set(MASTERY_LABELS.keys()) == {0, 1, 2, 3, 4}

    def test_colors_5_levels(self):
        assert set(MASTERY_COLORS.keys()) == {0, 1, 2, 3, 4}
        assert MASTERY_COLORS[0] == "#6c757d"
        assert MASTERY_COLORS[4] == "#198754"

    def test_override_level_map(self):
        assert OVERRIDE_LEVEL_MAP["not_assessed"] is None
        assert OVERRIDE_LEVEL_MAP["shaky"] == 0.20
        assert OVERRIDE_LEVEL_MAP["mastered"] == 0.95

    def test_self_assess_color_map(self):
        assert set(SELF_ASSESS_COLOR_MAP.keys()) == {"1", "2", "3", "4", "5", "6"}
        assert SELF_ASSESS_COLOR_MAP["1"] == 0.20
        assert SELF_ASSESS_COLOR_MAP["5"] == 0.90
