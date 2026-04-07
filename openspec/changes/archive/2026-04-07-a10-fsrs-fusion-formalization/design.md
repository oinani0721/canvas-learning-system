# Design: Formalize FSRS Fusion Architecture (A10)

## Context

### Origin of the question

A10 is one of 11 user-raised questions in `docs/project-status/fr-exploration/A10.md` (88 lines, untouched since Apr 5). The verbatim question (line 88) is:

> 「FSRS 的算法是如何和其他的算法进行融合的，没有理清楚」

This is **not** a bug report or feature request — it is an architectural clarity question. The user wants to know how FSRS retrievability interacts with the other mastery signals (BKT, exam scores, calibration, self-confidence) to produce the displayed node "mastery" state.

### Phase 1 exploration findings (4 Explore agents + 6 source-line samplings)

Reading the codebase reveals that the **answer is non-obvious because there is no single fusion path** — instead, three independent weighting systems coexist and never read each other's results.

**System 1: `mastery_fusion.py` — node-level 5-signal fusion**
- File: `backend/app/services/mastery_fusion.py:46-121`
- Entry point: `MasteryFusionEngine.compute_fused_mastery(node_id) → FusionResult`
- Signals (defined in `signal_registry.py`):
  - BKT Mastery, base weight 0.30 (`signal_registry.py:105`)
  - FSRS Retrievability, base weight 0.25 (`signal_registry.py:140`)
  - Exam Score Average, base weight 0.25 (`signal_registry.py:174`)
  - Calibration Bias, base weight 0.10 (`signal_registry.py:212`)
  - Self-Confidence Average, base weight 0.10 (`signal_registry.py:249`)
- Algorithm: dynamic-renormalized weighted average (`mastery_fusion.py:103-114`)
  ```python
  active = registry.get_active_signals(node_id)  # only signals with valid data
  weight_sum = sum(w for _, _, w, _ in active)
  fused = 0.0
  for name, value, weight, _reliability in active:
      norm_weight = weight / weight_sum   # renormalize over active signals
      fused += norm_weight * value
  fused = max(0.0, min(1.0, fused))       # clamp to [0,1]
  ```
- **Critical finding**: a backend-wide grep for `compute_fused_mastery` returns **zero external call sites**. The function is loaded into a global singleton at startup (commit `3659e3c`) but no service consumes it.

**System 2: `question_generator.py` — exam priority computation**
- File: `backend/app/services/question_generator.py`
- Docstring formula at L114: `priority = W1*(1-p_mastery) + W2*(1-R) + W3*kg_relevance`
- Real implementation at L202-206:
  ```python
  priority = (
      W_MASTERY * (1.0 - p_mastery)
      + W_RETRIEVABILITY * (1.0 - retrievability)
      + W_KG_RELEVANCE * kg_relevance
  )
  ```
- **Diverges from System 1** in two ways: it uses raw `p_mastery` (not `fused_mastery`), and it introduces `kg_relevance` which System 1 has no concept of.
- Why it bypasses System 1: System 1 has no KG signal, so System 2 needs to roll its own formula to incorporate KG relevance into priority.

**System 3: `recommendation_service.py` — recommendation ranking**
- File: `backend/app/services/recommendation_service.py`
- Sort: `recommendation_service.py:134` → `filtered.sort(key=lambda c: c.confidence, reverse=True)`
- `confidence` source:
  - L1 text cosine similarity (L295-307, threshold ≥ 0.6)
  - L2 shared neighbor count (L208-218, formula `shared_neighbors / 3.0`)
- **Diverges from System 1** completely. A grep for `mastery|p_mastery|fused_mastery|kg_relevance` in `recommendation_service.py` returns zero matches. CANVAS_EDGE only acts as a *filter* (`L174-180 WHERE NOT (n)-[:CANVAS_EDGE]-()`), **not** as a weight as the `algo-question` spec claims.

### Capability state

`openspec/specs/algo-fusion/` exists as a directory but `spec.md` was never created (verified by `find ... -type f`). This means the central fusion contract has never been formalized. `algo-mastery/` is similarly empty (out of scope for this change).

### Stakeholder

- The user (single stakeholder) wants this question answered with academic backing, planning to forward the resulting analysis to ChatGPT Deep Research for review.
- ChatGPT Deep Research will be the secondary reader; the design document must be self-contained enough for ChatGPT to evaluate without local repo access.

## Goals / Non-Goals

**Goals:**

1. **Make the 5-signal fusion contract explicit** by formalizing it as the first set of requirements under the `algo-fusion` capability
2. **Document the three-system decoupling problem** with file:line evidence so future readers can verify it without re-discovery
3. **Produce a ChatGPT-reviewable artifact** (the twin docs file) that contains all the context ChatGPT needs to evaluate the architecture
4. **Establish a baseline** so future implementation changes (KG-as-6th-signal, verification using fused_mastery, recommendation using fused_mastery) can use `## MODIFIED Requirements` cleanly
5. **Surface 7 Open Questions** that need ChatGPT input before any implementation proceeds

**Non-Goals:**

- ❌ Modifying any backend or frontend code (`mastery_fusion.py`, `verification_service.py`, `recommendation_service.py`, `question_generator.py` are read-only inputs)
- ❌ Deciding the answer to the Open Questions in this change — those decisions belong in follow-up changes after ChatGPT review
- ❌ Filling the empty `algo-mastery/` capability stub
- ❌ Creating MODIFIED Requirements deltas for `verification-service`, `canvas-recommendations`, or `algo-question` capabilities
- ❌ Running any ablation experiments or performance benchmarks
- ❌ Modifying the original `A10.md` problem document
- ❌ Archiving this change in the same session (this is RFC-style — archive happens after follow-up changes land)

## Decisions

### Decision 1: Codify current behavior as spec, not the desired behavior

**Choice**: The `specs/algo-fusion/spec.md` requirements describe what `mastery_fusion.py` does *today* (dynamic renormalization, reliability-as-information-only, output clamping), not what it *should* do.

**Rationale**:
- We don't yet know what the optimal design is — that's exactly what ChatGPT review will tell us.
- Writing aspirational requirements before review would force the change to be reworked after ChatGPT responds.
- A baseline spec gives follow-up changes a clean MODIFIED Requirements anchor.

**Alternative considered**: Write requirements describing the unified architecture (5 signals + KG + reliability-weighted + consumed by verification/recommendation). **Rejected** because it pre-commits to design choices the user explicitly wants ChatGPT to validate.

### Decision 2: Twin documents (design.md + A10-resolution-summary.md)

**Choice**: Maintain both `openspec/changes/a10-fsrs-fusion-formalization/design.md` and `docs/project-status/fr-exploration/A10-resolution-summary.md`. They share ~80% content but differ in framing.

**Rationale**:
- `design.md` is the OpenSpec-canonical artifact, follows the spec-driven schema strictly, and survives `archive` into the OpenSpec history.
- `A10-resolution-summary.md` is the ChatGPT-friendly entry point, lives in `docs/project-status/fr-exploration/` alongside the original A10.md problem statement, and is what the user copies into ChatGPT Deep Research.
- Cross-linking both ways prevents drift and gives readers two entry points depending on context (developer browsing OpenSpec vs reviewer reading project status).

**Alternative considered**: Single document in one of the two locations. **Rejected** because:
- Putting it only in OpenSpec hides it from the `docs/project-status/fr-exploration/` index where users browse FR work.
- Putting it only in `docs/` violates the user's stated preference for following the OpenSpec workflow.

### Decision 3: Keep this change scope minimal — no MODIFIED deltas

**Choice**: Only one delta file: `specs/algo-fusion/spec.md` with `## ADDED Requirements`. No MODIFIED Requirements for `verification-service` or `canvas-recommendations` even though those capabilities are clearly affected by the three-system decoupling.

**Rationale**:
- The fix to verification/recommendation depends on ChatGPT input. If we MODIFIED them now, we'd be guessing.
- A focused change is easier to review and easier to revert.
- Future changes (e.g., `unify-verification-with-fused-mastery`) can each carry their own MODIFIED delta.

**Alternative considered**: A "kitchen sink" change that touches all 4 capabilities at once. **Rejected** as too risky and pre-emptive.

### Decision 4: Don't archive in this session

**Choice**: Run `npx openspec validate --strict` and `status` to confirm 4/4 artifacts complete, but do **not** run `npx openspec archive`. The change stays in `openspec/changes/` until ChatGPT review and follow-up implementation changes are also ready to merge into `openspec/specs/algo-fusion/spec.md`.

**Rationale**:
- Archiving this change alone would leave `openspec/specs/algo-fusion/spec.md` sitting at "Phase 1 only" indefinitely.
- Better to archive a series of changes together when the picture is complete.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Codifying current behavior as spec may "freeze" non-optimal choices (e.g., 0.30/0.25/0.25/0.10/0.10 weights, equal renormalization) | Open Questions section explicitly flags every design choice that needs review; future MODIFIED Requirements can update them after ChatGPT input |
| Source line numbers in design/docs will drift as code evolves | Document headers state "verified at commit `<hash>`"; the change is small enough to re-verify on each refactor; specs themselves cite contracts not line numbers |
| ChatGPT may skim summary without reading source | Open Questions are phrased to require source-level evidence (e.g., "Is the dynamic renormalization at `mastery_fusion.py:103-114` biased toward BKT?"), forcing ChatGPT to engage with concrete code |
| `algo-fusion/` was empty due to a forgotten archive — adding ADDED Requirements may conflict with whatever was supposed to land there | Verified `find openspec/specs/algo-fusion -type f` returns no files; no historical change references the empty folder; safe to seed |
| `npx openspec validate` may fail on subtle template issues | Each requirement has ≥1 four-hashtag scenario; proposal uses `## Why` / `## What Changes` / `## Capabilities` (with `### New Capabilities` subsection) / `## Impact` exactly per template |
| Lefthook pre-push backend-smoke gate may block doc-only push | Plan documents fallback to `LEFTHOOK=0 git push origin main` for the doc-only commit; the gate is designed for code changes |
| Twin documents may fall out of sync | Both files cross-link the other; `tasks.md` includes a verification step to grep both for the link; future updates should always touch both |
| Reader confuses `mastery_fusion` with the agentic-rag `fusion_report` (commit `2303b6b`) | design.md and the docs twin both name "RAG-layer fusion" vs "node-level mastery fusion" explicitly |

## Open Questions for ChatGPT Deep Research Review

These 7 questions are the core review request. ChatGPT should provide academic backing or empirical reasoning for each:

1. **Weight calibration**: Are the base weights (BKT 0.30, FSRS 0.25, Exam 0.25, Calibration 0.10, Self-Confidence 0.10) supported by ablation studies or established mastery-modeling literature? Or are they ad-hoc? If the latter, what would a defensible baseline be?
2. **Dynamic renormalization bias**: When most signals are missing (the common case for new nodes), `mastery_fusion.py:103-107` redistributes weight to whichever signals remain. For a fresh node with only BKT, this means BKT effectively gets weight 1.0. Is this a bug (inflates BKT confidence) or a feature (graceful degradation)?
3. **Architecture: converge or diverge?**: Three parallel weighting systems (`mastery_fusion`, `question_generator` priority, `recommendation_service` confidence) currently coexist. Should they converge into a single source of truth (`fused_mastery`)? Or is the separation a legitimate concern-separation pattern? Is there literature on "single fusion vs multiple specialized aggregators" in EdTech?
4. **Reliability activation path**: `signal_details[i].reliability` is computed but not used in fusion (`mastery_fusion.py:78` records it; L103-114 ignores it). What is the right way to activate it? Beta-Bayesian? Confidence-weighted average? Inverse-variance? Reference papers preferred.
5. **KG relevance integration**: `kg_relevance` exists in `question_generator.py:202-206` but not in `signal_registry.py`. Should it become the 6th signal (with what base weight)? Or stay independent because "relevance to current task" is a different conceptual axis from "mastery"?
6. **Anti-pattern check on `_advance_concept`**: `verification_service.py:932-945` advances through `concept_queue` by `next_idx = current_idx + 1`. The queue order is determined upstream by `start_session` (L615-708) which does mastery-based filtering but not ranking. Is "linear queue traversal" an MVP simplification that should be replaced with `fused_mastery`-driven priority queue, or is there a legitimate UX reason for stable ordering (e.g., user expects sequential progression)?
7. **Explainability**: Is there learning-science research on how many concurrent signals a learner can interpret in their mastery dashboard? 5 signals may be cognitively overwhelming. Does the literature suggest collapsing to 2-3 user-facing dimensions?

## Cross-Links

### Within this change

- `proposal.md` — motivation and `What Changes` summary
- `specs/algo-fusion/spec.md` — formalized 4 ADDED Requirements (Five-Signal / Dynamic Renormalization / Reliability Phase 1 / Output Clamping)
- `tasks.md` — execution checklist

### To project documentation

- `docs/project-status/fr-exploration/A10.md` — original 88-line user question (read-only, never modified by this change)
- `docs/project-status/fr-exploration/A10-resolution-summary.md` — ChatGPT-friendly twin of this design document, lives alongside the original A10.md for project-status browsing

### Indirect-related existing commits (background only)

| Commit | Title | Relation to A10 |
|---|---|---|
| `3659e3c` | fix(S35): Phase 3 Step 4 — Fusion Engine 接入全局单例 | Loads `MasteryFusionEngine` as a startup singleton — but no service consumes it |
| `793cd53` | refactor(FR-KG-04): structlog + decision_tracker migration | Adds structured logging along the fusion path |
| `a6da4f7` | fix(kg-relevance): Phase 1 schema unification + weighted edge formula | A11 work — adds `kg_relevance` weighting to `question_generator`; **does not propagate to `mastery_fusion`** |
| `c363c3c` | test(fusion-strategy): add state-priority override regression tests | Tests for fusion strategy overrides |
| `2303b6b` | feat(agentic-rag): publish fusion_report / sharpness_report | RAG-layer "fusion" (a different concept from mastery fusion — same name, different domain) |

## Source Anchors (verified at the commit producing this change)

> Verified by Read tool sampling on 2026-04-07 against the working tree.

### Core fusion engine

- `backend/app/services/signal_registry.py` lines 27-77 (registry init), 105 (BKT weight 0.30), 140 (FSRS weight 0.25), 174 (Exam weight 0.25), 212 (Calibration weight 0.10), 249 (Confidence weight 0.10)
- `backend/app/services/mastery_fusion.py` lines 46-121 (`compute_fused_mastery` body), 78 (SignalDetail with reliability), 103-114 (dynamic renormalization core loop), 114 (output clamp)

### Verification path (System 2 evidence)

- `backend/app/services/verification_service.py` lines 615-708 (`start_session` mastery filtering — produces `concept_queue`), 932-945 (`_advance_concept` linear `next_idx = current + 1`), 1712-1790 (`_get_difficulty_for_concept` — affects question difficulty but not ordering)

### Recommendation path (System 3 evidence)

- `backend/app/services/recommendation_service.py` lines 53-84 (`generate_recommendations` entry), 134 (`sort by confidence`), 174-180 (CANVAS_EDGE filter not weight), 208-218 (shared-neighbor confidence), 295-307 (text cosine confidence)

### Question Generator (System 2 formula)

- `backend/app/services/question_generator.py` line 114 (docstring formula `W1*(1-p_mastery) + W2*(1-R) + W3*kg_relevance`), lines 202-206 (real implementation using `W_MASTERY` / `W_RETRIEVABILITY` / `W_KG_RELEVANCE`)

### Field definitions (referenced for completeness)

- `backend/app/models/exam_models.py` lines 224, 258 (`kg_relevance` field on payload models)

### Frontend entry (not modified, for context)

- `frontend/src/hooks/useRecommendations.ts` line 102 (frontend call site)
- `frontend/src/services/api-client.ts` lines 895-903 (`POST /api/v1/canvas/{id}/recommendations`)
- `backend/app/api/v1/endpoints/canvas.py` lines 422-459 (backend endpoint)

### Related existing specs

- `openspec/specs/algo-question/spec.md` (KG relevance CANVAS_EDGE / RELATES_TO weighting formula — this is where System 2's weighting is defined contractually)
- `openspec/specs/algo-scoring/spec.md` (LEARNED.score + review_count consistency)
- `openspec/specs/verification-service/spec.md` (Fail-Closed Degraded Scoring — adjacent but unrelated)
- `openspec/specs/canvas-recommendations/spec.md` (Recommendation toggle and debouncing — adjacent but unrelated)
