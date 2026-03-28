/**
 * PostToolUse Auto-Test — 编辑代码后自动运行相关测试
 *
 * .py 文件编辑 → pytest 相关测试
 * .ts/.tsx 文件编辑 → vitest (如已配置)
 *
 * Exit 0 always (信息性，不阻断)
 */
const { execSync } = require('child_process');
const path = require('path');

const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const tool = data.tool_name || '';
    if (!/^(Edit|Write)$/i.test(tool)) { process.exit(0); }

    const filePath = (data.tool_input && data.tool_input.file_path) || '';
    if (!filePath) { process.exit(0); }

    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // 文件名安全处理（防命令注入）
    const sanitize = (name) => name.replace(/[^a-zA-Z0-9_\-]/g, '');
    const shellOpts = { timeout: 30000, encoding: 'utf-8', shell: 'bash' };

    // Python 文件 → pytest
    if (filePath.endsWith('.py') && /backend/.test(filePath)) {
      const fileName = sanitize(path.basename(filePath, '.py'));
      if (!fileName) { process.exit(0); }
      try {
        const result = execSync(
          `cd "${projectDir}/backend" && python -m pytest tests/ -k "${fileName}" --no-header -q --tb=short 2>&1 | tail -15`,
          shellOpts
        );
        if (result.trim()) {
          process.stdout.write('🧪 Auto-test (' + fileName + '):\n' + result.trim().substring(0, 500));
        }
      } catch (e) {
        if (e.stdout) {
          process.stdout.write('🧪 Auto-test (' + fileName + '):\n' + e.stdout.trim().substring(0, 500));
        }
      }
    }

    // TypeScript/React 文件 → vitest (if available)
    if (/\.(tsx?|jsx?)$/.test(filePath) && /frontend[\\/]src/.test(filePath)) {
      const fileName = sanitize(path.basename(filePath).replace(/\.(tsx?|jsx?)$/, ''));
      if (!fileName) { process.exit(0); }
      try {
        const result = execSync(
          `cd "${projectDir}/frontend" && npx vitest run --reporter=verbose --no-color "${fileName}" 2>&1 | tail -15`,
          shellOpts
        );
        if (result.trim()) {
          process.stdout.write('🧪 Auto-test (' + fileName + '):\n' + result.trim().substring(0, 500));
        }
      } catch (e) {
        if (e.stdout && !/command not found|not recognized|Cannot find module/.test(e.stdout)) {
          process.stdout.write('🧪 Auto-test (' + fileName + '):\n' + e.stdout.trim().substring(0, 500));
        }
      }
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
});
