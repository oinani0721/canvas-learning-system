# Conflict Resolution Prompt Template

Use this template when specification conflicts are detected during story validation.

---

## Specification Conflict Detected

**Story**: `{{story_id}}`
**Validation Phase**: `{{validation_phase}}`
**Timestamp**: `{{timestamp}}`

---

### Conflict Summary

| Total Conflicts | Critical | Should-Fix | Nice-to-Have |
|-----------------|----------|------------|--------------|
| {{total_count}} | {{critical_count}} | {{should_fix_count}} | {{nice_to_have_count}} |

---

### Conflict Details

{{#conflicts}}

#### Conflict {{index}}: {{title}}

**Type**: {{conflict_type}}
**Severity**: {{severity}}

| Aspect | Document A | Document B |
|--------|------------|------------|
| Source | {{doc_a_name}} | {{doc_b_name}} |
| Location | {{doc_a_location}} | {{doc_b_location}} |
| Value | `{{doc_a_value}}` | `{{doc_b_value}}` |

**Context**: {{context_description}}

{{/conflicts}}

---

### SoT Hierarchy Analysis

According to the Source of Truth hierarchy defined in `docs/architecture/sot-hierarchy.md`:

```
PRD (Level 1) > Architecture (Level 2) > Schema (Level 3) > OpenAPI (Level 4) > Story (Level 5)
```

{{#conflicts}}

**Conflict {{index}} Recommendation**:
- {{doc_a_name}} is Level {{doc_a_level}}
- {{doc_b_name}} is Level {{doc_b_level}}
- **Suggested Resolution**: {{suggested_winner}} should be authoritative

{{/conflicts}}

---

### Decision Required

Please select a resolution for each conflict:

{{#conflicts}}

---

#### Conflict {{index}}: {{title}}

{{description}}

**Options**:

- [ ] **Option A**: Accept SoT recommendation
  - Action: Update {{doc_to_update}} to match {{authoritative_doc}}
  - Specifically: {{specific_change_a}}

- [ ] **Option B**: Override SoT hierarchy
  - Action: Update {{authoritative_doc}} instead
  - Requires: ADR documenting technical justification
  - Specifically: {{specific_change_b}}

- [ ] **Option C**: Both documents need modification
  - Please describe the required changes:
  - Document A change: _________________
  - Document B change: _________________

**Your Selection**: [ ]

**Justification** (required if Option B or C):
```
_________________
```

{{/conflicts}}

---

### Next Steps After Resolution

1. **Apply Changes**: Update the selected documents
2. **Re-validate**: Run `*validate-story-draft` again
3. **Document Decision**: Record in story's Dev Notes or ADR
4. **Cascade Updates**: If higher-level doc changed, update derived docs

---

### Resolution Record

| Conflict | Decision | Approved By | Timestamp | Notes |
|----------|----------|-------------|-----------|-------|
{{#conflicts}}
| {{index}} | _TBD_ | _TBD_ | _TBD_ | |
{{/conflicts}}

---

**IMPORTANT**: Validation cannot proceed to GO status until all conflicts are resolved.

---

## Usage Example

```markdown
## Specification Conflict Detected

**Story**: `15.2.story.md`
**Validation Phase**: PO *validate-story-draft
**Timestamp**: 2025-11-24 10:30:00

---

### Conflict Details

#### Conflict 1: Email Field Requirement

**Type**: Field Definition
**Severity**: Critical

| Aspect | Document A | Document B |
|--------|------------|------------|
| Source | PRD Section 3.2.1 | user.schema.json |
| Location | docs/prd/FULL-PRD.md#3.2.1 | specs/data/user.schema.json |
| Value | `email: optional for guests` | `email: required` |

**Context**: Guest users should be able to use the system without providing email.

---

### SoT Hierarchy Analysis

**Conflict 1 Recommendation**:
- PRD is Level 1
- JSON Schema is Level 3
- **Suggested Resolution**: PRD should be authoritative

---

### Decision Required

#### Conflict 1: Email Field Requirement

**Options**:

- [x] **Option A**: Accept SoT recommendation
  - Action: Update user.schema.json to match PRD
  - Specifically: Remove "email" from required array, add description "Optional for guest users"

**Your Selection**: [A]

**Justification**: N/A - following SoT hierarchy
```
