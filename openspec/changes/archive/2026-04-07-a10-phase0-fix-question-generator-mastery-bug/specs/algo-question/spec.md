# algo-question Capability Delta

## ADDED Requirements

### Requirement: Mastery Data Flows Through MasteryEngine

The `question_generator._get_mastery_data(node_id)` helper SHALL obtain volatile mastery fields (`effective_proficiency`, `mastery_level`, `mastery_label`, `retrievability`) by calling `MasteryEngine` instance methods on a `ConceptState` returned from `mastery_store.get_concept(node_id)`. The helper SHALL NOT use `getattr(concept, "<volatile_field>", default)` to read these fields, because `ConceptState` (defined at `backend/app/models/mastery_state.py`) is documented as storing only stable fields and explicitly never persists volatile values. Reading volatile fields via `getattr` silently returns the default value (e.g., `0.0`), which corrupts downstream difficulty selection and Gemini prompt rendering.

This requirement exists because of a long-standing silent bug discovered during ChatGPT Deep Research review of the previous A10 change `a10-fsrs-fusion-formalization`. The fix wires `question_generator` into the existing `get_mastery_engine()` global singleton (initialized at `backend/app/main.py:220-261` with fusion engine attached), restoring the intended Story 5.6 multi-signal fusion consumption path.

#### Scenario: Volatile fields are computed via MasteryEngine

- **GIVEN** a `ConceptState` instance returned by `mastery_store.get_concept(node_id)`
- **AND** the global `MasteryEngine` singleton is fusion-enabled (initialized at startup)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned dict contains `effective_proficiency = mastery_engine.effective_proficiency(concept)`
- **AND** the returned dict contains `mastery_level = mastery_engine.mastery_level(concept)`
- **AND** the returned dict contains `mastery_label = mastery_engine.mastery_label(concept)`
- **AND** the returned dict contains `retrievability = mastery_engine.get_retrievability(concept)`

#### Scenario: Non-zero fused mastery propagates to ACP

- **GIVEN** a `ConceptState` whose 5 signals fuse to `fused_mastery = 0.85`
- **AND** the concept has no override and no self-assess decay
- **WHEN** `_get_mastery_data(node_id)` is invoked and the result populates an `ACPData` object via `acp.effective_proficiency = mastery.get("effective_proficiency", 0.0)`
- **THEN** `acp.effective_proficiency == 0.85` (within float tolerance), not `0.0`

#### Scenario: Difficulty selector reflects real proficiency

- **GIVEN** an `ACPData` with `effective_proficiency = 0.85` populated by the fixed `_get_mastery_data`
- **WHEN** the question_generator difficulty branch evaluates `acp.effective_proficiency` against the thresholds at lines 482-489
- **THEN** the chosen `difficulty_level` is `"hard"` (the branch `else` after `0.7`), not `"easy"`

#### Scenario: Not-assessed concepts return zero proficiency

- **GIVEN** a `ConceptState` with `interaction_count == 0` (never assessed)
- **WHEN** `_get_mastery_data(node_id)` is invoked
- **THEN** the returned `effective_proficiency` is `0.0` (per `MasteryEngine.effective_proficiency` line 344-346 contract)
- **AND** `mastery_label` is `"Not Assessed"`
- **AND** the difficulty selector still picks `"easy"` (correctly, because the learner has no demonstrated mastery)

#### Scenario: getattr fallback path is removed

- **GIVEN** a code review of `question_generator.py:_get_mastery_data` after this change
- **WHEN** searching for the pattern `getattr(concept, "effective_proficiency"` or `getattr(concept, "mastery_level"` or `getattr(concept, "mastery_label"` or `getattr(concept, "retrievability"`
- **THEN** no matches are found
- **AND** the function instead imports `from app.services.mastery_engine import get_mastery_engine` and uses `engine.effective_proficiency(concept)` etc.
