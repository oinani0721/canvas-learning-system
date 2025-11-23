# Planning Iteration Conversation Template

**Version**: 1.0.0
**Last Updated**: 2025-11-19
**Purpose**: Standard conversation template for BMad Phase 2 (Planning) iteration management

---

## Template: Planning Iteration N - [Goal]

### Pre-Iteration Checklist
Before starting, complete these items:
- [ ] Review current document versions (PRD, Architecture, API specs)
- [ ] Identify affected Epics/Components
- [ ] Backup critical files (auto-done by system)
- [ ] Define clear iteration goal

---

### Step 1: Initialize Iteration

```
@planning-orchestrator "Start iteration [N] for [brief goal description]"
```

**Example**:
```
@planning-orchestrator "Start iteration 4 for Epic 13 - Ebbinghaus Review System"
```

**Expected Response**:
- ✅ Snapshot created
- ✅ OpenAPI specs backed up
- 📋 Pre-iteration checklist generated

---

### Step 2: Planning Modifications

```
@pm *correct course "[detailed changes]"
```

**Example**:
```
@pm *correct course "Add Epic 13 - Ebbinghaus Review System:
- Add to PRD: FR-13.1 (Review Scheduling), FR-13.2 (Forgetting Curve)
- Update Architecture: Add Review Engine component
- Add API endpoints: /api/reviews/schedule, /api/reviews/due
- Create Epic 13 document with 4 Stories"
```

**Expected Response**:
- ✅ PRD updated (version incremented)
- ✅ Architecture updated (version incremented)
- ✅ API spec updated (version incremented)
- ✅ Epic document created

---

### Step 3: Validate Changes

**Option A**: Auto-validation (orchestrator handles it)
```
@planning-orchestrator "Validate current iteration"
```

**Option B**: Manual validation
```
@iteration-validator "Validate current changes against iteration [N-1]"
```

**Expected Response**:
- Validation report with:
  - ✅ Breaking changes (if any)
  - ⚠️ Warnings
  - ℹ️ Info changes

---

### Step 4: Resolve Issues (If Needed)

#### If Breaking Changes Detected:

**Option A**: Fix issues
```
[Fix the issues in source files]
@planning-orchestrator "Validate current iteration"
```

**Option B**: Accept breaking changes
```
@planning-orchestrator "Finalize iteration [N], accept breaking changes"
```

**Option C**: Rollback
```
@planning-orchestrator "Rollback to iteration [N-1]"
```

---

### Step 5: Finalize Iteration

```
@planning-orchestrator "Finalize iteration [N]"
```

**Expected Response**:
- ✅ Final snapshot created
- ✅ Git tag created: `planning-v[N]`
- ✅ iteration-log.md updated
- 📋 Post-iteration checklist generated

---

### Step 6: Git Commit

```bash
git add .
git commit -m "Planning Iteration [N]: [Goal]"
git push origin main --tags
```

---

### Post-Iteration Checklist
After completing:
- [ ] Review validation report
- [ ] Update CHANGELOG.md (if API changed)
- [ ] Notify stakeholders (if breaking changes)
- [ ] Document any deferred items
- [ ] Plan next iteration (if needed)

---

## Quick Reference Commands

### Planning Orchestrator
| Action | Command |
|--------|---------|
| Start iteration | `@planning-orchestrator "Start iteration N for [goal]"` |
| Validate | `@planning-orchestrator "Validate current iteration"` |
| Finalize | `@planning-orchestrator "Finalize iteration N"` |
| Status | `@planning-orchestrator "Status report"` |
| Rollback | `@planning-orchestrator "Rollback to iteration N"` |
| Compare | `@planning-orchestrator "Compare iterations M and N"` |

### Iteration Validator
| Action | Command |
|--------|---------|
| Initialize | `@iteration-validator "Initialize Iteration N"` |
| Validate | `@iteration-validator "Validate current changes"` |
| Finalize + Breaking | `@iteration-validator "Finalize Iteration N, accept breaking changes"` |
| OpenAPI Diff | `@iteration-validator "Compare agent-api v1.0.0 vs current"` |

### PM Agent (Planning Modifications)
| Action | Command |
|--------|---------|
| Create PRD | `@pm "Create PRD for [project]"` |
| Correct Course | `@pm *correct course "[changes]"` |
| Add Epic | `@pm *correct course "Add Epic N: [name]"` |

---

## Common Scenarios

### Scenario 1: First PRD Creation
```
@planning-orchestrator "Start iteration 1 for initial Planning"
@pm "Create comprehensive PRD for Canvas Learning System"
@planning-orchestrator "Finalize iteration 1"
```

### Scenario 2: Add New Epic
```
@planning-orchestrator "Start iteration 4 for Epic 13"
@pm *correct course "Add Epic 13 - Ebbinghaus Review System"
@planning-orchestrator "Finalize iteration 4"
```

### Scenario 3: Breaking API Change
```
@planning-orchestrator "Start iteration 5 for API v2.0"
@pm *correct course "Remove deprecated /api/cache endpoint"
# Validation will detect breaking change
@planning-orchestrator "Finalize iteration 5, accept breaking changes"
# API version auto-incremented to v2.0.0
```

### Scenario 4: Emergency Rollback
```
@planning-orchestrator "Status report"
# Review current state
@planning-orchestrator "Rollback to iteration 3"
# All changes since iteration 3 are reverted
```

---

## Notes

- **All iterations are versioned**: Snapshots in `.bmad-core/planning-iterations/snapshots/`
- **Git tags track iterations**: `planning-v1`, `planning-v2`, etc.
- **Breaking changes require explicit acceptance**: Safety mechanism
- **Pre-commit hook validates**: Cannot accidentally commit breaking changes
- **Helper System is Phase 4**: Do NOT use `@helpers.md` in Phase 2 Planning

---

**Template End**
