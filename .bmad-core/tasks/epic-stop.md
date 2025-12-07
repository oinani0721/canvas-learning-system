# Task: Stop Epic Workflow

## Purpose
Gracefully stop a running Epic workflow, preserving all progress for later resumption.

## Prerequisites
- Workflow is currently running (`*epic-status` shows in_progress)

## Input
- **ThreadID**: Workflow thread ID (e.g., "epic-15")

## Steps

### Step 1: Check Current Status

```bash
python -m bmad_orchestrator epic-status {thread_id}
```

**Output**: Show current workflow state.

### Step 2: Stop Workflow

```bash
python -m bmad_orchestrator epic-stop {thread_id}
```

**Output**: Workflow stop confirmation.

## Output Format

### Successful Stop
```
Stopping workflow: epic-15

⚠️ Workflow Stop Requested

Current State:
  Phase: DEV
  Active Stories: 15.3, 15.5

Graceful Shutdown:
  ✓ Waiting for current Claude sessions to complete...
  ✓ Saving checkpoint to SQLite...
  ✓ Preserving worktree state...

======================================================================
WORKFLOW STOPPED
======================================================================
  Thread ID: epic-15
  Stopped At: 2025-11-30T16:45:33
  Status: stopped

Progress Preserved:
  SM: 6 drafts ✓
  PO: 6 approvals ✓
  DEV: 3 stories completed, 2 in-progress (interrupted)
  QA: 2 reviews ✓

Worktrees Preserved:
  - Canvas-develop-15.3 (interrupted during dev)
  - Canvas-develop-15.5 (interrupted during dev)

To Resume:
  *epic-resume epic-15

To Abandon:
  Delete worktrees manually and start fresh
======================================================================
```

### Not Running
```
Stopping workflow: epic-15

⚠️ Workflow is not currently running

Current Status: halted
Last Activity: 2025-11-30T14:20:45

The workflow has already stopped (due to blockers).

Options:
  - Fix blockers and resume: *epic-resume epic-15
  - Check detailed status: *epic-status epic-15
  - Start fresh: *epic-develop 15 --stories ...
```

### Already Completed
```
Stopping workflow: epic-15

✅ Workflow already completed successfully

Final Status: success
Completed At: 2025-11-30T18:45:33

No action needed.
```

### Force Stop (Not Yet Implemented)
```
Stopping workflow: epic-15

⚠️ Stop functionality is not yet fully implemented.

Current workaround:
  1. Find running Claude processes:
     Get-Process | Where-Object {$_.Name -like "*claude*"}

  2. Terminate manually:
     Stop-Process -Id {pid}

  3. Checkpoint is auto-saved, so you can resume later:
     *epic-resume epic-15

Note: Force stopping may leave worktrees in inconsistent state.
      Recommend using *epic-status to check state before resuming.
```

## Graceful vs Force Stop

| Type | Description | When to Use |
|------|-------------|-------------|
| **Graceful** | Waits for current phase to complete | Normal stop, preserves all work |
| **Force** | Terminates immediately | Emergency, may lose current story progress |

## After Stopping

1. **Inspect Worktrees**: Check worktree state manually if needed
   ```bash
   cd C:\Users\ROG\托福\Canvas-develop-15.3
   git status
   ```

2. **Resume Later**: Use `*epic-resume epic-15` to continue

3. **Abandon**: Delete worktrees and checkpoint to start fresh
   ```powershell
   # Remove all worktrees for Epic 15
   Get-ChildItem "C:\Users\ROG\托福" -Directory |
     Where-Object { $_.Name -like "Canvas-develop-15.*" } |
     Remove-Item -Recurse -Force

   # Remove checkpoint
   Remove-Item "C:\Users\ROG\托福\Canvas\bmad_orchestrator.db"
   ```

## Notes

- Progress is always saved to SQLite checkpoint
- Worktrees are preserved for inspection
- Can resume anytime with `*epic-resume`
- Force stop is last resort (may lose current story progress)
