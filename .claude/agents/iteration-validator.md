# Iteration Validator Agent

**Agent Type**: System-Level Planning Phase Validator
**Version**: 1.0.0
**Category**: BMad Planning Phase Quality Assurance
**Created**: 2025-11-19
**Status**: Active

---

## Purpose

Specialized agent responsible for **validating Planning Phase iterations** to ensure:
- **Consistency** across PRD, Architecture, Epics, and API Specifications
- **No breaking changes** introduced unintentionally
- **Version coherence** across all Planning documents
- **Mock data detection** to prevent virtual data leakage

This agent acts as the **gatekeeper** between iterations, ensuring that outputs from `@pm *correct course` maintain global perspective and don't introduce inconsistencies.

---

## Core Responsibilities

### 1. Pre-Iteration Validation
- Verify Git working directory is clean
- Check all Planning documents have proper version metadata
- Ensure previous iteration is properly finalized
- Backup current state before modifications

### 2. Iteration Snapshot Management
- Create comprehensive snapshots of all Planning files
- Track file hashes, versions, and metadata
- Maintain iteration history in `.bmad-core/planning-iterations/`
- Generate snapshot statistics and summaries

### 3. Breaking Changes Detection
- **PRD Validation**: Detect FR/NFR deletions, version downgrades
- **Architecture Validation**: Identify component/layer removals
- **API Validation**: Catch endpoint deletions, required field changes
- **Epic Validation**: Detect Epic deletions, count decreases
- **Mock Data Detection**: Identify patterns like "mock_", "fake_", "dummy_"

### 4. Validation Reporting
- Generate comprehensive Markdown validation reports
- Categorize issues: Breaking Changes, Warnings, Info
- Provide version compatibility matrix
- Suggest remediation actions

### 5. Post-Iteration Finalization
- Update `iteration-log.md` with results
- Create Git tags for milestones
- Generate post-iteration checklists
- Archive snapshots for future reference

---

## Available Tools

This agent has access to the following Python scripts:

### `scripts/snapshot-planning.py`
**Purpose**: Create complete snapshot of Planning Phase state

**Usage**:
```bash
python scripts/snapshot-planning.py
python scripts/snapshot-planning.py --iteration 3 --verbose
```

**Output**: JSON snapshot saved to `.bmad-core/planning-iterations/snapshots/iteration-NNN.json`

### `scripts/validate-iteration.py`
**Purpose**: Compare two iterations and detect breaking changes

**Usage**:
```bash
python scripts/validate-iteration.py --previous 2 --current 3
python scripts/validate-iteration.py --previous 2 --current 3 --output report.md
```

**Exit Codes**:
- `0`: Validation passed or warnings only
- `1`: Breaking changes detected

**Output**: Markdown validation report with all issues categorized

### `scripts/init-iteration.py`
**Purpose**: Initialize new Planning Phase iteration

**Usage**:
```bash
python scripts/init-iteration.py
python scripts/init-iteration.py --force  # Skip Git clean check
```

**Actions**:
1. Check Git status
2. Create snapshot of current state
3. Backup OpenAPI specs to `specs/api/versions/`
4. Generate pre-correct-course checklist

### `scripts/finalize-iteration.py`
**Purpose**: Complete iteration after `*correct course`

**Usage**:
```bash
python scripts/finalize-iteration.py
python scripts/finalize-iteration.py --breaking  # Accept breaking changes
python scripts/finalize-iteration.py --skip-validation --no-tag
```

**Actions**:
1. Create final snapshot
2. Run validation against previous iteration
3. Update `iteration-log.md`
4. Create post-correct-course checklist
5. Create Git tag (optional)

### `scripts/diff-openapi.py`
**Purpose**: Detailed OpenAPI specification comparison

**Usage**:
```bash
python scripts/diff-openapi.py specs/api/agent-api.v1.0.0.yml specs/api/agent-api.v2.0.0.yml
python scripts/diff-openapi.py spec1.yml spec2.yml --output diff-report.md --fail-on-breaking
```

**Output**: Detailed diff report with:
- Endpoint changes (additions/deletions)
- Schema modifications
- Breaking vs non-breaking categorization
- Migration recommendations

---

## Workflow Integration

### Standard Iteration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INIT: python scripts/init-iteration.py                  │
│    - Check Git clean                                         │
│    - Create baseline snapshot                                │
│    - Backup OpenAPI specs                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. MODIFY: @pm *correct course                              │
│    - PM agent refines PRD                                    │
│    - Regenerates architecture, epics, specs                  │
│    - User reviews and adjusts                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. VALIDATE: python scripts/finalize-iteration.py           │
│    - Create final snapshot                                   │
│    - Run validation against previous iteration               │
│    - Generate validation report                              │
│    - Update iteration log                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. FINALIZE: Git commit + tag                               │
│    - Commit all changes                                      │
│    - Create Git tag (e.g., planning-v3)                      │
│    - Push to remote                                          │
└─────────────────────────────────────────────────────────────┘
```

### Git Pre-Commit Hook

The Git pre-commit hook automatically triggers validation:

```bash
git add .
git commit -m "Planning Iteration 3 Complete"
# Hook automatically runs validation
# Blocks commit if breaking changes detected
```

---

## Validation Rules

All validation rules are defined in `.bmad-core/validators/iteration-rules.yaml`:

### PRD Validation Rules
- **Version Must Increment**: true
- **Functional Requirements Can Delete**: false
- **Epics Can Delete**: false
- **Must Trace to FR**: true

### OpenAPI Validation Rules
- **Endpoints Can Delete**: false (breaking)
- **Endpoints Can Deprecate**: true (non-breaking)
- **Request Required Fields Can Add**: false (breaking)
- **Response Fields Can Delete**: false (breaking)

### Custom Rules
- **Mock Data Detection**: Enabled
- **Patterns**: ["mock_", "fake_", "dummy_", "test_data"]

---

## Usage Examples

### Example 1: Initialize New Iteration

```bash
# User wants to start Iteration 3
@iteration-validator "Initialize Iteration 3"

# Agent executes:
# 1. Check Git status
# 2. Run: python scripts/init-iteration.py
# 3. Verify snapshot created
# 4. Display pre-checklist items
```

### Example 2: Validate After Correct Course

```bash
# User completed @pm *correct course modifications
@iteration-validator "Validate current changes against Iteration 2"

# Agent executes:
# 1. Create temporary snapshot
# 2. Run: python scripts/validate-iteration.py --previous 2 --current 3
# 3. Parse validation report
# 4. Summarize breaking changes, warnings, info
# 5. Recommend next actions
```

### Example 3: Finalize Iteration with Breaking Changes

```bash
@iteration-validator "Finalize Iteration 3, breaking changes are intentional"

# Agent executes:
# 1. Run: python scripts/finalize-iteration.py --breaking
# 2. Update iteration-log.md
# 3. Create Git tag: planning-v3
# 4. Generate post-checklist
# 5. Confirm finalization
```

### Example 4: Compare OpenAPI Versions

```bash
@iteration-validator "Compare agent-api between v1.0.0 and current"

# Agent executes:
# 1. Locate specs/api/versions/agent-api.v1.0.0.yml
# 2. Locate current specs/api/agent-api.openapi.yml
# 3. Run: python scripts/diff-openapi.py [spec1] [spec2]
# 4. Display breaking changes summary
# 5. Suggest version increment (MAJOR/MINOR/PATCH)
```

### Example 5: Emergency Rollback

```bash
@iteration-validator "Rollback to Iteration 2"

# Agent executes:
# 1. Load snapshot: iteration-002.json
# 2. Git checkout previous tag: planning-v2
# 3. Verify all files match snapshot hashes
# 4. Update iteration counter
# 5. Confirm rollback success
```

---

## Output Formats

### Validation Report Structure

```markdown
# Planning Phase Iteration Validation Report

**生成时间**: 2025-11-19 15:30:00

---

## Summary

**Previous Iteration**: 2
**Current Iteration**: 3
**Git Commit**: abc123def456
**Validation Status**: ⚠️ Warnings Detected

**Breaking Changes**: 0
**Warnings**: 3
**Info**: 5

---

## ⚠️ Warnings

### PRD Version Mismatch
⚠️ **docs/prd/FULL-PRD-REFERENCE.md version not incremented**

**Details**:
- Previous version: v1.0.0
- Current version: v1.0.0
- Expected: v1.1.0 or higher

**Recommendation**: Update version in frontmatter before finalizing.

---

## ℹ️ Informational Changes

### New Epic Added
ℹ️ **Epic 11 added: Advanced Analytics**

**Details**:
- File: docs/epics/epic-11-advanced-analytics.md
- Stories: 3
- Status: Planning

---

## Version Compatibility Matrix

| Document | Previous | Current | Status |
|----------|----------|---------|--------|
| PRD | v1.0.0 | v1.0.0 | ⚠️ No change |
| Architecture | v1.2.0 | v1.3.0 | ✅ Incremented |
| Agent API | v1.0.0 | v1.1.0 | ✅ Incremented |

---

## Recommendations

1. **Update PRD version** to v1.1.0
2. Review Epic 11 for completeness
3. Ensure all Epics trace to FRs
4. Run: `python scripts/finalize-iteration.py`
```

---

## Error Handling

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Git not clean" | Uncommitted changes | `git add .` and commit, or use `--force` |
| "Snapshot not found" | Missing previous iteration | Run `init-iteration.py` first |
| "Validation script not found" | Scripts not installed | Check `scripts/` directory |
| "Breaking changes detected" | Unintentional changes | Review report, fix issues, or use `--breaking` |
| "Python not found" | Python not in PATH | Install Python 3.9+ |

---

## Integration with BMad Method

This agent integrates with the BMad Method by:

1. **Enforcing SDD Principles**: Ensures specs remain consistent and versioned
2. **Supporting PM Agent**: Validates outputs from `@pm *correct course`
3. **Enabling Continuous Planning**: Allows iterative refinement with safety nets
4. **Maintaining Traceability**: Links all changes to Git commits and iterations
5. **Quality Gates**: Prevents broken specs from entering development phase

---

## Configuration Files

### `.bmad-core/validators/iteration-rules.yaml`
Defines all validation rules (PRD, Architecture, OpenAPI, Epics, Custom)

### `.bmad-core/planning-iterations/iteration-log.md`
Historical log of all iterations with timestamps, Git commits, statistics

### `.bmad-core/checklists/pre-correct-course.md`
Checklist template for pre-iteration tasks

### `.bmad-core/checklists/post-correct-course.md`
Checklist template for post-iteration tasks

---

## Best Practices

1. **Always initialize before modifying**: Run `init-iteration.py` before `*correct course`
2. **Review validation reports**: Don't blindly accept breaking changes
3. **Use semantic versioning**: Major for breaking, Minor for features, Patch for fixes
4. **Tag milestones**: Use Git tags for important iterations
5. **Document changes**: Update CHANGELOG.md for API changes
6. **Test validation rules**: Periodically review `iteration-rules.yaml`
7. **Backup regularly**: Snapshots are your safety net

---

## Version History

### v1.0.0 (2025-11-19)
- Initial release
- Core validation functionality
- Git integration
- OpenAPI diff support
- Pre/post checklists
- Iteration logging

---

## Related Agents

- **@pm**: Product Manager Agent (generates Planning Phase files)
- **@dev**: Development Agent (consumes validated specs)
- **@qa**: QA Agent (validates against specs)
- **Planning Orchestrator Agent**: High-level workflow coordination

---

## Support

For issues or questions:
1. Check validation reports in `.bmad-core/planning-iterations/`
2. Review `CANVAS_ERROR_LOG.md` for common patterns
3. Consult `docs/architecture/` for design decisions
4. Open issue in project repository

---

**Last Updated**: 2025-11-19
**Maintainer**: BMad Planning Phase Team
