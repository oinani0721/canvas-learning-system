// Canvas Learning System - Commitlint Configuration
// Enforces conventional commits with EPIC scope tracking
//
// Format: type(scope): description
// Examples:
//   feat(32): add FSRS-4.5 algorithm integration
//   fix(31): resolve vault sync stale detection
//   refactor(epic-30): extract shared FSRS fixtures
//   chore: update lefthook configuration
//   test(34): add multimodal upload E2E tests

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Types allowed
    'type-enum': [2, 'always', [
      'feat',      // New feature
      'fix',       // Bug fix
      'refactor',  // Code refactoring (no behavior change)
      'test',      // Test additions/changes
      'docs',      // Documentation only
      'chore',     // Build, tooling, dependencies
      'style',     // Formatting, whitespace
      'perf',      // Performance improvement
      'ci',        // CI/CD changes
      'revert',    // Revert a commit
    ]],
    // Scope is optional but encouraged
    'scope-empty': [0, 'never'],
    // Max header length
    'header-max-length': [2, 'always', 100],
    // Subject must not be empty
    'subject-empty': [2, 'never'],
    // Type must not be empty
    'type-empty': [2, 'never'],
    // Subject should be lowercase
    'subject-case': [1, 'always', 'lower-case'],
  },
};
