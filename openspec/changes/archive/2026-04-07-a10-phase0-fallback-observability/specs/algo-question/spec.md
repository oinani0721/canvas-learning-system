# algo-question Capability Delta

## MODIFIED Requirements

### Requirement: Mastery Data Degraded Observability

The `question_generator._get_mastery_data(node_id)` helper SHALL always return a dict that contains a `mastery_degraded: Optional[str]` key. The value SHALL be `None` on the happy path (when `mastery_store.get_concept(node_id)` returns a valid `ConceptState`, `MasteryEngine` methods succeed, AND the underlying fusion engine actually produced a fused value). The value SHALL be the string `"concept_not_found"` when `store.get_concept` returns `None` (typical cause: the `CanvasNode.id` has no corresponding `EntityNode.mastery_concept_id` because the score event has not been processed yet, or an ID mapping gap exists). The value SHALL be the string `"exception"` when the function's try/except catches an `ImportError`, `AttributeError`, or `ValueError`. The value SHALL be the string `"fusion_fallback"` when `MasteryEngine.effective_proficiency_with_fallback_info(concept)` reports that the `min(p_mastery, R)` fallback path was used instead of the multi-signal fusion (either because no fusion engine is attached, or because `compute_fused_mastery` returned `active_signal_count == 0` and the engine fell through to the conservative Story 5.1 strategy).

The `ACPData.mastery_degraded` and `NodePriority.mastery_degraded` fields SHALL expose this value unchanged to downstream observability (log pipelines, prompt rendering decisions, and metrics). This parallels the existing `kg_relevance_degraded` field on `NodePriority` (which distinguishes `"empty_graph"` from `"neo4j_unavailable"` from the happy path).

This requirement was established in the A10 Phase 0 silent-bug fix and extended by A10 Phase 0 Hardening. A10 Phase 0 Hardening #2 (`a10-phase0-fallback-observability`) added the `"fusion_fallback"` value to distinguish "fusion actually produced a value" from "fusion fell through to min(p_mastery, R)" — closing a cross-layer observability gap where the `mastery_engine.effective_proficiency` return signature lost the fusion fallback state.

#### Scenario: Happy path returns None degraded flag

- **GIVEN** a `ConceptState` returned from `mastery_store.get_concept(node_id)`
- **AND** the fusion engine returns `FusionResult` with `active_signal_count > 0` and `is_fallback=False`
- **AND** all `MasteryEngine` methods succeed
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `"mastery_degraded": None`
- **AND** downstream `acp.mastery_degraded` is `None`

#### Scenario: Concept not found returns concept_not_found marker

- **GIVEN** a `node_id` for which `mastery_store.get_concept(node_id)` returns `None` (no matching `EntityNode.mastery_concept_id`)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `"mastery_degraded": "concept_not_found"`
- **AND** the other fields use the documented fallback values (`p_mastery=0.1`, `effective_proficiency=0.0`, `mastery_level=0`, `mastery_label="Not Assessed"`, `retrievability=1.0`)
- **AND** the caller can distinguish this path from the happy-path "truly not assessed" result

#### Scenario: Exception returns exception marker

- **GIVEN** any of `get_mastery_store()`, `get_mastery_engine()`, `store.get_concept()`, or the `MasteryEngine` method calls raise `ImportError`, `AttributeError`, or `ValueError`
- **WHEN** `_get_mastery_data(node_id)` catches the exception
- **THEN** the returned dict contains `"mastery_degraded": "exception"`
- **AND** a debug log is emitted with the exception type and message

#### Scenario: Fusion fallback returns fusion_fallback marker

- **GIVEN** a `ConceptState` returned from `mastery_store.get_concept(node_id)` with `interaction_count > 0`
- **AND** `MasteryEngine.effective_proficiency_with_fallback_info(concept)` returns `(eff, fusion_fallback=True)` because the attached fusion engine produced `active_signal_count == 0` (no signal had data for this concept)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `"mastery_degraded": "fusion_fallback"`
- **AND** the `effective_proficiency` value is the `min(p_mastery, R)` fallback value (not 0.0 like `concept_not_found`)
- **AND** the caller can distinguish "fusion produced a confident value" from "fusion fell through to the conservative Story 5.1 strategy"

#### Scenario: Not-assessed concept returns None degraded flag (not fusion_fallback)

- **GIVEN** a `ConceptState` with `interaction_count == 0`
- **AND** the fusion engine is attached
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned `effective_proficiency` is `0.0` (per `MasteryEngine` not-assessed contract)
- **AND** `mastery_degraded` is `None` (NOT `"fusion_fallback"`, because returning 0.0 for a not-assessed concept is the correct output, not a degradation)
- **AND** the caller can distinguish "truly not assessed" from "fusion fell through"

#### Scenario: NodePriority propagates mastery_degraded from batch path

- **GIVEN** `select_target_node` batch-gathers `_get_mastery_data` for N node_ids
- **AND** one of the results has `mastery_degraded="fusion_fallback"`
- **WHEN** the resulting `NodePriority` objects are constructed
- **THEN** the corresponding `NodePriority.mastery_degraded` equals `"fusion_fallback"`
- **AND** other node priorities retain their own `mastery_degraded` values (each node is observable independently)

#### Scenario: getattr fallback path is removed

- **GIVEN** a code review of `question_generator.py:_get_mastery_data` after this change
- **WHEN** searching for the pattern `getattr(concept, "effective_proficiency"` or `getattr(concept, "mastery_level"` or `getattr(concept, "mastery_label"` or `getattr(concept, "retrievability"`
- **THEN** no matches are found
- **AND** the function instead imports `from app.services.mastery_engine import get_mastery_engine` and uses `engine.effective_proficiency_with_fallback_info(concept)` to compute volatile fields
