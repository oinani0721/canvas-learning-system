# Wave-Based Parallel + Sequential Development Command

**Purpose**: Execute Epic development with wave-based parallelization and integrated BMad QA workflow.

**Usage**: `/parallel-wave [options]`

---

## Command Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-Epic` | Required | Epic number (e.g., "12") |
| `-StartWave` | Auto-detect | Starting wave number |
| `-EndWave` | All | Ending wave number |
| `-QAMode` | "integrated" | QA mode: "integrated" (per-story) or "batch" (per-wave) |
| `-MaxParallel` | 3 | Maximum concurrent worktrees |
| `-UltraThink` | false | Enable extended thinking mode |

---

## Wave Definition Format

Waves are defined in `scripts/wave-config-epic{N}.json`:

```json
{
  "epic": 12,
  "waves": [
    {
      "id": 1,
      "stories": ["12.1", "12.2", "12.4"],
      "mode": "parallel",
      "status": "completed"
    },
    {
      "id": 2,
      "stories": ["12.3", "12.5"],
      "mode": "parallel",
      "dependencies": { "12.3": ["12.2"], "12.5": ["12.1"] }
    },
    {
      "id": 3,
      "stories": ["12.6"],
      "mode": "sequential",
      "dependencies": { "12.6": ["12.5"] }
    }
  ]
}
```

---

## Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Wave-Based Development Workflow                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Load wave-config-epic{N}.json                           │
│  2. Find first incomplete wave                               │
│  3. For each wave:                                           │
│     ├─ Create worktrees for parallel stories                 │
│     ├─ Launch Claude sessions (Dev phase)                    │
│     ├─ Wait for all Dev completions                          │
│     ├─ Run QA for each story (integrated mode)               │
│     │   └─ If FAIL: retry once, then pause                   │
│     ├─ Update wave-progress.json                             │
│     └─ Proceed to next wave if all PASS                      │
│  4. Final merge to main                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Example Usage

### Basic Usage
```bash
# Start Epic 12 development from Wave 2
/parallel-wave -Epic 12 -StartWave 2

# Full Epic with UltraThink
/parallel-wave -Epic 12 -UltraThink

# Limited parallel (2 max)
/parallel-wave -Epic 12 -MaxParallel 2
```

### Status Check
```bash
# Check current progress
/parallel-wave -Epic 12 -Status
```

### Output
```
📊 Wave Development Status - Epic 12
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wave 1: ✅ COMPLETED
  ├─ 12.1 Graphiti:      ✅ DEV_PASS → QA_PASS
  ├─ 12.2 LanceDB POC:   ✅ DEV_PASS → QA_PASS
  └─ 12.4 Temporal:      ✅ DEV_PASS → QA_PASS

Wave 2: 🔄 IN_PROGRESS
  ├─ 12.3 Migration:     🔄 DEV_IN_PROGRESS (45%)
  └─ 12.5 StateGraph:    🔄 DEV_IN_PROGRESS (30%)

Wave 3-6: ⏳ PENDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Cost: $8.45 | ⏱️ Elapsed: 4h 23m
📁 Worktrees: 2 active, 3 completed
```

---

## Integration with BMad

### Dev Phase
```bash
# In each worktree, the script runs:
/dev
*develop-story {story_id}
```

### QA Phase (if QAMode = "integrated")
```bash
# After Dev completes:
/qa
*review {story_id}
*gate {story_id}
```

### Gate Decisions
| Decision | Action |
|----------|--------|
| PASS | Continue to next story/wave |
| CONCERNS | Log warning, continue |
| FAIL | Retry once, then pause for human |
| WAIVED | Log waiver, continue |

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `scripts/wave-develop.ps1` | Core execution engine |
| `scripts/wave-progress.json` | Real-time status tracking |
| `scripts/wave-config-epic{N}.json` | Wave definitions |
| `scripts/qa-parallel.ps1` | Parallel QA execution |
| `Canvas-develop-{story}/` | Worktree directories |

---

## Error Handling

1. **Dev Failure**: Log error, mark story as FAILED, continue with others
2. **QA Failure**: Retry once with fixes, then pause
3. **Merge Conflict**: Pause and alert for manual resolution
4. **Timeout**: After 2 hours per story, mark as TIMEOUT

---

## Cost Control

Default limits (configurable):
- `max-turns`: 300 per story
- `timeout`: 7200 seconds (2 hours) per story
- `max-retries`: 1 for QA failures

---

## See Also

- `/parallel` - Original parallel coordinator
- `/planning` - Planning iteration management
- BMad QA Agent commands: `*review`, `*gate`
