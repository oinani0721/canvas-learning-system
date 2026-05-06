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

  // Load current task - skip YAML frontmatter, then take 10 lines
  const taskPath = path.join(projectDir, '_decisions', 'CURRENT_TASK.md');
  if (fs.existsSync(taskPath)) {
    const content = fs.readFileSync(taskPath, 'utf8');
    let lines = content.split('\n');

    // Skip YAML frontmatter if present
    if (lines[0] === '---') {
      const endIdx = lines.findIndex((line, idx) => idx > 0 && line === '---');
      if (endIdx !== -1) {
        // Extract frontmatter fields for traceability injection
        const fmBlock = lines.slice(1, endIdx).join('\n');
        const planMatch = fmBlock.match(/active_plan:\s*"?([^"\n]+)"?/);
        if (planMatch && planMatch[1].trim()) {
          parts.push(`[Traceability] Active Plan: ${planMatch[1].trim()}. Commit 必须包含此 ID。完成步骤后更新 checkbox。`);
        }
        lines = lines.slice(endIdx + 1);
      }
    }

    const summary = lines.slice(0, 10).join('\n');
    parts.push(`[Current Task]\n${summary}`);
  }

  // BMAD Process Awareness: only inject annotation summary when in BMAD workflow
  // Reads plan_kind from CURRENT_TASK.md frontmatter — non-BMAD gets zero injection
  if (fs.existsSync(taskPath)) {
    const taskContent = fs.readFileSync(taskPath, 'utf8');
    const fmMatch = taskContent.match(/^---\n([\s\S]*?)\n---/);
    if (fmMatch) {
      const planKindMatch = fmMatch[1].match(/plan_kind:\s*"?([^"\n]+)"?/);
      const planKind = planKindMatch ? planKindMatch[1].trim() : '';
      if (planKind.startsWith('bmad')) {
        try {
          const { execSync } = require('child_process');
          const summary = execSync(
            'python3 scripts/bmad/scan_feedback.py --mode=pending-summary',
            { cwd: projectDir, timeout: 2000, encoding: 'utf8' }
          ).trim();
          if (summary && summary !== '0') {
            parts.push(`[BMAD-ANNO] ${summary}`);
          }
        } catch (_scanErr) {
          // scan_feedback failure is non-blocking
        }
      }
    }
  }

  if (parts.length > 0) {
    process.stdout.write(parts.join('\n---\n'));
  }
} catch (e) {
  // Non-blocking: if injection fails, session proceeds normally
}

process.exit(0);
