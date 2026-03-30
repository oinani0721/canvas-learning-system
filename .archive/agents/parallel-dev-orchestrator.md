# Parallel Dev Orchestrator Agent

**Agent Type**: System-Level Parallel Development Coordinator
**Version**: 1.0.0
**Category**: BMad Phase 4 Parallel Development Management
**Created**: 2025-11-20
**Status**: Active

---

## Purpose

High-level orchestration agent responsible for **coordinating parallel development workflows** across multiple stories. This agent:
- **Manages** Git worktree lifecycle for parallel development
- **Coordinates** multiple Claude sessions for Draft/Develop/QA phases
- **Analyzes** dependencies to prevent file conflicts
- **Merges** completed worktrees back to main branch
- **Tracks** parallel development status

This is the **command center** for Phase 4 parallel development operations.

---

## Design Decisions

| Decision | Choice |
|----------|--------|
| Parallel Scope | Full workflow (*draft, *develop, *review) |
| Parallel Count | 8+ Stories |
| QA Timing | After merge, grouped QA |
| Code Consistency | Rely on devLoadAlwaysFiles |
| YAML Concurrency | Each worktree has independent status |
| API Contract | Read-only during parallel development |
| Dependency Analysis | affected_files field in Story |
| Conflict Handling | Use existing *correct-course |
| Intermediate Status | New 'dev-complete' status |

---

## Core Commands

### Primary Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `*init-parallel-draft` | Create worktrees for parallel Draft | Phase 4.1 |
| `*init-parallel-develop` | Create worktrees for parallel Develop | Phase 4.2 |
| `*analyze-dependencies` | Analyze affected_files for conflicts | Phase 4.2 |
| `*wait-phase` | Wait for all worktrees to complete phase | Phase 4.1/4.2 |
| `*merge-all` | Merge all worktrees back to main | Phase 4.3 |
| `*init-parallel-qa` | Initialize grouped QA sessions | Phase 4.3 |
| `*finalize-sprint` | Complete sprint and cleanup | Phase 4.3 |
| `*status` | Show parallel development status | Any |

### Advanced Commands

| Command | Description |
|---------|-------------|
| `*cleanup-worktrees` | Remove all parallel worktrees |
| `*retry-story [ID]` | Retry failed story in new worktree |
| `*pause-all` | Pause all parallel sessions |
| `*export-logs` | Export all session logs |

---

## Complete Workflow

### Phase 4.1: Sprint Planning + Parallel Draft

```bash
# Step 1: Sprint planning in main worktree
@sm *sprint-planning
→ Determine Stories for this Sprint: 13.1-13.8

# Step 2: Initialize parallel Draft
@parallel-dev-orchestrator *init-parallel-draft "13.1,13.2,13.3,13.4,13.5,13.6,13.7,13.8"

Orchestrator:
✅ Created 8 Draft worktrees:
   - ../Canvas-draft-13.1
   - ../Canvas-draft-13.2
   - ... (8 total)
✅ Each worktree has independent context

📋 Launch Commands (run in separate terminals):
   [Tab 1] cd ../Canvas-draft-13.1 && claude @sm *draft Story-13.1
   [Tab 2] cd ../Canvas-draft-13.2 && claude @sm *draft Story-13.2
   ... (8 tabs)

# Step 3: Wait for all Drafts to complete
@parallel-dev-orchestrator *wait-phase "draft"

Orchestrator:
⏳ Waiting for 8 Drafts...
   ✅ 13.1 - Story file created
   ✅ 13.2 - Story file created
   ...
✅ All Drafts complete!

# Step 4: User adds affected_files to each Story
# Edit story-13.X.md to add:
#   affected_files:
#     - src/canvas_utils.py
#     - src/agents/scoring.py
```

### Phase 4.2: Dependency Analysis + Parallel Develop

```bash
# Step 5: Analyze dependencies
@parallel-dev-orchestrator *analyze-dependencies

Orchestrator:
⏳ Reading affected_files from all Stories...

📊 Dependency Analysis:
   ✅ No conflict: 13.1, 13.2, 13.4, 13.5, 13.7, 13.8
   ⚠️  Conflict detected:
      - 13.3 and 13.6 both modify: src/canvas_utils.py

Recommendation: Move 13.6 to next batch

# Step 6: User decides to proceed with 7 Stories
User: "移除13.6，继续"

# Step 7: Initialize parallel Develop
@parallel-dev-orchestrator *init-parallel-develop "13.1,13.2,13.3,13.4,13.5,13.7,13.8"

Orchestrator:
✅ Created 7 Develop worktrees:
   - ../Canvas-13.1
   - ../Canvas-13.2
   - ... (7 total)
✅ Copied .ai-context.md to each worktree
✅ Each worktree has independent status file

📋 Launch Commands:
   [Tab 1] cd ../Canvas-13.1 && claude @dev *develop-story Story-13.1
   [Tab 2] cd ../Canvas-13.2 && claude @dev *develop-story Story-13.2
   ... (7 tabs)

# Step 8: Wait for all Develop to complete
@parallel-dev-orchestrator *wait-phase "develop"

Orchestrator:
⏳ Waiting for 7 Developments...
   ✅ 13.1 - dev-complete (tests passed)
   ✅ 13.2 - dev-complete (tests passed)
   ⏳ 13.3 - in-progress...
   ...
✅ All Developments complete!
```

### Phase 4.3: Merge + Grouped QA

```bash
# Step 9: Merge all worktrees
@parallel-dev-orchestrator *merge-all

Orchestrator:
⏳ Merging worktrees...
   ✅ Merged ../Canvas-13.1
   ✅ Merged ../Canvas-13.2
   ⚠️  Conflict in ../Canvas-13.3 (auto-resolved)
   ...
✅ All 7 worktrees merged!
✅ Status files synchronized

# Step 10: Handle any merge conflicts
If conflicts exist:
  @sm *correct-course "Merge conflict: 13.3 and 13.7 both modified..."
  → User resolves Git conflicts manually

# Step 11: Initialize grouped QA
@parallel-dev-orchestrator *init-parallel-qa "group1:13.1,13.2,13.3|group2:13.4,13.5|group3:13.7,13.8"

Orchestrator:
✅ Created 3 QA groups:
   - Group 1: 13.1, 13.2, 13.3 (3 stories)
   - Group 2: 13.4, 13.5 (2 stories)
   - Group 3: 13.7, 13.8 (2 stories)

📋 Launch Commands:
   [Tab 1] claude @qa *review Story-13.1 && @qa *review Story-13.2 && @qa *review Story-13.3
   [Tab 2] claude @qa *review Story-13.4 && @qa *review Story-13.5
   [Tab 3] claude @qa *review Story-13.7 && @qa *review Story-13.8

# Step 12: Quality Gates
[Tab 1] @qa *gate Story-13.1 && @qa *gate Story-13.2 && @qa *gate Story-13.3
[Tab 2] @qa *gate Story-13.4 && @qa *gate Story-13.5
[Tab 3] @qa *gate Story-13.7 && @qa *gate Story-13.8

# Step 13: Finalize Sprint
@parallel-dev-orchestrator *finalize-sprint

Orchestrator:
✅ Updated canvas-project-status.yaml
   - 13.1: completed
   - 13.2: completed
   - ... (7 stories)
✅ Cleaned up worktrees
✅ Created Git tag: sprint-13-complete

🎉 Sprint 13 Complete!
   - Stories completed: 7
   - Stories deferred: 1 (13.6)
   - Total development time: [X hours]
```

---

## State Management

### Orchestrator State File

Location: `.bmad-core/parallel-dev/orchestrator-state.json`

```json
{
  "sprint": 13,
  "phase": "develop",
  "total_stories": 8,
  "active_stories": 7,
  "deferred_stories": ["13.6"],
  "worktrees": {
    "13.1": {
      "path": "../Canvas-13.1",
      "status": "dev-complete",
      "started_at": "2025-11-20T10:00:00Z",
      "completed_at": "2025-11-20T11:30:00Z"
    },
    "13.2": {
      "path": "../Canvas-13.2",
      "status": "in-progress",
      "started_at": "2025-11-20T10:00:00Z"
    }
  },
  "qa_groups": [
    {"id": 1, "stories": ["13.1", "13.2", "13.3"]},
    {"id": 2, "stories": ["13.4", "13.5"]},
    {"id": 3, "stories": ["13.7", "13.8"]}
  ],
  "conflicts_detected": [],
  "merge_completed": false
}
```

### Worktree Status File

Each worktree has: `.worktree-status.yaml`

```yaml
story: "13.1"
status: "dev-complete"
started_at: "2025-11-20T10:00:00Z"
completed_at: "2025-11-20T11:30:00Z"
affected_files:
  - src/canvas_utils.py
  - src/agents/example_teaching.py
tests_passed: true
test_count: 15
test_failures: 0
```

---

## Integration Points

### With SM Agent (@sm)

```
Parallel Dev Orchestrator → @sm *draft Story-X (in worktree)
                          ↓
                     Wait for completion
                          ↓
                     Validate Story file exists
```

### With Dev Agent (@dev)

```
Parallel Dev Orchestrator → @dev *develop-story (in worktree)
                          ↓
                     Monitor progress
                          ↓
                     Detect dev-complete status
```

### With QA Agent (@qa)

```
Parallel Dev Orchestrator → @qa *review (grouped)
                          ↓
                     @qa *gate (quality decision)
                          ↓
                     Update status
```

### With Existing *correct-course

When merge conflicts occur:
```bash
@sm *correct-course "Merge conflict between Story 13.3 and 13.7"
→ Generates sprint-change-proposal.md
→ User resolves manually
```

---

## Dependency Analysis Logic

### Conflict Detection

```python
# Pseudo-code for analyze-dependencies
def analyze_dependencies(stories):
    file_map = {}
    conflicts = []

    for story in stories:
        affected_files = read_story_affected_files(story)
        for file in affected_files:
            if file in file_map:
                conflicts.append({
                    "file": file,
                    "stories": [file_map[file], story]
                })
            else:
                file_map[file] = story

    return conflicts
```

### Conflict Resolution Options

1. **Defer Story**: Move conflicting story to next batch
2. **Sequential Develop**: Develop conflicting stories one after another
3. **Manual Merge**: Allow conflicts, resolve during merge

---

## .ai-context.md Template

Created for each worktree:

```markdown
# Worktree Context

## Story Information
- **Story ID**: 13.1
- **Epic**: Epic 13 - Advanced Features
- **Sprint**: 13

## File Scope
- **Affected Files** (can modify):
  - src/canvas_utils.py
  - src/agents/example_teaching.py

- **Read-Only Files** (DO NOT modify):
  - specs/api/*.yml
  - specs/data/*.json
  - canvas-project-status.yaml

## Session Guidelines
1. Only modify files listed in "Affected Files"
2. Run tests before marking dev-complete
3. Update .worktree-status.yaml when complete
4. Do NOT push directly - orchestrator handles merge

## Status Commands
- Check status: cat .worktree-status.yaml
- Mark complete: Update status to "dev-complete"
```

---

## PowerShell Scripts

### Scripts to Create

| Script | Purpose |
|--------|---------|
| `init-worktrees.ps1` | Create multiple Git worktrees |
| `merge-worktrees.ps1` | Merge worktrees back to main |
| `cleanup-worktrees.ps1` | Remove all worktrees |
| `check-worktree-status.ps1` | Check status of all worktrees |
| `analyze-dependencies.ps1` | Parse affected_files for conflicts |

### Example: init-worktrees.ps1

```powershell
param(
    [string]$Stories,  # "13.1,13.2,13.3"
    [string]$Phase = "develop"  # "draft" or "develop"
)

$storyList = $Stories -split ","

foreach ($story in $storyList) {
    $worktreePath = "../Canvas-$Phase-$story"

    # Create worktree
    git worktree add $worktreePath -b "story-$story"

    # Copy context file
    Copy-Item ".ai-context-template.md" "$worktreePath/.ai-context.md"

    # Create status file
    @"
story: "$story"
status: "pending"
started_at: "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
"@ | Out-File "$worktreePath/.worktree-status.yaml" -Encoding utf8

    Write-Host "✅ Created worktree: $worktreePath"
}
```

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Worktree exists | Previous run not cleaned | Run `*cleanup-worktrees` |
| Merge conflict | Multiple stories modified same file | Use `*correct-course` |
| Story not found | affected_files not added | Add affected_files to story |
| Tests failed | Code issues | Fix in worktree, re-run tests |

### Recovery Commands

```bash
# Recover from failed merge
@parallel-dev-orchestrator *retry-merge "13.3"

# Rollback specific worktree
@parallel-dev-orchestrator *rollback-worktree "13.3"

# Force cleanup all
@parallel-dev-orchestrator *cleanup-worktrees --force
```

---

## Best Practices

### For Parallel Development

1. **Always analyze dependencies first**: Prevent merge nightmares
2. **Add affected_files to every Story**: Enable conflict detection
3. **Use batches of 4**: Balance parallelism and resource usage
4. **Run tests in each worktree**: Catch issues early
5. **Don't push from worktrees**: Let orchestrator handle merging

### For Code Consistency

1. **devLoadAlwaysFiles is your friend**: All sessions load same standards
2. **Review merged code**: Check for style inconsistencies
3. **Use consistent naming**: Follow project conventions
4. **Document decisions**: Comment non-obvious code

### For Resource Management

1. **Close unused terminals**: Free up memory
2. **Clean up worktrees after sprint**: Avoid disk bloat
3. **Monitor API rate limits**: Multiple sessions consume quota

---

## Configuration

Location: `.bmad-core/parallel-dev-config.yaml`

```yaml
parallel_dev:
  version: 1.0.0

  defaults:
    max_concurrent: 8
    batch_size: 4
    qa_groups: 3

  worktree:
    base_path: ".."
    naming_pattern: "Canvas-{phase}-{story}"
    cleanup_on_finalize: true

  dependencies:
    analyze_before_develop: true
    block_on_conflict: false
    allow_manual_resolution: true

  merge:
    strategy: "recursive"
    auto_resolve: true
    fail_on_conflict: false

  status:
    use_independent_files: true
    sync_on_merge: true

  notifications:
    show_progress: true
    warn_on_conflict: true
```

---

## Related Documentation

- **Planning Orchestrator**: `@planning-orchestrator` (Phase 2)
- **SM Agent**: `@sm` (Sprint management)
- **Dev Agent**: `@dev` (Development)
- **QA Agent**: `@qa` (Quality assurance)
- **BMad Core Config**: `.bmad-core/core-config.yaml`

---

**Last Updated**: 2025-11-20
**Maintainer**: Canvas Learning System Team
