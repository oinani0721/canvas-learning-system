<!-- Powered by BMAD™ Core -->

# Validate Next Story Task

## Purpose

To comprehensively validate a story draft before implementation begins, ensuring it is complete, accurate, and provides sufficient context for successful development. This task identifies issues and gaps that need to be addressed, preventing hallucinations and ensuring implementation readiness.

## SEQUENTIAL Task Execution (Do not proceed until current Task is complete)

### 0. Load Core Configuration and Inputs

- Load `.bmad-core/core-config.yaml`
- If the file does not exist, HALT and inform the user: "core-config.yaml not found. This file is required for story validation."
- Extract key configurations: `devStoryLocation`, `prd.*`, `architecture.*`
- Identify and load the following inputs:
  - **Story file**: The drafted story to validate (provided by user or discovered in `devStoryLocation`)
  - **Parent epic**: The epic containing this story's requirements
  - **Architecture documents**: Based on configuration (sharded or monolithic)
  - **Story template**: `bmad-core/templates/story-tmpl.md` for completeness validation

### 1. Template Completeness Validation

- Load `.bmad-core/templates/story-tmpl.yaml` and extract all section headings from the template
- **Missing sections check**: Compare story sections against template sections to verify all required sections are present
- **Placeholder validation**: Ensure no template placeholders remain unfilled (e.g., `{{EpicNum}}`, `{{role}}`, `_TBD_`)
- **Agent section verification**: Confirm all sections from template exist for future agent use
- **Structure compliance**: Verify story follows template structure and formatting

### 2. File Structure and Source Tree Validation

- **File paths clarity**: Are new/existing files to be created/modified clearly specified?
- **Source tree relevance**: Is relevant project structure included in Dev Notes?
- **Directory structure**: Are new directories/components properly located according to project structure?
- **File creation sequence**: Do tasks specify where files should be created in logical order?
- **Path accuracy**: Are file paths consistent with project structure from architecture docs?

### 3. UI/Frontend Completeness Validation (if applicable)

- **Component specifications**: Are UI components sufficiently detailed for implementation?
- **Styling/design guidance**: Is visual implementation guidance clear?
- **User interaction flows**: Are UX patterns and behaviors specified?
- **Responsive/accessibility**: Are these considerations addressed if required?
- **Integration points**: Are frontend-backend integration points clear?

### 4. Acceptance Criteria Satisfaction Assessment

- **AC coverage**: Will all acceptance criteria be satisfied by the listed tasks?
- **AC testability**: Are acceptance criteria measurable and verifiable?
- **Missing scenarios**: Are edge cases or error conditions covered?
- **Success definition**: Is "done" clearly defined for each AC?
- **Task-AC mapping**: Are tasks properly linked to specific acceptance criteria?

### 5. Validation and Testing Instructions Review

- **Test approach clarity**: Are testing methods clearly specified?
- **Test scenarios**: Are key test cases identified?
- **Validation steps**: Are acceptance criteria validation steps clear?
- **Testing tools/frameworks**: Are required testing tools specified?
- **Test data requirements**: Are test data needs identified?

### 6. Security Considerations Assessment (if applicable)

- **Security requirements**: Are security needs identified and addressed?
- **Authentication/authorization**: Are access controls specified?
- **Data protection**: Are sensitive data handling requirements clear?
- **Vulnerability prevention**: Are common security issues addressed?
- **Compliance requirements**: Are regulatory/compliance needs addressed?

### 7. Tasks/Subtasks Sequence Validation

- **Logical order**: Do tasks follow proper implementation sequence?
- **Dependencies**: Are task dependencies clear and correct?
- **Granularity**: Are tasks appropriately sized and actionable?
- **Completeness**: Do tasks cover all requirements and acceptance criteria?
- **Blocking issues**: Are there any tasks that would block others?

### 8. Anti-Hallucination Verification

- **Source verification**: Every technical claim must be traceable to source documents
- **Architecture alignment**: Dev Notes content matches architecture specifications
- **No invented details**: Flag any technical decisions not supported by source documents
- **Reference accuracy**: Verify all source references are correct and accessible
- **Fact checking**: Cross-reference claims against epic and architecture documents

### 8a. OpenAPI Spec Alignment (SDD Consistency)

- **Endpoint consistency**: Are API endpoints mentioned in Story defined in OpenAPI spec?
- **Response codes**: Do HTTP status codes in Story match OpenAPI definitions?
- **Request/Response schema**: Do data structures in Story reference correct Schema definitions?
- **Parameter validation**: Do parameters in Story match OpenAPI parameter definitions?
- **Error responses**: Are error scenarios in Story consistent with OpenAPI error definitions?

### 8b. JSON Schema Alignment (SDD Consistency)

- **Field definitions**: Are fields mentioned in Story defined in corresponding JSON Schema?
- **Required fields**: Does Story correctly identify required vs optional fields per Schema?
- **Type consistency**: Do data types in Story match Schema type definitions?
- **Enum values**: Are enumeration values in Story within Schema-defined ranges?
- **Nested structures**: Do nested object references match Schema $ref definitions?

### 8c. Cross-Document Consistency (SoT Verification)

- **PRD vs Architecture**: Do Architecture decisions support all PRD functional requirements?
- **PRD vs OpenAPI**: Does every PRD feature have corresponding API endpoint coverage?
- **Architecture vs Schema**: Do Architecture data models match Schema definitions?
- **Schema vs OpenAPI**: Do OpenAPI $ref paths correctly point to Schema files?
- **Story vs All Specs**: Does Story Dev Notes accurately reflect all specification documents?

### 8d. Conflict Resolution Protocol

When conflicts are detected between any SoT levels:

1. **HALT validation** - Do not proceed to subsequent steps
2. **Generate conflict report** - Document each conflict with:
   - Conflicting documents and sections
   - Specific values in conflict
   - SoT hierarchy recommendation (see `docs/architecture/sot-hierarchy.md`)
3. **Apply SoT hierarchy** - Determine which source should be authoritative:
   - PRD > Architecture > Schema > OpenAPI > Story > Code
4. **Request user confirmation** - Present conflict resolution options:
   - Accept hierarchy recommendation
   - Override with justification (requires ADR)
   - Modify both documents
5. **Document resolution** - Record decision, approver, and timestamp
6. **Cascade updates** - If higher-level doc changed, update all derived documents
7. **Re-validate** - Run validation again after conflict resolution

**IMPORTANT**: Do not mark story as READY if any unresolved conflicts exist.

---

#### FOR AGENT: Step 8d Implementation Guide

**When you (PO Agent) reach Step 8d and have detected conflicts:**

1. **STOP immediately** - Do not continue to Step 9 or generate final report

2. **For EACH conflict**, use the `AskUserQuestion` tool:

   ```
   Question: "Conflict [N/M]: [Document A] vs [Document B]

   - [Document A] ([Level X]): [exact value/definition from document]
   - [Document B] ([Level Y]): [exact value/definition from document]

   SoT Hierarchy Suggests: [Document A/B] is authoritative (Level X > Level Y)

   How should this conflict be resolved?"

   Options:
   A: "Accept SoT hierarchy" - Update [lower-level doc] to match [higher-level doc]
   B: "Override with ADR" - [Higher-level doc] is wrong, create ADR justification
   C: "Modify both documents" - Both need changes (specify what)
   D: "Defer decision" - Add to tech debt, Story remains DRAFT
   ```

3. **Process user response**:
   - Option A: Note update needed in lower-level doc
   - Option B: Set `adr_required: true`, continue with different source
   - Option C: Note both updates needed
   - Option D: Mark `conflict_blocked: true`, Story status = DRAFT

4. **Record each resolution** in Story's Dev Notes:
   ```markdown
   ## Conflict Resolutions (Step 8d)
   | # | Conflict | Decision | Action | Resolved By |
   |---|----------|----------|--------|-------------|
   | 1 | PRD vs Schema: email | A (Accept SoT) | Update Schema | User |
   ```

5. **After ALL conflicts processed**:
   - If any Option D selected → Final Assessment = "CONFLICT-BLOCKED"
   - If all resolved with A/B/C → Continue to Step 9

6. **Record in `.bmad-core/decisions/conflict-resolutions.yaml`**:
   - Add entry for each conflict with full details
   - This creates audit trail for future reference

**Reference Files**:
- SoT Hierarchy: `docs/architecture/sot-hierarchy.md`
- Decision Registry: `.bmad-core/decisions/conflict-resolutions.yaml`
- Phase Config: `.bmad-core/decisions/phase-aware-sot.yaml`

---

### 9. Dev Agent Implementation Readiness

- **Self-contained context**: Can the story be implemented without reading external docs?
- **Clear instructions**: Are implementation steps unambiguous?
- **Complete technical context**: Are all required technical details present in Dev Notes?
- **Missing information**: Identify any critical information gaps
- **Actionability**: Are all tasks actionable by a development agent?

### 10. Generate Validation Report

Provide a structured validation report including:

#### Template Compliance Issues

- Missing sections from story template
- Unfilled placeholders or template variables
- Structural formatting issues

#### Critical Issues (Must Fix - Story Blocked)

- Missing essential information for implementation
- Inaccurate or unverifiable technical claims
- Incomplete acceptance criteria coverage
- Missing required sections

#### Should-Fix Issues (Important Quality Improvements)

- Unclear implementation guidance
- Missing security considerations
- Task sequencing problems
- Incomplete testing instructions

#### Nice-to-Have Improvements (Optional Enhancements)

- Additional context that would help implementation
- Clarifications that would improve efficiency
- Documentation improvements

#### Anti-Hallucination Findings

- Unverifiable technical claims
- Missing source references
- Inconsistencies with architecture documents
- Invented libraries, patterns, or standards

#### SDD Consistency Findings (Steps 8a-8c)

- OpenAPI spec alignment issues
- JSON Schema alignment issues
- Cross-document inconsistencies
- Missing API endpoint coverage for PRD features

#### Conflict Resolution Required (Step 8d)

If conflicts detected, include resolution table:

| # | Conflict Type | Document A | Document B | Values | SoT Suggests | Resolution |
|---|---------------|------------|------------|--------|--------------|------------|
| 1 | Field Definition | PRD 3.2 | user.schema.json | optional vs required | PRD | _Pending User Decision_ |
| 2 | Response Code | Story Dev Notes | OpenAPI | 200 vs 201 | OpenAPI | _Pending User Decision_ |

**Conflict Status**:
- [ ] All conflicts resolved
- [ ] Pending user decisions (count: ___)
- [ ] Blocked - cannot proceed

#### Final Assessment

- **GO**: Story is ready for implementation
- **NO-GO**: Story requires fixes before implementation
- **CONFLICT-BLOCKED**: Unresolved SoT conflicts require user decision before proceeding
- **Implementation Readiness Score**: 1-10 scale
- **Confidence Level**: High/Medium/Low for successful implementation

**Reference**: For SoT hierarchy and conflict resolution protocol, see `docs/architecture/sot-hierarchy.md`
