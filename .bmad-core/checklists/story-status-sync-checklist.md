<!-- Powered by BMAD™ Core -->

# Story Status Synchronization Checklist

## Purpose

This checklist ensures Story status is properly synchronized between:
1. Story file (`docs/stories/*.story.md`) - Status field
2. Project status YAML (`canvas-project-status.yaml`) - Story tracking

**Root Cause Reference**: BMad Issue #1015 - Workflow lacks automatic status sync step

---

## Instructions for Developer Agent

[[LLM: CRITICAL STATUS SYNC INSTRUCTIONS

This checklist addresses a known BMad workflow gap (Issue #1015).
After completing development work, you MUST manually update status in TWO locations.

EXECUTION APPROACH:
1. Complete all development tasks first
2. Update Story file Status field to new status
3. Update canvas-project-status.yaml to match
4. Verify both files are consistent
5. Commit both files together

Failure to sync status causes tracking discrepancies and confusion.]]

---

## Pre-Completion Status Sync Checklist

### 1. Code Completion

- [ ] All assigned tasks in Story file completed
- [ ] Local tests pass (`pytest` / `npm test`)
- [ ] Build succeeds without errors

### 2. Story File Status Update ⚠️ CRITICAL

**Location**: `docs/stories/{story-id}.story.md`

- [ ] Story file `## Status` section updated to new status
- [ ] Status uses **kebab-case** format (see table below)
- [ ] `LastUpdated` timestamp updated
- [ ] `UpdatedBy` field set to agent name

**Standard Status Values (kebab-case)**:

| Status | Meaning |
|--------|---------|
| `draft` | Story being written |
| `ready-for-dev` | Approved, ready for development |
| `in-progress` | Active development |
| `ready-for-review` | Dev complete, awaiting QA |
| `in-review` | QA actively reviewing |
| `done` | QA approved, story complete |
| `blocked` | Waiting on dependency |

**Example Format**:
```markdown
## Status

status: ready-for-review
last_updated: 2026-01-17T12:00:00Z
updated_by: dev-agent
```

### 3. Project Status YAML Update ⚠️ CRITICAL

**Location**: `.bmad-core/data/canvas-project-status.yaml`

- [ ] Find story entry in YAML file
- [ ] Update `status` field to match Story file
- [ ] Update `updated` timestamp

### 4. Change Log Update

- [ ] Story file Change Log section updated with entry
- [ ] Entry includes: Date, Version, Description, Author

### 5. Commit Both Files Together

- [ ] `git add` both Story file and YAML file
- [ ] Commit message: `chore: update story status [Story-ID] → {new-status}`

---

## Final Verification

[[LLM: FINAL SYNC VERIFICATION

Before marking this checklist complete:

1. Re-read Story file Status section - confirm it shows correct status
2. Re-read canvas-project-status.yaml - confirm status matches
3. Run: `git diff --name-only` to verify both files are staged
4. Verify no other stories accidentally modified

If statuses don't match, FIX IMMEDIATELY before proceeding.]]

- [ ] Story file Status and YAML status are **identical**
- [ ] Both files committed to git

---

## Quick Reference Commands

```powershell
# Check Story status
Select-String -Path "docs/stories/*.story.md" -Pattern "status:" | Select-Object -First 10

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.bmad-core/data/canvas-project-status.yaml'))"

# Commit both files
git add docs/stories/{story-id}.story.md .bmad-core/data/canvas-project-status.yaml
git commit -m "chore: update story status [Story-ID] → ready-for-review"
```

---

## Related Resources

- BMad Issue #1015: https://github.com/bmad-sim/bmad/issues/1015
- BMad Issue #1105: Status naming consistency
- Plan file: `.claude/plans/shimmying-moseying-lecun.md`
