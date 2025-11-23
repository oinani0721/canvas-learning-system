# Task: planning-status

## Purpose
Show current Planning iteration state and history.

## Steps

### 1. Gather Status Information
```bash
python scripts/planning-status.py
```

### 2. Output

```markdown
## Planning Iteration Status

### Current State
- **Active Iteration**: 4
- **Status**: In Progress
- **Branch**: planning-iteration-4
- **Started**: 2025-11-19 10:30:00
- **Goal**: Add Epic 13 - Ebbinghaus Review

### Uncommitted Changes
- docs/prd/epic-13-ebbinghaus.md (modified)
- specs/api/canvas-api.openapi.yml (modified)

### Iteration History

| Iteration | Status | Version | Date | Goal |
|-----------|--------|---------|------|------|
| 4 | In Progress | - | 2025-11-19 | Epic 13 - Ebbinghaus |
| 3 | Finalized | v1.2.0 | 2025-11-15 | Memory System |
| 2 | Finalized | v1.1.0 | 2025-11-10 | Agent Optimization |
| 1 | Finalized | v1.0.0 | 2025-11-05 | Initial PRD |

### SDD Spec Versions

| Spec | Current | Last Finalized |
|------|---------|----------------|
| canvas-api.openapi.yml | v1.3.0-draft | v1.2.0 |
| canvas-node.schema.json | v1.1.0 | v1.1.0 |
| agent-response.schema.json | v1.0.0 | v1.0.0 |

### Available Commands
- `*validate` - Check current changes for breaking changes
- `*finalize` - Complete this iteration
- `*rollback` - Restore previous state
- `*compare 3` - Compare to iteration 3
```

## Flags
- `--json`: Output as JSON for scripting
- `--history-only`: Show only iteration history

## Error Handling
- If no iterations: "No iterations found. Run *init to start"
