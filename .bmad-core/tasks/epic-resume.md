# Task: Resume Epic Workflow

## Purpose
Resume an interrupted or halted Epic workflow from its last checkpoint.

## Prerequisites
- Workflow was previously started with `*epic-develop`
- SQLite checkpoint exists with saved state
- Workflow status is NOT "success" or manually stopped

## Input
- **ThreadID**: Workflow thread ID (e.g., "epic-15")

## Steps

### Step 1: Check Current Status

```bash
python -m bmad_orchestrator epic-status {thread_id}
```

**Output**: Show current workflow state before resuming.

### Step 2: Resume Workflow

```bash
python -m bmad_orchestrator epic-resume {thread_id}
```

**Output**: Workflow resumes from last checkpoint.

## Output Format

### Successful Resume
```
Resuming workflow: epic-15

Current Phase: DEV
Resuming...

======================================================================
WORKFLOW RESUMED
======================================================================
  Thread ID: epic-15
  Resumed From: DEV phase, batch 2/3

  Completed Work Preserved:
    - SM: 6 drafts ✓
    - PO: 6 approvals ✓
    - DEV: 3 stories (batch 1) ✓
    - QA: 2 reviews ✓

  Resuming With:
    - DEV: Stories 15.3, 15.5 (batch 2)
    - Remaining batches: 1

  The workflow is now running.
  Use '*epic-status epic-15' to monitor progress.
======================================================================
```

### Resume After Fix
```
Resuming workflow: epic-15

Current Phase: HALT
Previous Status: halted (3 blockers)

⚠️ Workflow was halted due to blockers.
   Ensure blockers are fixed before resuming.

Blockers:
  - 15.3: DEV_FAILURE - Test failures in canvas_utils_test.py
  - 15.5: DEV_FAILURE - Import error: module 'fsrs' not found
  - 15.4: QA_FAIL - Security vulnerability in input validation

Continue anyway? [y/N]: y

Resuming...

======================================================================
WORKFLOW RESUMED (with retry)
======================================================================
  Retrying blocked Stories: 15.3, 15.4, 15.5

  Note: Each Story gets 1 retry attempt.
  If still blocked, workflow will HALT again.
======================================================================
```

### Already Completed
```
Resuming workflow: epic-15

❌ Cannot resume: Workflow already completed successfully

Final Status: success
Completed At: 2025-11-30T18:45:33

Statistics:
  Stories: 6/6 completed
  Commits: 6
  Blockers: 0

To start a new workflow, use:
  *epic-develop 15 --stories 15.1,15.2,...
```

### Not Found
```
Resuming workflow: epic-15

❌ No checkpoint found for thread: epic-15

Cannot resume a workflow that was never started.

To start a new workflow, use:
  *epic-develop 15 --stories 15.1,15.2,...
```

## Crash Recovery Scenarios

| Scenario | What Happens |
|----------|--------------|
| Claude session compact | Checkpoint saved, resume from same phase |
| Machine shutdown | Checkpoint in SQLite, resume on restart |
| Network failure | Checkpoint saved, retry current Story |
| Manual stop | Use `*epic-resume` to continue |
| HALT due to blockers | Fix issues, then `*epic-resume` |

## Notes

- All completed work is preserved in checkpoint
- Worktrees remain intact and can be inspected
- Blockers should be fixed manually before resuming
- Max 1 retry per blocked Story
- Use `*epic-status` before resuming to understand state
