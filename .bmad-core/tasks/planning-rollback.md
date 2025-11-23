# Task: planning-rollback

## Purpose
Restore Planning files to a previous iteration state.

## Prerequisites
- Target iteration snapshot exists
- Current work can be discarded (or stashed)

## Steps

### 1. Confirm Rollback
```markdown
⚠️ Rollback Warning

Current iteration: {N}
Target iteration: {M}

This will:
- Restore PRD files to iteration {M} state
- Restore Architecture files to iteration {M} state
- Restore Specs to iteration {M} state
- Discard all changes since iteration {M}

Proceed? (y/N)
```

### 2. Stash Current Work (Optional)
```bash
git stash push -m "Pre-rollback stash from iteration {N}"
```

### 3. Execute Rollback
```bash
python scripts/rollback-iteration.py --target {M}
```

The script will:
- Read `iterations/iteration-{M}.json`
- Restore files from Git history at that tag
- Update iteration tracking

### 4. Git Operations
```bash
# Reset to target tag
git checkout planning-v{M}

# Create new branch for recovery work
git checkout -b planning-recovery-from-{M}
```

### 5. Output
```markdown
✅ Rollback Complete
   └─ Restored to: Iteration {M}
   └─ Branch: planning-recovery-from-{M}
   └─ Stash: stash@{0} (if applicable)

📋 You can now:
   - Start new iteration: *init
   - View restored state: *status
   - Recover stash: git stash pop
```

## Flags
- `--force`: Skip confirmation prompt
- `--no-stash`: Discard current changes without stashing

## Error Handling
- If target iteration doesn't exist: "Iteration {M} not found"
- If uncommitted changes and no stash: "Uncommitted changes. Use --force to discard"
