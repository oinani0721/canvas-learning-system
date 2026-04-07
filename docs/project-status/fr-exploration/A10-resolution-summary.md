# A10 Resolution Summary — FSRS Fusion Architecture (ChatGPT Deep Research Review Entry)

> **Status**: Pure analysis document (no code changes). A10 was an architectural clarity question, and the "resolution" is the formalization of how the 5-signal fusion engine actually works today + identification of three independent weighting systems that bypass it.
>
> **Entry point**: ChatGPT Deep Research starts here. Read the sections in order, then consult the source files referenced in Section 9. The 7 review questions in Section 8 are the core ask.
>
> **Twin document**: This file mirrors the structured `design.md` inside the (now archived) OpenSpec change [`2026-04-07-a10-fsrs-fusion-formalization`](../../../openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/design.md). The 4 formalized requirements were merged into the canonical [`openspec/specs/algo-fusion/spec.md`](../../../openspec/specs/algo-fusion/spec.md) on 2026-04-07. This file is the project-status-friendly version that lives next to the original A10 question.
>
> **Frozen at**: 2026-04-07 working tree. Source line numbers verified by 6 sed samplings in plan phase.

---

## 1. The Original A10 Question

From [`A10.md`](A10.md) line 88 (user2 batch):

> 「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」

This is **not** a bug report. It is an architectural clarity question. The user wants to know how FSRS retrievability interacts with the other mastery signals (BKT, exam scores, calibration, self-confidence) to produce what the UI displays as a node's "mastery."

---

## 2. The One-Sentence Answer

FSRS fusion **is implemented in form** at `mastery_fusion.py` as a 5-signal weighted average — but it is **bypassed by two shortcuts**: `verification_service._advance_concept()` simply increments a queue index, and `recommendation_service` sorts by a confidence score derived from text similarity and shared neighbors. The result is **three parallel weighting systems that never read each other's outputs**.

This decoupling is what A10 was trying to surface.

---

## 3. The 5-Signal Fusion Architecture (Layer 1: implemented)

### 3.1 Signal Registry

| Signal | Base Weight | File:Line | Data Source |
|---|---|---|---|
| BKT Mastery | 0.30 | `signal_registry.py:105` | `concept.p_mastery` (Bayesian posterior) |
| FSRS Retrievability | 0.25 | `signal_registry.py:140` | FSRS-4.5 stability decay |
| Exam Score Average | 0.25 | `signal_registry.py:174` | Recent calibrated answer records, normalized |
| Calibration Bias | 0.10 | `signal_registry.py:212` | `1.0 - |signed_bias|` (metacognitive correction) |
| Self-Confidence Average | 0.10 | `signal_registry.py:249` | User self-rating |

### 3.2 The `compute_fused_mastery()` formula

From [`backend/app/services/mastery_fusion.py:103-114`](../../../backend/app/services/mastery_fusion.py):

```python
active = registry.get_active_signals(node_id)   # only signals with valid data
weight_sum = sum(w for _, _, w, _ in active)
fused = 0.0
for name, value, weight, _reliability in active:
    norm_weight = weight / weight_sum            # dynamic renormalization
    fused += norm_weight * value
fused = max(0.0, min(1.0, fused))                # clamp to [0, 1]
```

### 3.3 Architectural characteristics

- **Dynamic weight renormalization**: signals with no data (return None from `get_value()`) are excluded entirely. The remaining base weights are renormalized so they sum to 1.0. This is **not** the same as treating missing signals as zero.
- **Reliability is informational only (Phase 1)**: every Signal computes a reliability ∈ [0,1] which is recorded in `FusionResult.signal_details[i].reliability` (`mastery_fusion.py:78`), but it does **not** participate in the weighted sum (L103-114). Phase 2 may activate it via Beta-Bayesian or similar — that's an Open Question for ChatGPT.
- **Output clamped to [0, 1]**: defensive against upstream contract violations.

---

## 4. The Three Parallel Weighting Systems (the core A10 finding)

### System 1: `mastery_fusion.py` — node-level 5-signal fusion

- Input: 5 mastery signals
- Output: `fused_mastery: float ∈ [0, 1]`
- Intended consumers: verification service, recommendation service, UI display
- **Actual consumers**: a backend-wide grep for `compute_fused_mastery` returns **zero external call sites**. The function is loaded into a global singleton at startup (commit `3659e3c` "Fusion Engine 接入全局单例") but no service consumes it.

### System 2: `question_generator.py` — exam priority computation (bypasses System 1)

- Docstring formula at [`question_generator.py:114`](../../../backend/app/services/question_generator.py): `priority = W1*(1-p_mastery) + W2*(1-R) + W3*kg_relevance`
- Real implementation at lines 202-206:
  ```python
  priority = (
      W_MASTERY * (1.0 - p_mastery)
      + W_RETRIEVABILITY * (1.0 - retrievability)
      + W_KG_RELEVANCE * kg_relevance
  )
  ```
- Diverges from System 1: uses raw `p_mastery` (not `fused_mastery`), and introduces `kg_relevance` which System 1 has no concept of
- Why it bypasses: System 1 has no KG signal, so System 2 rolls its own to incorporate KG relevance into priority

### System 3: `recommendation_service.py` — recommendation ranking (bypasses System 1)

- Sort at [`recommendation_service.py:134`](../../../backend/app/services/recommendation_service.py): `filtered.sort(key=lambda c: c.confidence, reverse=True)`
- `confidence` source:
  - L1 text cosine similarity (lines 295-307, threshold ≥ 0.6)
  - L2 shared neighbor count (lines 208-218, formula `shared_neighbors / 3.0`)
- Diverges from System 1 completely: a grep for `mastery|p_mastery|fused_mastery` in `recommendation_service.py` returns **zero** matches
- CANVAS_EDGE in this file is only a *filter* (`L174-180 WHERE NOT (n)-[:CANVAS_EDGE]-()`), **not** the weighted edge (CANVAS_EDGE=1.0, RELATES_TO=0.7) that `algo-question/spec.md` defines

### Grep evidence of mutual ignorance

- `verification_service.py` grep `MasteryFusionEngine|SignalRegistry|NodePriority|compute_fused_mastery|fused_mastery` = **0 matches**
- `recommendation_service.py` grep same pattern + `mastery|p_mastery|kg_relevance` = **0 matches**
- `question_generator.py` references `p_mastery` but never `fused_mastery`

---

## 5. Implementation Status Matrix

| Fusion relationship | Theory / spec expectation | Code reality | Gap type | Evidence |
|---|---|---|---|---|
| BKT × FSRS × Exam × Calibration × Confidence | 5-signal weighted average | ✅ Implemented | None | `mastery_fusion.py:103-114` |
| KG relevance → fusion | Should be 6th signal (per `algo-question/spec.md`) | ❌ 0 references | Dead concept in System 1 | `signal_registry.py` grep `kg_relevance` = 0 |
| Verification ranking → fused_mastery | Priority queue ordered by mastery | ❌ Linear `idx++` | Bypass | `verification_service.py:932-945` |
| Recommendation sort → fused_mastery | Sort by mastery | ❌ Sort by text-similarity confidence | Bypass | `recommendation_service.py:134` |
| Reliability × weight | Beta-Bayesian or inverse-variance | ❌ Field is dead-code | Phase 2+ | `mastery_fusion.py:78` |

---

## 6. Indirect-related Existing Commits

A10 has **no dedicated fix commits** (verified by `git log --grep "A10"` across all history). The following commits touched the files involved in A10's analysis but did not address the decoupling itself:

| Commit | Title | A10 relevance |
|---|---|---|
| `3659e3c` | fix(S35): Phase 3 Step 4 — Fusion Engine 接入全局单例 | Loads `MasteryFusionEngine` as a startup singleton — but no service consumes it |
| `793cd53` | refactor(FR-KG-04): structlog + decision_tracker migration | Adds structured logging along the fusion path |
| `a6da4f7` | fix(kg-relevance): Phase 1 schema unification + weighted edge formula | A11 work — adds `kg_relevance` weighting to `question_generator`; **does not propagate to `mastery_fusion`** |
| `c363c3c` | test(fusion-strategy): add state-priority override regression tests | Tests for fusion strategy overrides |
| `2303b6b` | feat(agentic-rag): publish fusion_report / sharpness_report | RAG-layer "fusion" — a different concept from mastery fusion (same name, different domain) |

---

## 7. Suggested Future Phases (out of scope for this resolution)

These are NOT decided. They are listed so ChatGPT can evaluate ordering and risk:

- **Phase 1** — Register `kg_relevance` as the 6th signal in `signal_registry.py`. Lowest-risk first move because it eliminates "System 1 has no KG" as the root cause of System 2's existence.
- **Phase 2** — Change `verification_service._advance_concept()` to use `fused_mastery` ranking instead of linear `idx++`.
- **Phase 3** — Change `recommendation_service` to use `fused_mastery` as a multiplier on the confidence score (or as a primary sort key).
- **Phase 4** — Run an ablation experiment on the 5 signal weights (0.30/0.25/0.25/0.10/0.10) to validate or revise them.
- **Phase 5** — Activate Reliability via Beta-Bayesian weighting (academic anchors needed: Yudelson BKT 2013, FSRS-4.5 Open Spaced Repetition).

Each phase should become its own OpenSpec change after ChatGPT review.

---

## 8. The 7 Open Questions for ChatGPT Deep Research

These are the core review request. Please provide academic backing or empirical reasoning for each, and explicitly cite source line numbers from Section 9 in your answers.

1. **Weight calibration** — Are the base weights (BKT 0.30, FSRS 0.25, Exam 0.25, Calibration 0.10, Self-Confidence 0.10) supported by ablation studies or established mastery-modeling literature? Or are they ad-hoc? If the latter, what would a defensible baseline be?
2. **Dynamic renormalization bias** — When most signals are missing (the common case for new nodes), `mastery_fusion.py:103-107` redistributes weight to whichever signals remain. For a fresh node with only BKT, this means BKT effectively gets weight 1.0. Is this a bug (inflates BKT confidence on sparse data) or a feature (graceful degradation)?
3. **Architecture: converge or diverge?** — Three parallel weighting systems (`mastery_fusion`, `question_generator` priority, `recommendation_service` confidence) currently coexist. Should they converge into a single source of truth (`fused_mastery`)? Or is the separation a legitimate concern-separation pattern? Is there literature on "single fusion vs multiple specialized aggregators" in EdTech / mastery learning systems?
4. **Reliability activation path** — `signal_details[i].reliability` is computed but not used in fusion. What is the right way to activate it? Beta-Bayesian? Confidence-weighted average? Inverse-variance pooling? Reference papers preferred.
5. **KG relevance integration** — `kg_relevance` exists in `question_generator.py:202-206` but not in `signal_registry.py`. Should it become the 6th signal (with what base weight)? Or stay independent because "relevance to current task" is a different conceptual axis from "mastery"? Pros/cons of both approaches?
6. **Anti-pattern check on `_advance_concept`** — `verification_service.py:932-945` advances through `concept_queue` by `next_idx = current_idx + 1`. The queue order is determined upstream by `start_session` (L615-708) which does mastery-based filtering but not ranking. Is "linear queue traversal" an MVP simplification that should be replaced with `fused_mastery`-driven priority queue, or is there a legitimate UX reason for stable ordering (e.g., user expects sequential progression)?
7. **Explainability** — Is there learning-science research on how many concurrent mastery signals a learner can interpret in their dashboard? 5 signals may be cognitively overwhelming. Does the literature suggest collapsing to 2-3 user-facing dimensions?

---

## 9. Source Anchor Cheat Sheet (verified 2026-04-07 working tree)

> Line numbers may drift as code evolves. If a future reader finds a discrepancy, prefer the source over this document.

### Core fusion engine
- [`backend/app/services/signal_registry.py`](../../../backend/app/services/signal_registry.py) lines 27-77 (registry init), 105 (BKT 0.30), 140 (FSRS 0.25), 174 (Exam 0.25), 212 (Calibration 0.10), 249 (Confidence 0.10)
- [`backend/app/services/mastery_fusion.py`](../../../backend/app/services/mastery_fusion.py) lines 46-121 (`compute_fused_mastery` body), 78 (SignalDetail.reliability), 103-114 (dynamic renormalization), 114 (output clamp)

### Verification path (System 2 evidence)
- [`backend/app/services/verification_service.py`](../../../backend/app/services/verification_service.py) lines 615-708 (`start_session` mastery filter), 932-945 (`_advance_concept` linear `next_idx = current + 1`), 1712-1790 (`_get_difficulty_for_concept` — affects difficulty not order)

### Recommendation path (System 3 evidence)
- [`backend/app/services/recommendation_service.py`](../../../backend/app/services/recommendation_service.py) lines 53-84 (`generate_recommendations` entry), 134 (`sort by confidence`), 174-180 (CANVAS_EDGE filter not weight), 208-218 (shared-neighbor confidence), 295-307 (text cosine confidence)

### Question Generator (System 2 formula)
- [`backend/app/services/question_generator.py`](../../../backend/app/services/question_generator.py) line 114 (docstring formula), lines 202-206 (real implementation `W_MASTERY` / `W_RETRIEVABILITY` / `W_KG_RELEVANCE`)

### Field definitions
- [`backend/app/models/exam_models.py`](../../../backend/app/models/exam_models.py) lines 224, 258 (`kg_relevance` field)

### Frontend entry (for completeness — not modified)
- [`frontend/src/hooks/useRecommendations.ts`](../../../frontend/src/hooks/useRecommendations.ts) line 102 (frontend call site)
- [`frontend/src/services/api-client.ts`](../../../frontend/src/services/api-client.ts) lines 895-903 (`POST /api/v1/canvas/{id}/recommendations`)
- [`backend/app/api/v1/endpoints/canvas.py`](../../../backend/app/api/v1/endpoints/canvas.py) lines 422-459 (backend endpoint)

### Existing OpenSpec specs (related but unmodified)
- [`openspec/specs/algo-question/spec.md`](../../../openspec/specs/algo-question/spec.md) — KG relevance CANVAS_EDGE / RELATES_TO weighting formula (System 2's contractual home)
- [`openspec/specs/algo-scoring/spec.md`](../../../openspec/specs/algo-scoring/spec.md) — LEARNED.score + review_count consistency
- [`openspec/specs/verification-service/spec.md`](../../../openspec/specs/verification-service/spec.md) — Fail-Closed Degraded Scoring (adjacent, unrelated)
- [`openspec/specs/canvas-recommendations/spec.md`](../../../openspec/specs/canvas-recommendations/spec.md) — Recommendation toggle / debouncing (adjacent, unrelated)

### OpenSpec resolution artifacts (archived 2026-04-07)
- [`openspec/specs/algo-fusion/spec.md`](../../../openspec/specs/algo-fusion/spec.md) — **canonical** location of the 4 formalized requirements (merged via `npx openspec archive`)
- [`openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/proposal.md`](../../../openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/proposal.md) — historical proposal
- [`openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/design.md`](../../../openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/design.md) — formal twin of this document with full architecture analysis
- [`openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/specs/algo-fusion/spec.md`](../../../openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/specs/algo-fusion/spec.md) — original ADDED Requirements delta (pre-merge)
- [`openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/tasks.md`](../../../openspec/changes/archive/2026-04-07-a10-fsrs-fusion-formalization/tasks.md) — historical task list

### The original question
- [`docs/project-status/fr-exploration/A10.md`](A10.md) — preserved untouched, 88 lines

---

## 10. Known Limitations of This Document

- Source line numbers were verified by 6 sed samplings on 2026-04-07. The remaining file regions (e.g., `verification_service.py:1712-1790`) were not exhaustively re-scanned and may drift more easily as those areas are rarely touched.
- The "fix path" in Section 7 has not been validated by any code spike — it is a brainstormed sequence, not an architectural recommendation.
- The question of whether the three parallel systems should converge or stay separated is open by design — see Section 8 question 3.
- The Reliability Phase 2 activation strategy needs literature backing that this document does not provide.

---

## 11. Out of Scope for This Resolution

- ❌ Any code changes to `mastery_fusion.py`, `verification_service.py`, `recommendation_service.py`, or `question_generator.py`
- ❌ Modifying the original [`A10.md`](A10.md) (88 lines preserved)
- ❌ Filling the empty `algo-mastery/` capability stub (a separate concern)
- ❌ Running the 5-signal weight ablation experiment (Phase 4)
- ❌ Activating Reliability via Beta-Bayesian (Phase 5)
- ❌ Implementing the 5 future phases listed in Section 7 (those become follow-up OpenSpec changes after ChatGPT review)

> Note: The OpenSpec change `a10-fsrs-fusion-formalization` was **archived on 2026-04-07** so the formalized requirements could be tracked in `openspec/specs/algo-fusion/spec.md`. This contradicts an earlier draft of the plan that said "do not archive yet" — the contradiction was resolved by user decision after discovering that `openspec/changes/*/` is gitignored, which would have made the change invisible to ChatGPT review. Archiving was the only path that produced a tracked, GitHub-visible artifact while preserving the spec-driven workflow.

---

## 12. Discovered During ChatGPT Review (2026-04-07)

ChatGPT Deep Research reviewed this document and the associated `a10-fsrs-fusion-formalization` change. Two corrections emerged from that review and were addressed by the follow-up Phase 0 change `a10-phase0-fix-question-generator-mastery-bug`.

### 12.1 Correction: "compute_fused_mastery zero call sites" was wrong

Section 4 ("Three Parallel Weighting Systems") originally claimed that a backend-wide grep for `compute_fused_mastery` returns zero external call sites. ChatGPT used the GitHub connector to read the actual codebase and corrected this:

- **`mastery_engine.py:347-355`** — `effective_proficiency()` calls `compute_fused_mastery(concept_id)` and uses the fused result as `base` (Story 5.6 multi-signal fusion path)
- **`mastery_engine.py:563-567`** — `concept_to_response()` calls `compute_fused_mastery` and includes `fused_mastery` in the API response payload
- **`backend/app/main.py:220-261`** — startup wires the fusion engine into a global `MasteryEngine` singleton via `set_fusion_engine`

The corrected statement is: **`compute_fused_mastery` IS consumed by `mastery_engine.effective_proficiency()`. The decoupling is that `verification_service`, `recommendation_service`, and `question_generator` do not call `effective_proficiency()` either** — so the fusion result still does not reach the three downstream business paths.

The "three parallel weighting systems" finding remains correct; it was just one layer deeper than originally diagnosed.

### 12.2 Deeper finding: question_generator silent bug (fixed by Phase 0)

Following ChatGPT's correction, deeper exploration of `question_generator.py` revealed a **silent production bug**:

- `question_generator._get_mastery_data` (lines 673-698 pre-fix) used `getattr(concept, "effective_proficiency", 0.0)` and similar `getattr` calls for `mastery_level`, `mastery_label`, and `retrievability`
- `ConceptState` (`mastery_state.py:74`) explicitly states: "Volatile values (retrievability, effective_proficiency) are computed on read and never stored"
- A backend-wide grep for `concept\.effective_proficiency\s*=` finds no setters anywhere
- Therefore the `getattr(... 0.0)` calls **always returned the default** — every exam question was silently classified as `"easy"` difficulty (because `0.0 < 0.3`), and the Gemini prompt always told the LLM the learner had zero mastery for every concept

The fix in Phase 0:
- `question_generator._get_mastery_data` now imports `get_mastery_engine` lazily and calls `engine.effective_proficiency(concept)`, `engine.mastery_level(concept)`, `engine.mastery_label(concept)`, `engine.get_retrievability(concept)`
- The existing `MasteryEngine.get_retrievability(concept)` public method (lines 301-307) is reused (no new wrapper needed — the Phase 0 plan initially assumed one had to be added)
- A new regression test file `backend/tests/unit/test_question_generator_mastery_data.py` covers 5 scenarios including a static-grep guard against the broken `getattr` pattern reappearing

### 12.3 Phase 0 change reference

- **OpenSpec change**: `a10-phase0-fix-question-generator-mastery-bug` (archived after this Phase 0 commit)
- **New `algo-question` Requirement**: "Mastery Data Flows Through MasteryEngine" — codifies that volatile mastery fields MUST be read via `MasteryEngine` instance methods, not via `getattr` on `ConceptState`
- **Files changed**: `backend/app/services/question_generator.py` (the fix), `backend/tests/unit/test_question_generator_mastery_data.py` (new), `backend/tests/e2e/test_a11_kg_relevance_e2e.py` (clarifying comment on the intentional stub), `openspec/specs/algo-question/spec.md` (merged Requirement), `openspec/specs/algo-fusion/spec.md` (Purpose updated)
- **Out of scope**: ChatGPT's other 5 architectural recommendations (ReviewPriorityEngine, advance_strategy, recommendation mastery factor, reliability weighting, ablation harness) — those become Phase 1+ changes after the user reviews ChatGPT's full response

---

## 13. Phase 0 Hardening (2026-04-07)

Following ChatGPT Deep Research's **second-round adversarial review** of the Phase 0 fix itself, a follow-up OpenSpec change `a10-phase0-hardening` was executed in the same session to close three residual risks that the original Phase 0 did not cover.

### 13.1 Four hardenings applied

| # | Risk identified by review | Hardening applied |
|---|---|---|
| **1** | Phase 0 silently fails when `mastery_store.get_concept` returns None (ID mapping drift or unprocessed score events) — fallback dict is indistinguishable from the pre-fix bug | Added `mastery_degraded: Optional[str]` key to `_get_mastery_data` return dict with values `None` / `"concept_not_found"` / `"exception"`. Propagated to `ACPData.mastery_degraded` and `NodePriority.mastery_degraded` (mirroring the existing `kg_relevance_degraded` pattern). |
| **2** | `effective_proficiency` was called **3×** per node (direct + via `mastery_level` internal + via `mastery_label → mastery_level` recursion) | Added public helpers `MasteryEngine.mastery_level_from_proficiency(eff, concept)` and `mastery_label_from_level(level)` that accept pre-computed values. Refactored `_get_mastery_data` to compute eff exactly once. 50-node batch drops from 150 → 50 fusion computations (3× reduction). |
| **3** | `_get_kg_relevance` MATCH only bound primary node to `id` (not `canvasId`), leaving a forward-looking cross-canvas contamination path | Tightened Cypher `MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})` — dual binding eliminates the risk even if per-canvas node_id namespaces are later introduced. |
| **4** | `select_target_node` batch `asyncio.gather` had no concurrency cap → 1000+ simultaneous Neo4j queries on a 500-node canvas | Added function-local `asyncio.Semaphore(20)` wrapping each per-node coroutine (mirrors `canvas_service.py:598-616` pattern). |

### 13.2 Spec deltas merged to `algo-question`

- **NEW Requirement**: "Mastery Data Degraded Observability" (4 scenarios)
- **NEW Requirement**: "Effective Proficiency Computed Once Per Mastery Query" (2 scenarios)
- **NEW Requirement**: "Bounded Concurrency for Batch Node Scoring" (2 scenarios)
- **MODIFIED Requirement**: "kg_relevance Schema Correctness" — added "Primary node is bound to canvasId" + "Cypher syntax check" scenarios

### 13.3 Test coverage expansion

- Existing Phase 0 regression suite: 8 scenarios (unchanged semantics, updated to match new API)
- New Phase 0 Hardening unit scenarios: 5 (1x eff call count, concept_not_found marker, exception marker, mastery_level_from_proficiency equivalence, mastery_label_from_level equivalence)
- New Phase 0 Hardening e2e scenarios: 2 (cross-canvas isolation, bounded concurrency instrumentation)
- Total A10 guard surface: **13 unit + 13 e2e = 26 tests**

### 13.4 Phase 0 Hardening change reference

- **OpenSpec change**: `a10-phase0-hardening` (archived in the same commit)
- **Files changed**: `backend/app/services/question_generator.py`, `backend/app/services/mastery_engine.py`, `backend/app/models/exam_models.py`, `backend/tests/unit/test_question_generator_mastery_data.py`, `backend/tests/e2e/test_a11_kg_relevance_e2e.py`, `openspec/specs/algo-question/spec.md` (Requirements merged via archive)

### 13.5 Self-reinforcing discovery in the test suite

While writing the cross-canvas isolation test, the test setup itself reproduced the exact bug the production fix was guarding against: a `MERGE (n:CanvasNode {id: 'nodeE'}) ... ON MATCH SET canvasId=$parallel` clause stole the original canvas's nodeE into the parallel canvas. The fix in both test and production is the same — bind both `id` and `canvasId` in the MERGE/MATCH. This is documented here because it demonstrates why the ChatGPT review was correct to flag the forward-looking risk: the footgun is easy to step on.

---

## How to use this document with ChatGPT Deep Research

1. Copy this entire file (≈ 20 KB after Phase 0 Hardening update) into ChatGPT Deep Research as the primary input.
2. Tell ChatGPT it has access to the GitHub repo (provide the repo URL), so it can resolve the relative source links in Section 9.
3. Direct ChatGPT to focus on the 7 questions in Section 8.
4. Expect 1-3 rounds of clarifying questions before ChatGPT produces a `[FINAL]` recommendation per question.
5. When ChatGPT responds, the next session can convert the answers into follow-up OpenSpec changes (one per Phase).
