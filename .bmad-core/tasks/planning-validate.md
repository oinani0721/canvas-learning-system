# Task: planning-validate

## Purpose
Validate current Planning changes, including SDD spec checks for breaking changes.

## Prerequisites
- Active iteration initialized
- Changes made to PRD/Architecture/Specs

## Steps

### 1. Run Validation Script
```bash
python scripts/validate-iteration.py --iteration {N}
```

### 2. Validation Checks

#### 2.1 PRD Validation
- Check all Epic files exist
- Verify Story references valid
- Check for orphaned Stories

#### 2.2 Architecture Validation
- Verify architecture files complete
- Check ADR references

#### 2.3 SDD Validation (Breaking Changes)

**OpenAPI Specs** (`specs/api/*.yml`):
```bash
python scripts/diff-openapi.py --base iterations/iteration-{N}.json --current specs/api/
```

Breaking changes detected:
- Endpoint deleted
- Required parameter added
- Response field removed
- HTTP method changed

**JSON Schemas** (`specs/data/*.json`):
```bash
python scripts/diff-schemas.py --base iterations/iteration-{N}.json --current specs/data/
```

Breaking changes detected:
- Required field added
- Field type changed
- Enum value removed
- Field deleted

**Gherkin Specs** (`specs/behavior/*.feature`):
- Scenario removed
- Given/When/Then step deleted

### 3. Output

#### No Breaking Changes
```markdown
✅ Validation Passed
   └─ PRD: 3 Epics validated
   └─ Architecture: Complete
   └─ OpenAPI: No breaking changes
   └─ Schemas: Compatible

⚠️ Suggestions:
   - Update CHANGELOG.md with changes
```

#### Breaking Changes Detected
```markdown
❌ Breaking Changes Detected!

OpenAPI Breaking Changes:
  - DELETE /api/cache/{id} removed
  - POST /api/nodes: required field 'position' added

Schema Breaking Changes:
  - CanvasNode: required field 'metadata' added

Options:
  A. Fix issues and re-validate
  B. Accept: *finalize --accept-breaking
  C. Rollback: *rollback
```

## Error Handling
- If no active iteration: "No active iteration. Run *init first"
- If validation script fails: Show error details
