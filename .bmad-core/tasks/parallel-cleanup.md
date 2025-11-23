# Task: parallel-cleanup

## Purpose
Remove completed and merged worktrees to free disk space.

## Input
- Story ID: "13.2" or "--all" for all merged

## Prerequisites
- Story already merged to main
- Worktree exists

## Steps

### 1. Validate Safe to Remove
```bash
python scripts/validate-cleanup.py --story {story_id}
```

Checks:
- Branch is merged to main
- No uncommitted changes
- Not currently checked out elsewhere

### 2. Remove Worktree
```bash
git worktree remove ../Canvas-develop-{story_id}
```

### 3. Delete Branch (Optional)
```bash
git branch -d develop-story-{story_id}
```

### 4. Update Tracking
Remove entry from `.bmad-core/data/worktree-tracking.yaml`

### 5. Output

```markdown
## Cleanup Complete

### Removed Worktrees

| Story | Worktree | Branch | Disk Freed |
|-------|----------|--------|------------|
| 13.2 | Canvas-develop-13.2 | develop-story-13.2 | 45 MB |

### Summary
- Worktrees removed: 1
- Branches deleted: 1
- Total disk freed: 45 MB

### Remaining Active Worktrees
| Story | Status |
|-------|--------|
| 13.1 | in-progress |
| 13.4 | in-progress |
```

## Flags
- `--all`: Cleanup all merged worktrees
- `--keep-branch`: Don't delete the branch
- `--force`: Remove even if not merged (dangerous)

## Error Handling
- If not merged: "Story {id} not merged yet. Use --force to remove anyway."
- If worktree not found: "No worktree found for Story {id}"
- If uncommitted changes: "Uncommitted changes in worktree. Commit or stash first."
