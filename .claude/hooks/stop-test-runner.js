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
 *
 * fix-test-infra-paralysis Phase 0.2:
 *   - Replaced `pytest ... | head -20` with scripts/run_cmd_capture.sh, which
 *     correctly propagates the original pytest exit code (the previous pipe
 *     pattern always returned head's exit code = 0, so the regex check on
 *     result text was the only failure detector — and that regex was
 *     unreliable because pytest's `--tb=line` doesn't always include literal
 *     "FAILED" or "ERROR" in the truncated output).
 *   - Removed the `/FAILED|ERROR/.test(result)` regex check entirely.
 *   - Forced `.venv/bin/python` instead of bare `python` to avoid PATH
 *     ambiguity between system Python and project venv.
 *   - Switched stdio to "inherit" so the wrapper's `[TEST FAILURE]` block
 *     streams directly to the user terminal without Node's 1MB maxBuffer
 *     truncating long tracebacks.
 */
const { execSync } = require('child_process');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || '.';
const wrapper = path.join(projectDir, 'scripts/run_cmd_capture.sh');

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

  // Run fast unit tests through the wrapper. The wrapper handles tail+capture
  // and exits with pytest's original exit code. stdio: "inherit" lets the
  // wrapper's stderr (including [TEST FAILURE] block) stream directly.
  try {
    execSync(
      `"${wrapper}" --cwd backend --tail 120 -- ` +
        `.venv/bin/python -m pytest tests/ -m "not integration" ` +
        `-x -q --tb=line --no-header --no-cov ` +
        `--override-ini="addopts="`,
      { cwd: projectDir, stdio: 'inherit', timeout: 300000 }
    );
  } catch (testErr) {
    // execSync throws on non-zero exit. status holds the wrapper's exit code,
    // which equals pytest's exit code thanks to run_cmd_capture.sh propagation.
    const code = testErr.status ?? 1;
    process.stderr.write(`\n[DD-07 stop-test-runner] pytest failed with exit code ${code} — see [TEST FAILURE] block above for tail and full-log path.\n`);
    process.exit(2); // Stop hook protocol: exit 2 blocks
  }

  process.exit(0);
} catch (outerErr) {
  // Defensive catch for git command errors etc — don't block on pre-test infra
  process.exit(0);
}
