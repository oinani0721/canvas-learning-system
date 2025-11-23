# Task: planning-compare

## Purpose
Compare changes between two iterations or current state vs iteration.

## Prerequisites
- At least one finalized iteration exists

## Steps

### 1. Determine Comparison Targets
- `*compare {M} {N}`: Compare iteration M to iteration N
- `*compare {M}`: Compare iteration M to current state

### 2. Generate Diff Report
```bash
python scripts/compare-iterations.py --from {M} --to {N|current}
```

### 3. Output Report

```markdown
## Iteration Comparison: {M} → {N}

### Summary
- PRD Changes: 3 files modified
- Architecture Changes: 1 file added
- API Changes: 2 endpoints added
- Schema Changes: 1 field added

### PRD Changes

#### docs/prd/epic-13-ebbinghaus.md
```diff
+ ## Story 13.5: Adaptive Review Scheduling
+ As a learner, I want adaptive scheduling...
```

### Architecture Changes

#### docs/architecture/coding-standards.md
```diff
- max_line_length: 100
+ max_line_length: 120
```

### API Changes (OpenAPI)

| Change | Type | Details |
|--------|------|---------|
| POST /api/review/schedule | Added | New endpoint for review scheduling |
| GET /api/review/stats | Added | Review statistics endpoint |

### Schema Changes (JSON Schema)

| Schema | Field | Change |
|--------|-------|--------|
| ReviewSession | adaptiveWeight | Added (optional) |

### Breaking Changes
None detected ✅
```

## Flags
- `--format {markdown|json}`: Output format
- `--output {file}`: Save to file instead of display

## Error Handling
- If iteration not found: "Iteration {M} not found"
- If no iterations exist: "No finalized iterations. Run *init and *finalize first"
