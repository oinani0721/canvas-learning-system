<!-- Powered by BMAD Core - Canvas Extension -->

# Create Architecture Decision Record (ADR)

## Purpose

Create standardized Architecture Decision Records using the Michael Nygard format to document important architectural decisions.

## Workflow

### Step 1: Determine Next ADR Number

1. Read existing ADRs from `docs/architecture/decisions/`
2. Extract the highest existing number (e.g., 0005)
3. Increment to get next number (e.g., 0006)

### Step 2: Gather Decision Context

**Present to user:**

"I'll help you create ADR-{NUMBER}. Please provide the following information:"

**Required Information:**

1. **Decision Title**: Brief title describing the decision (e.g., "Vector Database Selection")
2. **Problem Context**: What problem are we solving? What constraints exist?
3. **Candidate Solutions**: What options were considered? (minimum 2)

**For each candidate, collect:**
- Name
- Key advantages
- Key disadvantages
- Score (1-5)

### Step 3: Record the Decision

**Ask user:**

1. **Selected Solution**: Which candidate was chosen?
2. **Key Reasons**: Why was this solution selected? (list 3+ reasons)
3. **Tradeoffs Accepted**: What downsides are we accepting?

### Step 4: Document Consequences

**Guide user through:**

1. **Positive Impacts**: What benefits does this decision bring?
2. **Negative Impacts**: What challenges or limitations does it introduce?
3. **Migration Path**: If replacing existing solution, what are the migration steps?

### Step 5: Add References

**Collect:**

1. **Related PRD Section**: Which PRD section(s) drove this decision?
2. **Related Epic/Story**: Which Epic or Stories will implement this?
3. **External Documentation**: Any relevant external docs or research?

### Step 6: Generate ADR Document

1. Load template from `.bmad-core/templates/adr-template.md`
2. Fill in all collected information
3. Set Status to "Proposed"
4. Add current date
5. Generate filename: `{NUMBER}-{title-with-dashes}.md`

### Step 7: Save and Confirm

1. Save to `docs/architecture/decisions/{filename}`
2. Display summary:

```
✅ ADR Created Successfully

📄 File: docs/architecture/decisions/{filename}
📋 Number: ADR-{NUMBER}
📝 Title: {TITLE}
📅 Status: Proposed

Next Steps:
1. Review the ADR content
2. Get team approval if needed
3. Change Status to "Accepted" when approved
4. Reference this ADR in relevant Story Dev Notes
```

## Elicitation Options

When gathering information, use the following elicitation techniques if user needs help:

1. **Proceed** - Continue to next section
2. **Compare Alternatives** - Help analyze trade-offs between options
3. **Research Topic** - Deep dive into a specific technology
4. **Clarify Requirements** - Revisit what the decision needs to achieve
5. **Review Similar ADRs** - Look at existing ADRs for reference
6. **Brainstorm Options** - Generate additional candidate solutions

## Output Format

The generated ADR must follow the Michael Nygard format exactly as defined in:
`.bmad-core/templates/adr-template.md`

## Naming Convention

- File format: `NNNN-title-with-dashes.md`
- Example: `0006-vector-database-selection.md`
- Numbers are zero-padded to 4 digits

## Integration with Other Workflows

### When to Create ADR

- During Phase 3 (Solutioning) for architecture decisions
- During Phase 4 when encountering major technical pivots
- Whenever there's a "Why A instead of B?" question

### After ADR Creation

1. Update related Story Dev Notes to reference the ADR
2. Update Architecture.md if needed
3. Consider adding to devLoadAlwaysFiles if decision impacts all development

## Status Transitions

```
Proposed → Accepted → [Deprecated | Superseded by ADR-XXXX]
```

- **Proposed**: Initial state, under review
- **Accepted**: Approved and in effect
- **Deprecated**: No longer relevant
- **Superseded**: Replaced by newer ADR
