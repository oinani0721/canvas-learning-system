# Task: Check Epic Workflow Status

## Purpose
Show the current status and progress of a running or completed Epic workflow.

## Prerequisites
- Workflow must have been started with `*epic-develop`
- SQLite checkpoint file exists (`bmad_orchestrator.db`)

## Input
- **ThreadID**: Workflow thread ID (e.g., "epic-15")

## Steps

### Step 1: Query Workflow Status

```bash
python -m bmad_orchestrator epic-status {thread_id}
```

**Output**: Detailed workflow status report.

## Output Format

### In Progress
```
Checking status for: epic-15

======================================================================
WORKFLOW STATUS: epic-15
======================================================================
Session ID: epic-15-20251130-143022
Epic ID: 15
Current Phase: DEV
Final Status: in_progress
Started At: 2025-11-30T14:30:22

Progress:
  SM: 6 drafts created
  PO: 6 stories approved
  DEV: 3 stories developed
  QA: 2 stories reviewed

Phase Status:
  SM: completed
  PO: completed
  DEV: in_progress
  QA: pending
  MERGE: pending

Execution:
  Mode: hybrid
  Current Batch: 2/3

Active Work:
  - Story 15.3 in worktree Canvas-develop-15.3 (dev_complete)
  - Story 15.5 in worktree Canvas-develop-15.5 (qa_reviewing)

Commits:
  - abc1234: Story 15.1 - Canvas node validation
  - def5678: Story 15.2 - API endpoint implementation
  - ghi9012: Story 15.4 - Unit tests
======================================================================
```

### Completed Successfully
```
======================================================================
WORKFLOW STATUS: epic-15
======================================================================
Session ID: epic-15-20251130-143022
Epic ID: 15
Current Phase: COMPLETE
Final Status: success
Started At: 2025-11-30T14:30:22
Completed At: 2025-11-30T18:45:33

Progress:
  SM: 6 drafts created
  PO: 6 stories approved
  DEV: 6 stories developed
  QA: 6 stories reviewed

Phase Status:
  SM: completed
  PO: completed
  DEV: completed
  QA: completed
  MERGE: completed

Statistics:
  Total Duration: 4h 15m
  Stories Processed: 6
  Dev Success: 6
  QA Passed: 5
  QA Waived: 1
  Commits: 6
  Blockers: 0

Commits:
  - abc1234: Story 15.1 - Canvas node validation
  - def5678: Story 15.2 - API endpoint implementation
  - ghi9012: Story 15.3 - Canvas utils refactor
  - jkl3456: Story 15.4 - Unit tests
  - mno7890: Story 15.5 - Integration tests
  - pqr2345: Story 15.6 - Documentation update
======================================================================
```

### Halted with Blockers
```
======================================================================
WORKFLOW STATUS: epic-15
======================================================================
Session ID: epic-15-20251130-143022
Epic ID: 15
Current Phase: HALT
Final Status: halted
Started At: 2025-11-30T14:30:22
Halted At: 2025-11-30T16:20:45

Progress:
  SM: 6 drafts created
  PO: 6 stories approved
  DEV: 4 stories developed
  QA: 3 stories reviewed

Phase Status:
  SM: completed
  PO: completed
  DEV: partially_failed
  QA: completed
  MERGE: skipped

Statistics:
  Stories Processed: 6
  Dev Success: 4
  Dev Failed: 2
  QA Passed: 3
  QA Failed: 1
  Commits: 3
  Blockers: 3

Blockers:
  - 15.3: DEV_FAILURE - Test failures in canvas_utils_test.py
  - 15.5: DEV_FAILURE - Import error: module 'fsrs' not found
  - 15.4: QA_FAIL - Security vulnerability in input validation

Recommendation:
  1. Fix blockers manually in respective worktrees
  2. Run '*epic-resume epic-15' to continue from checkpoint
======================================================================
```

### Not Found
```
❌ No workflow found for thread: epic-15

Possible causes:
  - Workflow was never started
  - Different thread ID was used
  - Checkpoint database was deleted

Try:
  - List recent workflows with: ls bmad_orchestrator.db
  - Start new workflow with: *epic-develop 15 --stories 15.1,15.2,...
```

## Notes

- Status is read from SQLite checkpoint (`bmad_orchestrator.db`)
- All workflow states are preserved even after completion
- Use this to monitor 24/7 unattended workflows
- Combine with `*epic-stop` to pause if issues detected
