# Tasks: Formalize FSRS Fusion Architecture (A10)

## 1. Spec Authoring

- [x] 1.1 Read `backend/app/services/mastery_fusion.py` lines 46-121 to confirm the 5-signal contract and dynamic renormalization logic
- [x] 1.2 Read `backend/app/services/signal_registry.py` lines 27-249 to confirm the 5 base weights (BKT 0.30 / FSRS 0.25 / Exam 0.25 / Calibration 0.10 / Confidence 0.10)
- [x] 1.3 Draft `specs/algo-fusion/spec.md` with 4 ADDED Requirements (Five-Signal Mastery Fusion Engine / Dynamic Weight Renormalization / Reliability Phase 1 / Output Range Clamping)
- [x] 1.4 Verify each requirement contains at least one `#### Scenario:` header (4 hashtags)

## 2. Design Document

- [x] 2.1 Write `design.md` Context section citing A10.md L88 + Phase 1 exploration findings
- [x] 2.2 Write Goals / Non-Goals section enumerating the 5 goals and 7 explicit non-goals
- [x] 2.3 Write Decisions section with 4 decisions (codify-not-aspire / twin-docs / minimal-scope / no-archive)
- [x] 2.4 Write Risks / Trade-offs table with 8 rows
- [x] 2.5 Write 7 Open Questions for ChatGPT Deep Research Review
- [x] 2.6 Write Cross-Links section linking to `docs/project-status/fr-exploration/A10-resolution-summary.md` and `A10.md`
- [x] 2.7 Write Source Anchors section with all verified `file:line` references

## 3. Documentation Twin

- [ ] 3.1 Create `docs/project-status/fr-exploration/A10-resolution-summary.md`
- [ ] 3.2 Cross-link the twin back to `openspec/changes/a10-fsrs-fusion-formalization/design.md`
- [ ] 3.3 Include the 7 ChatGPT review prompt questions in the twin

## 4. Validation

- [ ] 4.1 Run `npx openspec validate a10-fsrs-fusion-formalization --strict` and confirm 0 errors
- [ ] 4.2 Run `npx openspec status --change a10-fsrs-fusion-formalization` and confirm `Progress: 4/4 artifacts complete`
- [ ] 4.3 Read all 4 OpenSpec artifacts end-to-end to confirm no markdown syntax errors and consistent cross-references

## 5. Source Line Re-verification

- [ ] 5.1 Re-confirm `signal_registry.py:105` returns `0.30`
- [ ] 5.2 Re-confirm `mastery_fusion.py:104-107` contains the dynamic renormalization loop
- [ ] 5.3 Re-confirm `verification_service.py:932-945` contains `next_idx = current_concept_idx + 1`
- [ ] 5.4 Re-confirm `recommendation_service.py:134` contains `filtered.sort(key=lambda c: c.confidence, reverse=True)`
- [ ] 5.5 Re-confirm `question_generator.py:114` docstring and `:202-206` real formula

## 6. Git Hygiene

- [ ] 6.1 Run `git status` and confirm only the 5 expected new files appear (no accidental code edits)
- [ ] 6.2 Stage with explicit file list (no `git add -A`)
- [ ] 6.3 Commit with conventional message (`docs(A10): formalize FSRS fusion architecture as openspec change`)
- [ ] 6.4 Verify lefthook auto-push to `origin/main` succeeded
- [ ] 6.5 Confirm `git rev-parse HEAD == git rev-parse origin/main`
