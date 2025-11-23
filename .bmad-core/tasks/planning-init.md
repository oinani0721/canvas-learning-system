# Task: planning-init

## Purpose
Initialize a new Planning iteration with snapshot of current state.

## Prerequisites
- Git repository clean (no uncommitted changes)
- Previous iteration finalized (if exists)

## Steps

### 1. Pre-flight Checks
```bash
# Check git status
git status --porcelain

# If dirty, abort with message
```

### 2. Create Iteration Snapshot
```bash
# Run Python script for complex snapshot logic
python scripts/init-iteration.py --iteration {N} --goal "{goal}"
```

The script will:
- Create `iterations/iteration-{N}.json` with:
  - PRD file hashes
  - Architecture file hashes
  - OpenAPI spec versions
  - JSON Schema versions
  - Timestamp

### 3. Create Git Branch
```bash
git checkout -b planning-iteration-{N}
```

### 4. Output
```markdown
✅ Iteration {N} Initialized
   └─ Snapshot: iterations/iteration-{N}.json
   └─ Branch: planning-iteration-{N}
   └─ Goal: {goal}

📋 Ready for Planning changes
```

## Error Handling
- If git dirty: "Please commit or stash changes before starting new iteration"
- If previous iteration not finalized: "Please finalize iteration {N-1} first"
