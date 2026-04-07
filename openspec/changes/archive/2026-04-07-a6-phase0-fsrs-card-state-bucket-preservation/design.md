## Context

Five parallel Explore agents verified A6 resolution status against the ChatGPT Deep Research review report. The verdict distribution was:

| Source | Claim | Verdict | Evidence |
|---|---|---|---|
| ChatGPT P1 | `_save_card_states` drops `_legacy_card_states` | **TRUE / P0** (this change) | `review_service.py:406` serializes only `self._card_states`; fixture `backend/data/fsrs_card_states.json` already contains 1 legacy key (`"node123"`) |
| ChatGPT P1 | Neo4j missing `canvasnode_id_unique` constraint | **FALSE alarm** | `backend/migrations/neo4j/001_canvas_constraints.cypher:22-23` already defines the constraint |
| ChatGPT P1 | LLM Router missing schema validation | **FALSE alarm** | `llm_router.py:49-51` has `ALLOWED_INTENTS` frozenset; `:257` enforces it strictly |
| ChatGPT P2 | Missing pip-audit / SBOM | **FALSE alarm** | `.github/workflows/test.yml:71-85` has `security` job running pip-audit |
| ChatGPT P3 | CORS mis-config | **FALSE alarm** | Tauri desktop + strict origin allowlist + `X-CLS-Internal-Key` auth on write ops |
| ChatGPT P2 | Missing RAGAS-style Faithfulness CI gate | **VALID P2** (Deferred) | Custom faithfulness impl in `agentic_rag.faithfulness_check` exists but no CI gate wired |
| Agent 1+2 | `RELATES_TO` write path has **zero callers** in `backend/app/` | **TRUE / P0** (Deferred) | `graphiti_client.add_relationship()` defined in lib; backend has zero callers → Q1 加权融合公式 `_get_kg_relevance()` 永远只命中 CANVAS_EDGE |
| Agent 1+2 | `fsrs_difficulty` field is computed but never consumed | **TRUE / P0** (Deferred) | `mastery_engine.py:292` assigns the field; `question_generator.py:202-206` priority formula only uses `p_mastery + retrievability + kg_relevance` → A6's claimed "难度分层 ≥80 / 60-79 / <60" is documentation-only |
| Agent 1+2 | Frontend `onConnect` → `/api/v1/sync/batch` call missing | **TRUE / P0** (Deferred) | Backend `sync_service._upsert_edge()` + `/api/v1/sync/batch` complete; frontend has zero POST to that endpoint → user drawing an edge in the Canvas is invisible to the backend |

A6.md 三问的真实解决度 ≈ **30%** (4 个 P0 中 0 个被先前的 "修复" 实际解决；只有 ChatGPT review 本身触发了 1 个 P0 的发现)。The remaining 3 P0s are deliberately deferred (see §Deferred below) so that this phase 0 can ship a **minimal, maximally-reversible, single-commit** fix for the most immediately dangerous failure mode (silent data loss on save).

**Constraints**:
- Must land **before** the main worktree change `fix-concept-id-identity-unification` merges to `origin/main` (otherwise the window between that merge and this phase 0 merge exposes users to silent data loss).
- Must not touch the load-path or lookup-path code — those are already covered by the sibling "Card State Load Is Backward Compatible" requirement and have passing tests.
- Must not introduce any new file I/O, lock, or schema change — the whole value of a phase 0 fix is that it's a single-commit, easily-reverted, low-risk correction.

## Goals / Non-Goals

**Goals:**
- Eliminate the silent legacy-bucket data loss **before** merging the `fix-concept-id-identity-unification` worktree to main.
- Codify the invariant as a spec contract under `concept-identity` capability so that future regressions are caught by `npx openspec validate --strict` (via the requirement's presence in `openspec/specs/concept-identity/spec.md` after archive).
- Establish a round-trip test pattern that future bucket-split persistence code can copy-paste.

**Non-Goals:**
- Migrating legacy text keys to UUID — out of scope; requires a separate user decision about whether to attempt in-place canonicalization (needs canvas-name resolution, Graphiti lookup) or defer until a future UI-driven migration wizard.
- Exporting the legacy bucket to a sidecar file `fsrs_card_states_legacy.json` — this was the ChatGPT case-B alternative and is rejected in D1 below.
- Touching the `ConceptRef` `concept_name` path-shape guard — the current guard only rejects names starting with `/` (POSIX paths). Windows paths (`C:\`), URLs (`http(s)://`), and backslash-separated paths are not rejected. This is a separate hardening change tracked in Deferred §4.
- Fixing the 3 deeper P0s discovered during verification (RELATES_TO write path, fsrs_difficulty integration, frontend edge sync). These each deserve their own OpenSpec change and user-facing scope decision.

## Decisions

### D1: Fix strategy — Merge both buckets in serialization

**Choice**: In `_save_card_states`, build `combined = {**self._legacy_card_states, **self._card_states}` inside the existing `async with _card_states_lock:` block and `json.dumps(combined, ...)` instead of `self._card_states`.

**Rationale**:
- **Minimal change**: 1-line payload change + 1-line log update. Total diff ≈ 5 lines including the new intermediate `combined` variable.
- **Zero data loss by construction**: `_load_card_states` uses `is_uuid_v4(key)` to partition keys into the two buckets (`concept_identity.py:is_uuid_v4`). The key spaces are therefore provably disjoint, so `{**legacy, **uuid}` cannot drop entries.
- **Defensive key-collision semantics**: On the (impossible by construction) chance that a key exists in both buckets, the UUID bucket value wins because of Python dict-merge order (right side overrides left). This is the safe choice because the UUID bucket is the authoritative post-migration source.
- **Zero new I/O**: no second file, no second lock, no atomic-write coordination, no recovery semantics if two files get out of sync. The existing temp-file-rename atomic write continues to protect the single file.
- **Trivial rollback**: `git revert <commit>` is an unambiguous 5-line revert. No schema/API breakage to roll back.

**Alternative considered (rejected)**: ChatGPT case-B suggested exporting the legacy bucket to `backend/data/fsrs_card_states_legacy.json` as an ops audit artifact. Reasons rejected:
- Adds a second file path, a second lock, and atomic-write coordination between two files.
- Introduces recovery semantics: what happens if the legacy file is missing on restart? What if the two files get out of sync?
- No actual data preservation benefit — D1's merged-bucket approach already preserves.
- Ops-audit value is better served by a structured log line (which D1 already adds via `len(combined)`).

### D2: Test file location — New file vs extend existing

**Choice**: Create a new file `backend/tests/unit/test_review_service_legacy_bucket_round_trip.py` rather than extending `test_card_states_compat_read.py`.

**Rationale**:
- **Test isolation**: round-trip tests need a non-trivial fixture setup (write a mixed-key JSON file to `tmp_path`, monkey-patch `_CARD_STATES_FILE`, instantiate `ReviewService`, exercise save, re-read). Mixing this with the existing compat-read tests would muddy the setup.
- **Naming clarity**: a file named `test_review_service_legacy_bucket_round_trip.py` is immediately discoverable by anyone investigating a future legacy-bucket regression via `grep -l legacy_bucket backend/tests/`.
- **Distinct concerns**: `test_card_states_compat_read.py` tests the read-side lookup chain (`_get_card_state` fall-through to `_legacy_card_states`). The new file tests the write-side preservation — a different contract.

**Alternative considered (rejected)**: Extend `test_card_states_compat_read.py` with a new class `TestRoundTrip`. Rejected because it would mix two distinct contracts into one file and make it harder to delete one contract's tests if the feature is later replaced.

### D3: Archive order independence vs main worktree change

**Choice**: This phase 0 change can be archived before, after, or in parallel with `fix-concept-id-identity-unification`.

**Rationale**:
- OpenSpec's `npx openspec archive` performs **append-only delta merge** against the main spec file at `openspec/specs/<capability>/spec.md`.
- Both changes target the same `concept-identity` capability, but each ADDs different Requirement names (no MODIFIED collisions — this phase 0 never modifies any existing Requirement). The two changes add to disjoint Requirement sets.
- Whichever archives first creates `openspec/specs/concept-identity/spec.md` from its delta; the second archive appends its Requirement(s) to the existing file.
- The Requirement name `FSRS Card State Legacy Bucket Preservation On Save` is distinct from all 7 Requirement names in the current worktree delta (verified by reading `.worktrees/fix-concept-id-identity-unification/openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md`).

## Risks / Trade-offs

- **[Risk]** The worktree branch `fix-concept-id-identity-unification` may evolve and introduce a new Requirement named "FSRS Card State Legacy Bucket Preservation On Save" before this phase 0 archives → **Mitigation**: coordinate with the main worktree change authors (self) — if collision appears, rename this Requirement to `FSRS Card State Legacy Bucket Preservation On Save (Phase 0)` with an explanatory sentence.

- **[Risk]** A future refactor changes `_split_card_state_buckets` to allow overlapping key sets → **Mitigation**: the new spec Requirement specifies the merge-order semantics (`{**legacy, **uuid}` with UUID winning on collision) explicitly, so the contract is clear. The round-trip test scenario "Save preserves new UUID entries via save_card_state" guards against one direction of this; any future change violating the invariant would need to update the spec first.

- **[Trade-off]** The fix uses a simple dict merge, not a `copy()` or separate persistence channel. This means any future concurrency bug that mutates `_legacy_card_states` mid-merge would corrupt the serialized JSON. **Mitigation**: the merge happens inside the existing `async with _card_states_lock:` block, which already serializes all `_card_states` writes. `_legacy_card_states` is only mutated during `_load_card_states` (init-time), not during runtime saves. The test scenarios verify the steady-state runtime behavior.

- **[Trade-off]** The round-trip test instantiates `ReviewService` via `pytest_asyncio` fixtures, which means it depends on the service's `__init__` not doing network I/O (it doesn't — Graphiti calls are lazy). If a future refactor introduces eager network init, the tests would need tmp-path + env-var monkey-patching. **Mitigation**: kept the test scope narrow to save/load/save, which is the only code path needed to verify the invariant.

## Deferred (Future Changes)

These 5 items were surfaced during the same deep-explore + ChatGPT verification session but are out of phase-0 scope. Each gets its own OpenSpec change in the near future; none of them block this phase-0 from shipping.

### §1. `a6-phase1-relates-to-write-side-activation` (P0)

- `graphiti_client.add_relationship()` is defined in the `lib` layer but has **zero callers** in `backend/app/`.
- Q1's加权融合公式 `_get_kg_relevance()` therefore only consults CANVAS_EDGE edges (the frontend-synced edges); RELATES_TO edges from Graphiti concept extraction are never written so never found.
- Open questions: which service should call `add_relationship()` (candidates: `memory_service`, `event_handlers`, `verification_service`)? At what trigger event? What is the payload schema?
- Out of phase-0 scope because: involves new service wiring, multi-file impact, and requires a design decision on call-site vs trigger.

### §2. `a6-phase1-fsrs-difficulty-integration-to-priority` (P0)

- `fsrs_difficulty` is computed by `mastery_engine.py:292` but never read by `question_generator.py:202-206`, which only uses `p_mastery + retrievability + kg_relevance` in the priority formula.
- A6 Q3 的 "难度分层 ≥80 应用题 / 60-79 验证题 / <60 基础题" is therefore a documentation-only claim — the priority formula does not exhibit this behavior.
- Open questions: weighted term in the priority formula? threshold-based question-type selection? both? What weights?
- Out of phase-0 scope because: requires re-calibration of priority weights and new integration tests covering the full priority distribution.

### §3. `a6-phase1-frontend-edge-sync-pipeline` (P0)

- Backend `sync_service._upsert_edge()` and `/api/v1/sync/batch` are complete and tested; frontend has **zero** POST calls to that endpoint from edge-related event handlers (`onConnect`, `onEdgesChange`).
- User drawing an edge in the canvas is therefore invisible to the backend graph — highest user-visible impact of the 4 P0s.
- Out of phase-0 scope because: cross-stack work requiring IndexedDB outbox + retry + dead-letter design, plus new `frontend/src/lib/sync-client.ts` module.

### §4. `a6-phase2-concept-name-path-guard-hardening` (P2)

- Current `ConceptRef.__post_init__` only rejects `concept_name.startswith("/")` (POSIX paths).
- Should also reject: Windows paths (`C:\`, `D:\`), URL schemes (`http://`, `https://`, `file://`), backslash-separated paths.
- Out of phase-0 scope because: hardening, not a correctness issue — `concept_name` comes from trusted Canvas node text in practice.

### §5. `a6-phase2-rag-faithfulness-ci-gate` (P2, valid from ChatGPT)

- Custom faithfulness implementation exists in `agentic_rag.faithfulness_check` but no CI workflow runs it against a fixed query set with a min-faithfulness threshold.
- Need: `backend/scripts/rag_quality_gate.py` + GitHub Actions workflow that runs on PR and blocks merge if faithfulness < threshold.
- Out of phase-0 scope because: requires a fixed query dataset, threshold decision, and new CI wiring.

## Migration Plan

1. Land this phase 0 commit on the `fix-concept-id-identity-unification` worktree branch (not main directly — the fix requires `_legacy_card_states` to exist, which only exists on that branch).
2. Land this OpenSpec change (the 4 artifacts under `openspec/changes/a6-phase0-...`) on `main`.
3. When the main worktree change `fix-concept-id-identity-unification` merges to main, it will include this phase 0 fix as part of its branch history. The OpenSpec change on main will archive independently.
4. Rollback strategy: `git revert <phase0-commit>` on the worktree branch restores the pre-fix behavior but leaves `_load_card_states` intact. This is safe as long as no save operation has been triggered between the revert and a subsequent re-fix.

## Open Questions

None. The 5 deferred items each have their own open questions tracked in the Deferred §1-§5 sections above, but the phase-0 scope itself has no unknowns — the fix is a 1-line payload change with clear semantics.
