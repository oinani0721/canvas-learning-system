## Context

`openspec/specs/concept-identity/spec.md` was created by archiving `2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation`. Its `## Purpose` is still the archiver's placeholder (`TBD - created by archiving change ...`), and it holds exactly one requirement, which describes a two-bucket FSRS card-state model:

- `ReviewService._save_card_states()` shall serialize `{**self._legacy_card_states, **self._card_states}`;
- `_load_card_states` shall partition keys with `is_uuid_v4(key)`;
- the merge shall happen inside `async with _card_states_lock:` to guard against a concurrent `save_card_state()` mutation.

Measured state of the implementation on `card-u9-mastery` @ `8f7440ef`:

| Claim in spec | Measurement | Result |
|---|---|---|
| `_legacy_card_states` bucket exists | `grep -E '_legacy_card_states\|is_uuid_v4' -- backend/app` | **0 hits** |
| ...ever existed | `git log --oneline -S'_legacy_card_states' -- backend/app/services/review_service.py` | **empty** |
| `_load_card_states` partitions keys | read `review_service.py:545-563` | returns `loaded` / `{}` verbatim, **no partitioning** |
| `save_card_state(concept_id, concept_name, ...)` | `review_service.py:2364` signature | **no `concept_name` parameter** |

So the requirement is not describing a regressed implementation; it describes an implementation that was never written on this branch. A reader who trusts the spec would conclude that pre-migration FSRS data is being preserved on save. It is not, because there is only one bucket and nothing to preserve.

## Goals / Non-Goals

**Goals:**

- Make the spec tree stop asserting behavior that no code implements.
- Preserve, in the removal record itself, the evidence that the requirement was never implemented — so the removal cannot later be mistaken for an accidental deletion or for the retirement of a working feature.
- Perform the removal through `openspec archive` so the main spec is edited by the tool, not by hand.

**Non-Goals:**

- Writing a replacement requirement for the single-bucket behavior that `_save_card_states` actually has. That is a specification-authoring decision about what the `concept-identity` capability should guarantee going forward; it needs its own proposal and is out of scope here.
- Any change to `backend/app` runtime behavior. This change ships no code.
- Touching `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/`. The historical record of the original requirement stays intact and readable.
- Fixing the placeholder `## Purpose` line. It is pre-existing and orthogonal to whether this requirement stays or goes.

## Decisions

**D1 — `REMOVED`, not `MODIFIED`.**
Alternative considered: rewrite the requirement under `## MODIFIED Requirements` to describe the single-bucket behavior that exists today. Rejected: `MODIFIED` asserts that a requirement's behavior changed. Nothing changed — the two-bucket behavior was never there. Using `MODIFIED` would silently convert "this was never true" into "this used to be true and now differs", which is exactly the misreading this change exists to prevent. `REMOVED` plus an evidence-bearing `Reason` states the actual situation.

**D2 — Leave the capability with zero requirements rather than inventing a replacement.**
Alternative considered: pair the removal with an `ADDED` requirement specifying the current single-bucket serialization, so the capability is not left empty. Rejected for this change: an empty capability is an accurate signal that nothing at spec level is currently guaranteed here, whereas a hastily-written replacement would freeze today's implementation details into a contract without anyone having decided they *should* be contractual. Writing that requirement deliberately is worth doing; doing it as a side effect of a removal is how implementation accidents become specifications.

**D3 — Route the edit through `openspec archive`, never by hand.**
The repository's OpenSpec workflow (root `CLAUDE.md`) forbids hand-editing `openspec/specs/**` and forbids `git mv` for archiving; `archive` is what merges the delta into the main spec. Doing it by hand would produce the same text while bypassing the validation that makes the delta well-formed, and would leave no change directory explaining why the requirement went away.

**D4 — Put the three measurements in `Reason`, not only in this design document.**
`Reason` travels with the removal into the archived change; a design document is easy to lose track of. The point of the evidence is to be findable by whoever later asks "why is `concept-identity` empty?".

## Risks / Trade-offs

- **[Risk]** An empty `concept-identity` spec might fail `openspec validate --specs --strict`, or might read as a bug rather than a decision. → **Mitigation**: validation is re-run after archive and the result reported as-is; if strict validation rejects an empty capability, the correct response is to stop and escalate the specification-authoring decision from D2, not to invent a placeholder requirement so the gate turns green.
- **[Risk]** Someone later reintroduces the two-bucket wording from the archived change, believing it documents real behavior. → **Mitigation**: the `Reason` field records that `git log -S'_legacy_card_states'` is empty, which is a claim about the entire branch history and therefore stays checkable regardless of the current code.
- **[Trade-off]** The capability's `## Purpose` stays at the archiver's `TBD` placeholder. Rewriting it is a separate authoring decision (see Non-Goals) and folding it in here would mix an evidence-driven removal with an editorial rewrite.
- **[Risk]** Reading this change as license to delete other requirements that "look unimplemented". → **Mitigation**: the bar used here is three independent measurements including a full-history `git log -S`, not a single grep of current code. Absence in current code alone would not have been sufficient.

## Migration Plan

1. Validate the change: `openspec validate retire-fsrs-legacy-bucket-spec --strict`.
2. Confirm all four artifacts are complete: `openspec status --change retire-fsrs-legacy-bucket-spec` → `Progress: 4/4`.
3. `openspec archive retire-fsrs-legacy-bucket-spec` — the CLI merges the `REMOVED` delta into `openspec/specs/concept-identity/spec.md` and moves the change directory under `openspec/changes/archive/`.
4. Verify the main spec was edited by the tool: `git diff --no-color -- openspec/specs/concept-identity/spec.md` shows the requirement and its three scenarios removed.
5. Re-run `openspec validate --specs --strict`; compare against the pre-change baseline of 14 specs passing.

**Rollback**: `git revert` the archive commit. No runtime behavior is affected in either direction, so rollback needs no deploy, no data migration, and no coordination with running services.

## Open Questions

- Should `concept-identity` eventually carry a requirement describing the single-bucket `_save_card_states` contract that actually exists (D2)? Deferred to a separate proposal.
- Should the placeholder `## Purpose` line be written properly, or should the capability be retired outright once it has no requirements? Deferred; both are authoring decisions beyond removing a never-implemented requirement.
