# Task: planning-finalize

## Purpose
Complete the current iteration with Git tag and version bump.

## Prerequisites
- Validation passed (or --accept-breaking flag)
- All changes committed

## Steps

### 1. Final Validation
```bash
python scripts/validate-iteration.py --iteration {N} --final
```

### 2. Version Determination

Based on changes:
- **MAJOR**: Breaking API/Schema changes → v2.0.0
- **MINOR**: New features, non-breaking → v1.1.0
- **PATCH**: Documentation, fixes → v1.0.1

### 3. Update Version Files
```bash
python scripts/finalize-iteration.py --iteration {N} --version {version}
```

Updates:
- `iterations/iteration-{N}.json` → status: "finalized"
- `CHANGELOG.md` → Add entry
- `.bmad-core/data/canvas-project-status.yaml` → Update status

### 4. Git Operations
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

### 5. Output

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

## Error Handling
- If uncommitted changes: "Please commit all changes before finalizing"
- If validation failed: "Validation failed. Fix issues or use --accept-breaking"
