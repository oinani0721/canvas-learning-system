# Source of Truth (SoT) Hierarchy

## 1. Overview

This document defines the authoritative Source of Truth hierarchy for the Canvas Learning System. When conflicts arise between different documentation artifacts, this hierarchy determines which source takes precedence.

**Core Principle**: PRD represents business intent and is the highest authority. Technical specifications must adapt to PRD, not vice versa.

---

## 2. SoT Hierarchy Definition

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: PRD (Product Requirements Document)               │
│  Authority: WHAT the system must do                         │
│  Contains: Functional requirements, business logic,         │
│            user stories, acceptance criteria                │
│  Location: docs/prd/                                        │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 2: Architecture Documents                            │
│  Authority: HOW to structure the system                     │
│  Contains: System design, tech stack, component structure   │
│  Location: docs/architecture/                               │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 3: JSON Schema                                       │
│  Authority: Data structure contracts                        │
│  Contains: Field types, required fields, validation rules   │
│  Location: specs/data/                                      │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 4: OpenAPI Specification                             │
│  Authority: API behavior contracts                          │
│  Contains: Endpoints, parameters, responses, status codes   │
│  Location: specs/api/                                       │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 5: Stories                                           │
│  Authority: Implementation details                          │
│  Contains: Dev Notes, tasks, acceptance criteria            │
│  Location: docs/stories/                                    │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 6: Code                                              │
│  Authority: None (must comply with all above)               │
│  Contains: Implementation                                   │
│  Location: src/                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Conflict Resolution Rules

### 3.1 General Principle

**Higher level always wins**. When two documents conflict, the document at the higher level in the hierarchy is authoritative.

### 3.2 Specific Resolution Rules

| Conflict Type | Winner | Action Required |
|---------------|--------|-----------------|
| PRD vs Architecture | PRD | Update Architecture to align with PRD |
| PRD vs Schema | PRD | Update Schema to align with PRD |
| PRD vs OpenAPI | PRD | Update OpenAPI to align with PRD |
| Architecture vs Schema | Architecture | Update Schema to align with Architecture |
| Architecture vs OpenAPI | Architecture | Update OpenAPI to align with Architecture |
| Schema vs OpenAPI | Schema | Update OpenAPI $ref or inline definitions |
| Any Spec vs Story | Spec | Update Story Dev Notes |
| Story vs Code | Story | Fix code to match Story requirements |

### 3.3 Special Cases

#### 3.3.1 Technical Constraints Override

When a **technical constraint** makes PRD requirements impossible:
1. Document the constraint in an ADR
2. Propose PRD modification with rationale
3. User approval required before proceeding
4. Update PRD first, then cascade changes

#### 3.3.2 Schema-OpenAPI Relationship

OpenAPI specs should **reference** JSON Schemas via `$ref`, not duplicate definitions:
```yaml
# Correct: Reference Schema
components:
  schemas:
    CanvasNode:
      $ref: '../data/canvas-node.schema.json'

# Incorrect: Duplicate definition
components:
  schemas:
    CanvasNode:
      type: object
      properties:
        id: { type: string }
```

---

## 4. Conflict Detection Triggers

### 4.1 During Story Drafting (SM *draft)

The `validate-next-story.md` task performs cross-document verification:
- Story vs Epic alignment
- Story vs Architecture alignment
- Story vs OpenAPI alignment (Step 8a)
- Story vs JSON Schema alignment (Step 8b)
- Cross-document consistency (Step 8c)

### 4.2 During Story Validation (PO *validate-story-draft)

Comprehensive validation including:
- Anti-Hallucination verification
- SDD consistency checks
- Conflict detection and reporting

### 4.3 During Development (Dev *develop-story)

Contract testing validates:
- Code vs OpenAPI compliance
- Code vs JSON Schema compliance
- Runtime behavior vs specification

### 4.4 Pre-commit Hook

Git hook blocks commits that:
- Fail contract tests
- Violate schema definitions
- Break API contracts

---

## 5. Conflict Resolution Protocol

When a conflict is detected, follow this protocol:

### Step 1: HALT
- Stop current validation/development
- Do not proceed with conflicting information

### Step 2: Generate Conflict Report
```markdown
## Conflict Detected

| Field | Document A | Document B | Values |
|-------|------------|------------|--------|
| email | PRD Section 3.2 | user.schema.json | Optional vs Required |

**SoT Hierarchy Suggests**: PRD is authoritative (Level 1 > Level 3)
```

### Step 3: User Confirmation
Present options to user:
- Option A: Accept SoT hierarchy suggestion
- Option B: Override with rationale (requires ADR)
- Option C: Both documents need modification

### Step 4: Document Resolution
Record the decision:
- Which document was updated
- Why (reference SoT hierarchy or ADR)
- Who approved
- Timestamp

### Step 5: Cascade Updates
If higher-level document is modified:
- Update all derived documents
- Re-run validation
- Verify consistency

---

## 6. Incremental Query Template

When conflicts are detected, use this format for user queries:

```markdown
## Specification Conflict Detected

**Story**: {{story_id}}
**Phase**: {{validation_phase}}

### Conflict Details

| # | Type | Document A | Document B | Description |
|---|------|------------|------------|-------------|
| 1 | Field Definition | PRD 3.2 | Schema | email: optional vs required |

### SoT Hierarchy Analysis

According to SoT hierarchy (PRD > Architecture > Schema > OpenAPI > Story):
- **Recommendation**: PRD is authoritative

### Decision Required

**Conflict 1**: email field definition
- [ ] A: PRD is correct → Update Schema to make email optional
- [ ] B: Schema is correct → Update PRD (requires technical justification)
- [ ] C: Both need modification → Please specify

Please select resolution for each conflict to continue validation.
```

---

## 7. Integration with BMad Workflow

### 7.1 Phase 2 (Planning)

- PM creates PRD (Level 1)
- Architect creates Architecture docs (Level 2)
- Architect creates OpenAPI/Schema specs (Level 3-4)
- `@iteration-validator` checks consistency

### 7.2 Phase 4 (Implementation)

- SM creates Stories referencing specs (Level 5)
- PO validates Story with `*validate-story-draft`
  - Includes SoT consistency checks
- Dev implements code (Level 6)
  - Contract testing validates compliance
- QA reviews with `*review`

### 7.3 Change Management

When changes are needed:
1. `*correct-course` generates change proposal
2. Identify affected SoT levels
3. Update from top to bottom
4. Re-validate entire chain

---

## 8. Examples

### Example 1: PRD vs Schema Conflict

**Scenario**: PRD says "user email is optional for guest users", but Schema defines email as required.

**Resolution**:
1. PRD is Level 1, Schema is Level 3
2. PRD wins
3. Update `specs/data/user.schema.json`:
   - Remove "email" from required array
   - Add comment: "Optional per PRD Section 3.2.1"
4. Re-run schema validation

### Example 2: Architecture vs OpenAPI Conflict

**Scenario**: Architecture specifies pagination with `offset/limit`, but OpenAPI defines `page/pageSize`.

**Resolution**:
1. Architecture is Level 2, OpenAPI is Level 4
2. Architecture wins
3. Update `specs/api/canvas-api.openapi.yml`:
   - Change parameters to `offset` and `limit`
   - Update response schema accordingly
4. Re-run OpenAPI validation

### Example 3: Technical Constraint Override

**Scenario**: PRD requires "real-time sync", but technical assessment shows it's not feasible with current architecture.

**Resolution**:
1. Create ADR documenting the constraint
2. Propose PRD modification: "near-real-time sync (< 5s delay)"
3. Get user approval
4. Update PRD first
5. Cascade to Architecture, then OpenAPI
6. Update affected Stories

---

## 9. Validation Checklist

Before marking a Story as ready for development:

- [ ] PRD requirements are covered by Story AC
- [ ] Story references correct Architecture sections
- [ ] Story data models match JSON Schema definitions
- [ ] Story API calls match OpenAPI specifications
- [ ] No conflicts detected between any SoT levels
- [ ] All cross-references are valid and accessible

---

## 10. Related Documents

- **Anti-Hallucination Protocol**: `.bmad-core/tasks/validate-next-story.md` (Steps 8-8d)
- **Conflict Resolution Template**: `.bmad-core/templates/conflict-resolution-prompt.md`
- **Contract Testing**: `tests/contract/test_schemathesis_api.py`
- **Iteration Validation Rules**: `.bmad-core/validators/iteration-rules.yaml`

---

## 11. Implementation Details (Agent Integration)

This section documents how the SoT hierarchy is implemented in BMad Agents.

### 11.1 Agent Configuration Files

The following agent files contain SoT handling instructions:

| Agent | File | Section | Purpose |
|-------|------|---------|---------|
| **PO** | `.bmad-core/agents/po.md` | `conflict-handling` | How to execute Step 8d, use AskUserQuestion |
| **SM** | `.bmad-core/agents/sm.md` | `phase-aware-sot` | Phase detection, SoT priority by phase |
| **Dev** | `.bmad-core/agents/dev.md` | `phase4-sot-protocol` | Specs-First in implementation |

### 11.2 Phase-Aware SoT

SoT priority changes based on BMad phase:

```
Phase 2 (Planning):     PRD > Architecture > Schema > OpenAPI
Phase 4 (Implementation): OpenAPI > Schema > Architecture > PRD (for technical details)
```

**Phase Detection**:
- `src/` empty or no .py/.ts files → Phase 2
- `src/` has implementation code → Phase 4
- User explicitly states phase → Use explicit

**Configuration**: `.bmad-core/decisions/phase-aware-sot.yaml`

### 11.3 Decision Registry

All conflict resolutions are recorded in:

**File**: `.bmad-core/decisions/conflict-resolutions.yaml`

**Entry Format**:
```yaml
- id: "CR-2025-11-25-001"
  conflict:
    document_a: { path, level, value }
    document_b: { path, level, value }
  resolution:
    option: "A|B|C|D"
    decision: "Which document wins"
    adr_required: true|false
  metadata:
    resolved_by: "User"
    timestamp: "ISO 8601"
    phase: "Phase 2|Phase 4"
```

### 11.4 ADR Fast Track (Phase 4 Spec Errors)

When Spec errors are found during Phase 4 implementation:

1. **Trigger**: Option B selected OR Spec missing endpoint/field
2. **Action**: Create ADR documenting deviation
3. **Continue**: Proceed with development per higher-authority source
4. **Sync**: Add to Planning iteration backlog

**ADR Naming**: `ADR-NNN-SPEC-DEVIATION-[topic].md`

### 11.5 AskUserQuestion Protocol

When conflicts detected, agents use AskUserQuestion with 4 standard options:

| Option | Label | Action | Story Status |
|--------|-------|--------|--------------|
| **A** | Accept SoT hierarchy | Update lower-level doc | Continues |
| **B** | Override with ADR | Create ADR, use different source | Continues |
| **C** | Modify both | Specify changes to both docs | Continues |
| **D** | Defer decision | Add to tech debt | Blocked (DRAFT) |

### 11.6 Validation Script Integration

| Script | Purpose | Location |
|--------|---------|----------|
| `validate-sot-hierarchy.py` | Check cross-doc consistency | `scripts/` |
| `validate-schemas.py` | JSON Schema syntax | `scripts/` |
| `validate-openapi.py` | OpenAPI spec syntax | `scripts/` |

**Pre-commit Hook Integration**: `.pre-commit-config.yaml`

---

**Document Version**: 1.1
**Created**: 2025-11-24
**Updated**: 2025-11-25
**Author**: Canvas Learning System Team
