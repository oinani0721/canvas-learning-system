# Task: Start Epic Full Automation Workflow

## Purpose
Start the BMad Orchestrator for fully automated 24/7 SM→PO→Dev→QA workflow using LangGraph StateGraph.

## Prerequisites
- Python 3.9+ available
- LangGraph installed (`pip install langgraph`)
- Story files exist in `docs/stories/`
- No workflow currently running for this Epic

## Input
- **EpicID**: Epic ID (e.g., "15")
- **Stories**: Comma-separated list of Story IDs (e.g., "15.1,15.2,15.3")
- **Mode** (optional): Execution mode - "parallel", "linear", "hybrid", or auto-detect (default)
- **DryRun** (optional): Preview mode, analyze without executing (default: false)

## Steps

### Step 1: Validate Environment

```bash
# Check Python and LangGraph
python --version
python -c "import langgraph; print('LangGraph:', langgraph.__version__)"
```

**Output**: Python version and LangGraph availability.

### Step 2: Analyze Dependencies (Dry Run First)

```bash
# Always show analysis first
python -m bmad_orchestrator epic-develop {epic_id} --stories {story_ids} --dry-run
```

**Output**: Dependency analysis report showing:
- Stories analyzed
- Conflicts found
- Recommended mode (parallel/linear/hybrid)
- Batch groupings

### Step 3: Start Workflow

```bash
# Start the full automation workflow
python -m bmad_orchestrator epic-develop {epic_id} \
    --stories {story_ids} \
    --base-path "C:\Users\ROG\托福\Canvas" \
    --max-turns 200 \
    {--mode {mode}} \
    {--dry-run}
```

**Output**: Workflow started confirmation with thread ID.

## Output Format

### Success - Dry Run
```
======================================================================
BMad Orchestrator - Epic Development Workflow
======================================================================
Epic ID: 15
Stories: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
Base Path: C:\Users\ROG\托福\Canvas
Worktree Base: Auto (parent of base_path)
Max Turns: 200
Mode: Auto-detect
UltraThink: True
Dry Run: True
======================================================================

[DRY RUN] Would execute workflow with above settings
[DRY RUN] No actual changes will be made

[DependencyAnalyzer] Analyzing 6 stories...
[DependencyAnalyzer] Parsed 6 story files
[DependencyAnalyzer] Found 2 conflict pairs
[DependencyAnalyzer] Generated 3 batches
[DependencyAnalyzer] Recommended mode: hybrid

============================================================
BMad Dependency Analysis Report
============================================================

Stories Analyzed: 6
Conflicts Found: 2
Batches Generated: 3
Recommended Mode: HYBRID

Parallel Batches:
  Batch 1: 15.1, 15.2, 15.4
  Batch 2: 15.3, 15.5
  Batch 3: 15.6

Conflicts:
  15.1 ↔ 15.3: src/canvas_utils.py
  15.3 ↔ 15.5: src/ebbinghaus_review.py

============================================================
```

### Success - Workflow Started
```
======================================================================
BMad Orchestrator - Epic Development Workflow
======================================================================
Epic ID: 15
Stories: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
Base Path: C:\Users\ROG\托福\Canvas
Mode Override: Auto-detect
Max Turns: 200
======================================================================

⚠️  This will start an automated 24/7 development workflow.
    The workflow will run unattended until completion.

    Press Enter to continue, or Ctrl+C to cancel...

[Press Enter]

✅ Workflow Started!
   Thread ID: epic-15
   Status: SM phase initiated

   The workflow is now running in the background.

   Commands:
     *epic-status epic-15  - Check progress
     *epic-stop epic-15    - Stop workflow
     *epic-resume epic-15  - Resume if interrupted

======================================================================
```

### Error - Missing Stories
```
❌ Error: Story files not found for: 15.4, 15.5
   Expected locations:
     - docs/stories/15.4.story.md
     - docs/stories/story-15.4.md
     - docs/stories/15.4.md
```

### Error - Workflow Already Running
```
⚠️ Warning: Workflow already running for epic-15
   Current Phase: DEV
   Use '*epic-status epic-15' to check progress
   Use '*epic-stop epic-15' to stop before starting new workflow
```

## Workflow Phases (v1.1.0 - 12 Node Architecture)

The orchestrator executes these phases automatically:

```
SM → PO → ANALYSIS → SDD_PRE → DEV → QA → SDD → MERGE → COMMIT → CLEANUP → END
                        ↓              ↓     ↓
                       HALT ←←←←←←←←←←←←←←←←←←
                        ↓
                     CLEANUP → END
```

| Phase | Agent | Description |
|-------|-------|-------------|
| SM | Scrum Master | Generate Story drafts from Epic |
| PO | Product Owner | Approve Story drafts |
| ANALYSIS | Orchestrator | Analyze dependencies, generate batches |
| **SDD_PRE** ⭐ | Orchestrator | **Pre-dev SDD validation (Tier 1/2 blocking)** |
| DEV | Developer | Implement Stories (parallel batches) |
| QA | QA Agent | Review implementations |
| FIX | Developer | Fix CONCERNS issues (1 retry) |
| **SDD** ⭐ | Orchestrator | **Post-QA SDD validation (Tier 3/4 contract testing)** |
| MERGE | Orchestrator | Git worktree merge |
| COMMIT | Orchestrator | Final commit with changelog |
| HALT | Orchestrator | Handle failures, generate report |
| **CLEANUP** ⭐ | Orchestrator | **Worktree cleanup (always runs, even on HALT)** |
| **Status** | Orchestrator | **Auto-persist Story status to YAML** |

### v1.1.0 New Features

1. **SDD Pre-Validation** (`sdd_pre_validation_node`)
   - Runs **before** DEV phase
   - Validates OpenAPI specs (Tier 1) and JSON Schemas (Tier 2)
   - **Blocks development** if critical SDD violations found

2. **SDD Post-Validation** (`sdd_validation_node`)
   - Runs **after** QA phase
   - Tier 3: Architecture compliance
   - Tier 4: Contract testing (Schemathesis)

3. **Guaranteed Cleanup** (`cleanup_node`)
   - **Always runs** - even after HALT
   - Removes worktrees to prevent disk bloat
   - Fail-forward design: partial failures still cleanup

4. **Session Health Monitoring**
   - 5-minute stuck detection
   - Partial result extraction from stuck sessions
   - Circuit breaker pattern for reliability

### SDD Configuration

SDD validation behavior is configurable via `.bmad-core/sdd-config.yaml`:

```yaml
sdd:
  enabled: true
  tiers:
    tier1_openapi: { enabled: true, blocking: true }
    tier2_schema: { enabled: true, blocking: true }
    tier3_architecture: { enabled: true, blocking: false }
    tier4_contract: { enabled: true, blocking: false }
```

## Crash Recovery

Workflow state is persisted to SQLite (`bmad_orchestrator.db`). If interrupted:
- Use `*epic-resume epic-15` to continue from checkpoint
- All completed work is preserved
- Only pending phases are re-executed

## Notes

- Each Claude session runs in separate context (200K tokens)
- Stories are developed in Git worktrees for isolation
- Conflict-free Stories are batched for parallel execution
- QA Gate required: Only PASS or WAIVED can merge
- Auto-retry: CONCERNS issues get 1 fix attempt before HALT
