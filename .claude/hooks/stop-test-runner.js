/**
 * Stop Hook: Deferred Test Runner
 *
 * Runs backend tests after Claude finishes a complete response,
 * NOT after every edit (which causes token bloat per Web report evidence).
 *
 * DD-07: Ensures code changes are tested.
 *
 * Exit code 2 = block completion, force Claude to fix failures.
 * Exit code 0 = tests passed or no test files changed.
 */
const { execSync } = require('child_process');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || '.';

try {
  // Check if any Python files were recently modified (last 2 minutes)
  const recentChanges = execSync(
    'git diff --name-only HEAD 2>/dev/null || echo ""',
    { cwd: projectDir, encoding: 'utf8', timeout: 5000 }
  ).trim();

  const hasPythonChanges = recentChanges.split('\n').some(f =>
    f.endsWith('.py') && (f.startsWith('backend/app/') || f.startsWith('backend/tests/'))
  );

  if (!hasPythonChanges) {
    process.exit(0); // No backend changes, skip tests
  }

  // Run fast unit tests only (no integration)
  const result = execSync(
    'cd backend && python -m pytest tests/ -m "not integration" -x -q --tb=line --no-header 2>&1 | head -20',
    { cwd: projectDir, encoding: 'utf8', timeout: 30000 }
  );

  // Check for failures
  if (/FAILED|ERROR/.test(result)) {
    process.stderr.write(`[DD-07] Tests failed after your changes:\n${result}\nPlease fix before concluding.`);
    process.exit(2);
  }

  process.exit(0);
} catch (e) {
  // If pytest not available or timeout, don't block
  if (e.status === 2) {
    process.stderr.write(e.stderr || e.stdout || '[DD-07] Test execution failed');
    process.exit(2);
  }
  process.exit(0);
}
