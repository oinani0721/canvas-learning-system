# Task: parallel-status

## Purpose
Show progress of all active parallel development worktrees.

## Steps

### 1. Find All Worktrees
```bash
git worktree list
```

### 2. Read Status from Each Worktree
```bash
python scripts/check-worktree-status.py
```

For each worktree, read `.worktree-status.yaml`

### 3. Output

```markdown
## Parallel Development Status

### Active Worktrees

| Worktree | Story | Status | Tests | QA Gate | Ready |
|----------|-------|--------|-------|---------|-------|
| Canvas-develop-13.1 | 13.1 | 🔄 dev-complete | Passed | - | ❌ |
| Canvas-develop-13.2 | 13.2 | ✅ ready-to-merge | Passed | PASS | ✅ |
| Canvas-develop-13.4 | 13.4 | 🔄 qa-reviewing | Passed | CONCERNS | ❌ |

### Progress Summary
- **Total**: 3 worktrees
- **Dev Complete**: 1
- **QA Reviewing**: 1
- **Ready to Merge**: 1
- **Failed Tests**: 0

### Detailed Status

#### Story 13.1 (dev-complete) 🔄
- Branch: develop-story-13.1
- Commits: 3
- Files changed: 2
- Tests: 12/12 passed
- QA Gate: Not reviewed yet
- Next: `/qa` → `*review 13.1` → `*gate 13.1`

#### Story 13.2 (ready-to-merge) ✅
- Branch: develop-story-13.2
- Commits: 5
- Files changed: 3
- Tests: 12/12 passed
- QA Gate: **PASS**
- Ready to merge

#### Story 13.4 (qa-reviewing) ⚠️
- Branch: develop-story-13.4
- Commits: 4
- Files changed: 2
- Tests: 10/10 passed
- QA Gate: **CONCERNS** - Minor code style issues
- Next: Address concerns or request WAIVE

### Recommended Actions
1. ✅ Merge Story 13.2: `*merge 13.2` (QA Gate = PASS)
2. 🔍 Story 13.1 needs QA review: run `/qa` in worktree
3. ⚠️ Story 13.4 has CONCERNS: fix issues or request waiver

### Commands
- Merge completed: `*merge 13.2`
- Merge all completed: `*merge --all`
- Cleanup merged: `*cleanup`
```

## Flags
- `--watch`: Continuous monitoring (refresh every 30s)
- `--json`: Output as JSON

## Error Handling
- If no worktrees: "No active parallel worktrees found"
- If status file missing: "Status file missing for {worktree}"
