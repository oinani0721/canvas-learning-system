# Task: planning-finalize

## Purpose
Complete the current iteration with Git tag and version bump.

## Prerequisites
- Validation passed (or --accept-breaking flag)
- All changes committed

## Steps

### 1. SDD Coverage Quality Gate ⚠️ CRITICAL

**Run SDD Coverage Check**:
```bash
python scripts/extract-sdd-requirements.py
```

**Read Coverage Report**:
```bash
Read: docs/specs/sdd-requirements-index.md
```

**Extract Coverage Percentage** from "覆盖率总览" table → "**总体**" row → "覆盖率" column.

**Quality Gate Decision**:

| Coverage | Status | Action |
|----------|--------|--------|
| ≥ 80% | ✅ PASS | Proceed to Step 2 |
| < 80% | ❌ FAIL | **HALT** - Cannot finalize |

**If Coverage < 80%**:
```markdown
❌ SDD Coverage Quality Gate Failed!

Current Coverage: {percentage}%
Required: ≥80%

Missing Items:
  - {count} OpenAPI endpoints
  - {count} JSON Schemas

❌ Cannot finalize iteration until SDD coverage ≥80%

🔧 Actions Required:
   1. Run: @architect *verify-sdd-coverage
   2. Supplement missing SDD specs:
      - @architect *create-openapi (for missing endpoints)
      - @architect *create-schemas (for missing models)
   3. Re-run: *validate
   4. Re-run: *finalize

⚠️ To override (NOT recommended): *finalize --skip-sdd-check
```

**If Coverage ≥ 80%**: Proceed to next step.

---

### 2. Final Validation
```bash
python scripts/validate-iteration.py --iteration {N} --final
```

### 3. Version Determination

Based on changes:
- **MAJOR**: Breaking API/Schema changes → v2.0.0
- **MINOR**: New features, non-breaking → v1.1.0
- **PATCH**: Documentation, fixes → v1.0.1

### 4. Update Version Files
```bash
python scripts/finalize-iteration.py --iteration {N} --version {version}
```

Updates:
- `iterations/iteration-{N}.json` → status: "finalized"
- `CHANGELOG.md` → Add entry
- `.bmad-core/data/canvas-project-status.yaml` → Update status

### 5. Git Operations
```bash
# Commit finalization
git add -A
git commit -m "Finalize Planning Iteration {N}: {goal}"

# Create tag
git tag planning-v{N}

# Merge to main (if on branch)
git checkout main
git merge planning-iteration-{N}
```

### 6. Output

#### Standard Finalization
```markdown
✅ Iteration {N} Finalized
   └─ Version: v1.2.0 (MINOR)
   └─ Git tag: planning-v{N}
   └─ CHANGELOG updated

🎉 Planning Phase Complete!
   Ready for Phase 3 (Architecture) or Phase 4 (Implementation)
```

#### With Breaking Changes
```markdown
⚠️ Iteration {N} Finalized with Breaking Changes
   └─ Version: v2.0.0 (MAJOR)
   └─ Git tag: planning-v{N}-BREAKING

⚠️ REQUIRED ACTIONS:
   1. Document migration path in CHANGELOG.md
   2. Notify all stakeholders
   3. Update consumer applications
```

## Flags
- `--accept-breaking`: Accept breaking changes without re-validation
- `--version {x.y.z}`: Override automatic version
- `--skip-sdd-check`: ⚠️ Skip SDD coverage quality gate (NOT recommended)

## Error Handling
- If uncommitted changes: "Please commit all changes before finalizing"
- If validation failed: "Validation failed. Fix issues or use --accept-breaking"
