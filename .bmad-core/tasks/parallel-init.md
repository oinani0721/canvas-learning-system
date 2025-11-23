# Task: parallel-init

## Purpose
Create Git worktrees for parallel Story development.

## Input
- Story IDs to parallelize: "13.1, 13.2, 13.4"

## Prerequisites
- Stories analyzed with `*analyze`
- No conflicting Stories in the list
- Git repository clean

## Steps

### 1. Validate No Conflicts
```bash
python scripts/validate-parallel-stories.py --stories "13.1,13.2,13.4"
```

### 2. Create Worktrees
```bash
# For each Story
for story_id in stories:
    # Create branch
    git branch develop-story-{story_id}

    # Create worktree
    git worktree add ../Canvas-develop-{story_id} develop-story-{story_id}
```

### 3. Setup Each Worktree

For each worktree, create context files:

**.ai-context.md**:
```markdown
# Worktree Context: Story {story_id}

## Active Story
- **ID**: {story_id}
- **Title**: {story_title}
- **Epic**: {epic_number}

## Complete Workflow (Dev + QA)

### Phase 1: Development
1. `/dev` - Activate Developer Agent
2. `*develop-story {story_id}` - Implement the Story
3. `*run-tests` - Run all tests

### Phase 2: Quality Review
4. `/qa` - Activate QA Agent
5. `*review {story_id}` - Code review
6. `*gate {story_id}` - Quality gate decision

### Phase 3: Ready to Merge
7. If gate = PASS, Story is ready
8. Return to main repo and run `*merge {story_id}`

## Story Location
docs/stories/story-{story_id}.md

## Related Files
{list of files from Story}

## Important
- Complete BOTH Dev and QA before marking ready
- Update .worktree-status.yaml after each phase

## Automation Mode
If launched via `parallel-develop-auto.ps1`, this session runs in non-interactive mode.
The prompt will guide you through the complete Dev+QA workflow automatically.
Output is logged to: dev-qa-output.log
```

**.worktree-status.yaml**:
```yaml
story_id: "{story_id}"
status: "initialized"  # initialized → in-progress → dev-complete → qa-reviewing → ready-to-merge
created: "{timestamp}"
tests_run: false
tests_passed: false
qa_reviewed: false
qa_gate: null  # PASS / CONCERNS / FAIL / WAIVED
```

### 4. Output

```markdown
## Worktrees Created

| Worktree | Story | Branch | Path |
|----------|-------|--------|------|
| Canvas-develop-13.1 | 13.1 | develop-story-13.1 | C:\Users\ROG\托福\Canvas-develop-13.1 |
| Canvas-develop-13.2 | 13.2 | develop-story-13.2 | C:\Users\ROG\托福\Canvas-develop-13.2 |
| Canvas-develop-13.4 | 13.4 | develop-story-13.4 | C:\Users\ROG\托福\Canvas-develop-13.4 |

## Launch Parallel Sessions

### Option 1: Full Automation (Recommended)

Run this command to launch all sessions with automatic Dev+QA workflow:

```powershell
.\scripts\parallel-develop-auto.ps1 -Stories 13.1,13.2,13.4
```

Each session will automatically:
1. /dev *develop-story → *run-tests
2. /qa *review → *gate
3. Update .worktree-status.yaml

### Option 2: Manual Interactive

Open each worktree in a new Claude Code window:

```bash
# Window 1
cd "C:\Users\ROG\托福\Canvas-develop-13.1"
claude

# Window 2
cd "C:\Users\ROG\托福\Canvas-develop-13.2"
claude

# Window 3
cd "C:\Users\ROG\托福\Canvas-develop-13.4"
claude
```

In each window, follow .ai-context.md for Dev+QA workflow.

## Monitoring

- Check progress: `*status`
- View logs: `Canvas-develop-{story}/dev-qa-output.log`
- Merge when ready: `*merge --all`
```

## Error Handling
- If conflict detected: "Cannot parallelize - {story_a} and {story_b} conflict on {file}"
- If worktree exists: "Worktree for {story_id} already exists"
