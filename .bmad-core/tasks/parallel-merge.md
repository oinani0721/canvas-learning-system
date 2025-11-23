# Task: parallel-merge

## Purpose
Merge completed worktree branches back to main.

## Input
- Story ID: "13.2" or "--all" for all completed

## Prerequisites
- Story status: "ready-to-merge"
- Tests passed
- QA Gate: PASS (or WAIVED with documented reason)
- No uncommitted changes in worktree

## Steps

### 1. Validate Ready to Merge
```bash
python scripts/validate-merge-ready.py --story {story_id}
```

Checks:
- Status is "ready-to-merge"
- All tests pass
- QA Gate is PASS or WAIVED
- No uncommitted changes
- Branch is up to date with main

### 2. Update from Main (Prevent Conflicts)
```bash
cd ../Canvas-develop-{story_id}
git fetch origin main
git rebase origin/main
```

### 3. Run Final Tests
```bash
pytest tests/ -v
```

### 4. Merge to Main
```bash
cd {main_repo}
git checkout main
git merge develop-story-{story_id} --no-ff -m "Merge Story {story_id}: {title}"
```

### 5. Update Status
Update `.bmad-core/data/canvas-project-status.yaml`:
- Mark Story as completed
- Update last_modified timestamp

### 6. Output

```markdown
## Merge Complete

### Story 13.2: Review Scheduling
- **Branch**: develop-story-13.2
- **Commits merged**: 5
- **Files changed**: 3
- **Tests**: 12/12 passed
- **QA Gate**: PASS

### Merge Details
```
commit abc1234
Merge: def5678 ghi9012
Author: Developer
Date: 2025-11-20

    Merge Story 13.2: Review Scheduling

    - Added adaptive scheduling algorithm
    - Implemented spaced repetition
    - 12 tests added
```

### Post-Merge Status
- Main branch updated
- Story 13.2 marked completed in YAML status
- Worktree can be removed: `*cleanup 13.2`

### Remaining Worktrees
| Story | Status | QA Gate |
|-------|--------|---------|
| 13.1 | dev-complete | - |
| 13.4 | qa-reviewing | CONCERNS |
```

## Flags
- `--all`: Merge all completed worktrees
- `--force`: Skip test re-run (use cautiously)

## Error Handling
- If tests fail: "Tests failed. Fix before merging."
- If not ready: "Story {id} status is not 'ready-to-merge'"
- If QA not passed: "Story {id} QA Gate is {gate}. Requires PASS or WAIVED."
- If merge conflict: "Conflict detected. Resolve in worktree first."
