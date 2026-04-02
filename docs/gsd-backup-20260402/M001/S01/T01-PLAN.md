---
estimated_steps: 4
estimated_files: 3
skills_used: []
---

# T01: Git-remove all tracked garbage files and deleted snapshots

**Slice:** S01 — 代码库清理 + 环境就绪
**Milestone:** M001

## Description

Remove 16 tracked garbage files (Windows temp leaks, single-char files, one-off scripts, test prompt files) and ~60 deleted-but-tracked unicode snapshot files from git tracking. This is pure mechanical `git rm` work with zero code changes. The `.gitignore` already covers `.canvas-learning/` and `*.canvas` patterns, so no new ignore rules are needed.

## Steps

1. Run `git rm` on the 16 tracked garbage files:
   - Root (10): `R`, `UsersHeishingAppDataLocalTempwrite-pig.js`, `UsersHeishingAppDataLocalTempwrite-story.js`, `UsersHeishingAppDataLocalTempwrite-test-event-bus.js`, `UsersHeishingAppDataLocalTempwrite-test-fc.js`, `UsersHeishingAppDataLocalTempwrite-test-pig.js`, `UsersHeishingAppDataLocalTempwrite-test-qa.js`, `UsersHeishingAppDataLocalTempwrite-tests.js`, `test-fix-v11-prompt.txt`, `test-pipe-prompt.txt`
   - Backend (6): `backend/!`, `backend/J`, `backend/R`, `backend/schema_test.canvas`, `backend/workflow_test.canvas`, `backend/_gen_mastery_tests.py`
2. Run `git rm` on all deleted-but-tracked files (the ~60 unicode snapshot files and unicode-named files). Use `git ls-files --deleted` to get the exact list, then pipe to `git rm`.
3. Verify `.gitignore` already contains `.canvas-learning/` and `*.canvas` patterns (no changes needed).
4. Commit the cleanup with message: "chore: remove tracked garbage files and stale snapshots (R042)"

## Must-Haves

- [ ] All 16 named garbage files removed from git tracking
- [ ] All ~60 deleted-but-tracked snapshot/unicode files removed from git tracking
- [ ] No new `.gitignore` rules added (existing rules already cover these patterns)
- [ ] Clean commit with descriptive message

## Verification

- `git ls-files -- R 'UsersHeishing*' 'test-fix*' 'test-pipe*' 'backend/!' 'backend/J' 'backend/R' 'backend/schema_test.canvas' 'backend/workflow_test.canvas' 'backend/_gen_mastery_tests.py'` returns empty output
- `git status --porcelain | grep '^ D' | wc -l` returns 0
- `git log -1 --oneline` shows the cleanup commit

## Inputs

- `R` — tracked garbage file (root)
- `UsersHeishingAppDataLocalTempwrite-pig.js` — tracked garbage file (root)
- `backend/!` — tracked garbage file (backend)
- `backend/.canvas-learning/snapshots/` — deleted-but-tracked snapshot directories
- `.gitignore` — verify existing ignore patterns cover these files

## Expected Output

- `.gitignore` — verified unchanged (existing patterns sufficient)
- `R` — removed from tracking
- `backend/!` — removed from tracking
- `backend/.canvas-learning/snapshots/` — removed from tracking
