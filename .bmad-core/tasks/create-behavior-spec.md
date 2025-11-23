<!-- Powered by BMAD Core - Canvas Extension -->

# Create Behavior Specification (Gherkin BDD)

## Purpose

Create standardized Gherkin BDD (Behavior-Driven Development) specifications to define acceptance criteria in Given/When/Then format. These specs serve as:
- Executable documentation
- Acceptance criteria for QA
- Contract between PM and Dev

## Workflow

### Step 1: Identify Feature Context

1. Read the feature name provided by user
2. Search for related PRD sections, Epic, or Story
3. Identify existing behavior specs in `specs/behavior/`
4. Determine output filename: `{feature-name}.feature`

### Step 2: Gather Feature Information

**Present to user:**

"I'll help you create a Gherkin specification for '{feature}'. Please provide:"

**Required Information:**

1. **Feature Description**: One-line description of what this feature does
2. **User Role**: Who is the primary actor? (e.g., "User", "Admin", "System")
3. **Business Value**: Why is this feature valuable?

### Step 3: Define Scenarios

**Guide user through creating scenarios:**

For each scenario, collect:

1. **Scenario Name**: Brief, descriptive name
2. **Given**: Initial context/preconditions (can be multiple)
3. **When**: Action or trigger
4. **Then**: Expected outcome (can be multiple)
5. **And/But**: Additional conditions (optional)

**Prompt:**
"Let's define the scenarios. Start with the happy path, then we'll add edge cases."

**Minimum Requirements:**
- At least 1 happy path scenario
- At least 1 error/edge case scenario

### Step 4: Add Examples (Optional)

If scenarios use variables, create Examples tables:

```gherkin
Scenario Outline: Score determines color
  Given a yellow node with user response
  When the scoring-agent evaluates with score <score>
  Then the color should be "<color>"

  Examples:
    | score | color  |
    | 90    | green  |
    | 70    | purple |
    | 40    | red    |
```

### Step 5: Define Tags

Add appropriate tags for organization:

- `@epic-N` - Related Epic number
- `@story-N.M` - Related Story
- `@priority-high/medium/low` - Test priority
- `@smoke` - Include in smoke tests
- `@wip` - Work in progress

### Step 6: Generate Specification

1. Load template from `.bmad-core/templates/behavior-spec-tmpl.md`
2. Fill in Feature, Background (if any), and Scenarios
3. Add tags
4. Format according to Gherkin syntax

### Step 7: Save and Confirm

1. Save to `specs/behavior/{feature-name}.feature`
2. Display summary:

```
✅ Behavior Specification Created

📄 File: specs/behavior/{feature-name}.feature
🏷️ Tags: @epic-13, @priority-high
📋 Scenarios: 4 (2 happy path, 2 edge cases)

Next Steps:
1. Review scenarios for completeness
2. Add to test automation (pytest-bdd or behave)
3. Reference in Story acceptance criteria
4. Run: pytest specs/behavior/{feature-name}.feature
```

## Elicitation Options

When gathering information, offer these options:

1. **Proceed** - Continue to next step
2. **Add More Scenarios** - Define additional test cases
3. **Review PRD** - Check PRD for acceptance criteria
4. **See Examples** - Show example Gherkin specs
5. **Clarify Given/When/Then** - Explain BDD syntax
6. **Generate from Story** - Auto-generate from Story acceptance criteria

## Output Format

Generated specs must follow Gherkin syntax exactly as defined in:
`.bmad-core/templates/behavior-spec-tmpl.md`

## Naming Convention

- File format: `{feature-name}.feature`
- Example: `scoring-agent.feature`, `ebbinghaus-review.feature`
- Use lowercase with hyphens
- Keep names descriptive but concise

## Integration with BMad Workflow

### When to Create Behavior Spec

- **Phase 2**: After defining Story acceptance criteria
- **Phase 3**: When Architect needs to specify component behavior
- **Phase 4**: Before Dev starts implementation (contract-first)

### After Creation

1. Reference in Story Dev Notes
2. Add to QA test suite
3. Include in CI/CD pipeline
4. Update if PRD changes (PRD-Spec sync)

## Gherkin Syntax Reference

```gherkin
Feature: Feature name
  As a [role]
  I want [feature]
  So that [benefit]

  Background:
    Given common precondition

  @tag1 @tag2
  Scenario: Scenario name
    Given [precondition]
    And [another precondition]
    When [action]
    Then [expected result]
    And [another result]
    But [exception]
```

## Example Scenarios

### Happy Path
```gherkin
Scenario: User scores a yellow node successfully
  Given a Canvas with node "yellow-001" of type "yellow"
  And the node contains user response "This is my explanation"
  When the user invokes scoring-agent on "yellow-001"
  Then the system returns a score between 0 and 100
  And the node color is updated based on score
```

### Error Case
```gherkin
Scenario: Score fails for invalid node
  Given a Canvas with node "invalid-001" of type "red"
  When the user invokes scoring-agent on "invalid-001"
  Then the system returns an error "Cannot score red nodes"
  And the node remains unchanged
```

## Pre-commit Hook Integration

Behavior specs are validated by `check-prd-spec-sync.py`:
- Checks that each Epic/Story has corresponding feature file
- Validates Gherkin syntax
- Detects orphaned scenarios (no Story reference)
