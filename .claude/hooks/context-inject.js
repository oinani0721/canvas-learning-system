/**
 * SessionStart Hook: Context Injection
 *
 * Injects known-gotchas summary and current task status into Claude's context
 * at the start of every session.
 *
 * DD-08: Ensures agents are aware of historical context.
 *
 * Output to stdout is injected into Claude's system prompt.
 * Exit code 0 = allow session to proceed.
 */
const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || '.';

try {
  const parts = [];

  // Load known gotchas (pending items only)
  const gotchasPath = path.join(projectDir, 'docs', 'known-gotchas.md');
  if (fs.existsSync(gotchasPath)) {
    const content = fs.readFileSync(gotchasPath, 'utf8');
    const pendingLines = content.split('\n').filter(line =>
      /Pending|pending|TODO|⛔/.test(line)
    );
    if (pendingLines.length > 0) {
      parts.push(`[Known Issues - ${pendingLines.length} pending]`);
      parts.push(pendingLines.slice(0, 5).join('\n'));
    }
  }

  // Load current task
  const taskPath = path.join(projectDir, '_decisions', 'CURRENT_TASK.md');
  if (fs.existsSync(taskPath)) {
    const content = fs.readFileSync(taskPath, 'utf8');
    const summary = content.split('\n').slice(0, 10).join('\n');
    parts.push(`[Current Task]\n${summary}`);
  }

  if (parts.length > 0) {
    process.stdout.write(parts.join('\n---\n'));
  }
} catch (e) {
  // Non-blocking: if injection fails, session proceeds normally
}

process.exit(0);
