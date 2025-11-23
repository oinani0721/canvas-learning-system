# Task: parallel-analyze

## Purpose
Analyze Story dependencies to identify which can be safely developed in parallel.

## Input
- List of Story IDs: "13.1, 13.2, 13.3, 13.4"

## Steps

### 1. Load Story Files
```bash
# Read each Story from docs/stories/
for story_id in stories:
    read docs/stories/story-{story_id}.md
```

### 2. Extract File Dependencies
Parse each Story's "Files to Modify" or "Technical Notes" section to identify:
- Source files to modify
- Test files to create/modify
- Config files to update

### 3. Build Conflict Matrix
```bash
python scripts/analyze-story-conflicts.py --stories "13.1,13.2,13.3,13.4"
```

### 4. Output

```markdown
## Story Dependency Analysis

### File Modification Map

| Story | Files to Modify |
|-------|-----------------|
| 13.1 | src/review_engine.py, tests/test_review.py |
| 13.2 | src/scheduler.py, tests/test_scheduler.py |
| 13.3 | src/review_engine.py, src/canvas_utils.py |
| 13.4 | src/memory_service.py, tests/test_memory.py |

### Conflict Detection

| Story A | Story B | Conflicting Files | Can Parallelize? |
|---------|---------|-------------------|------------------|
| 13.1 | 13.2 | None | ✅ Yes |
| 13.1 | 13.3 | src/review_engine.py | ❌ No |
| 13.1 | 13.4 | None | ✅ Yes |
| 13.2 | 13.3 | None | ✅ Yes |
| 13.2 | 13.4 | None | ✅ Yes |
| 13.3 | 13.4 | None | ✅ Yes |

### Recommended Parallel Groups

**Option A** (Max parallelism: 3):
- Group 1: 13.1, 13.2, 13.4 (parallel)
- Group 2: 13.3 (after 13.1 completes)

**Option B** (Max parallelism: 2):
- Group 1: 13.2, 13.3, 13.4 (parallel)
- Group 2: 13.1 (after 13.3 completes)

### Recommendation
Use Option A for maximum throughput.

Ready to proceed? Run: `*init "13.1, 13.2, 13.4"`
```

## Error Handling
- If Story file not found: "Story {id} not found in docs/stories/"
- If no file dependencies listed: "Story {id} missing 'Files to Modify' section"
