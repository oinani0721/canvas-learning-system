/**
 * WorktreeCreate Hook
 *
 * Claude Code 调用此 hook 创建 git worktree 并复制个人配置。
 *
 * stdin: JSON { name, cwd, session_id, hook_event_name }
 * stdout: 必须输出 worktree 的绝对路径（Claude Code 读取此路径）
 * stderr: 诊断信息（不影响 Claude Code）
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const input = Buffer.concat(chunks).toString().trim();

    // 解析 stdin JSON
    let data;
    try {
      data = JSON.parse(input);
    } catch (parseErr) {
      process.stderr.write(`[Worktree Setup] Failed to parse stdin JSON: ${parseErr.message}\n`);
      process.exit(1);
    }

    const name = data.name;
    if (!name) {
      process.stderr.write('[Worktree Setup] No worktree name provided in stdin\n');
      process.exit(1);
    }

    // 主项目根目录
    const projectDir = data.cwd || process.cwd();

    // worktree 目标路径（使用系统临时目录避免路径问题）
    const os = require('os');
    const worktreeDir = path.join(os.tmpdir(), 'claude-worktrees', name);
    const branchName = `worktree/${name}`;

    // 确保父目录存在
    const parentDir = path.dirname(worktreeDir);
    if (!fs.existsSync(parentDir)) {
      fs.mkdirSync(parentDir, { recursive: true });
    }

    // 清理可能残留的同名 worktree
    try {
      execSync(`git worktree remove "${worktreeDir}" --force`, {
        cwd: projectDir,
        stdio: 'pipe'
      });
    } catch (e) {
      // 不存在则忽略
    }

    // 清理可能残留的同名分支
    try {
      execSync(`git branch -D "${branchName}"`, {
        cwd: projectDir,
        stdio: 'pipe'
      });
    } catch (e) {
      // 不存在则忽略
    }

    // 创建 git worktree
    try {
      execSync(`git worktree add -b "${branchName}" "${worktreeDir}" HEAD`, {
        cwd: projectDir,
        stdio: 'pipe'
      });
      process.stderr.write(`[Worktree Setup] Created worktree at ${worktreeDir}\n`);
    } catch (gitErr) {
      process.stderr.write(`[Worktree Setup] git worktree add failed: ${gitErr.message}\n`);
      process.exit(1);
    }

    // 复制 .gitignore 排除的个人配置到新 worktree
    const filesToCopy = [
      'CLAUDE.md',
      '.claude/settings.json',
      '.claude/settings.local.json',
      '.claude/hooks',
      '.claude/commands',
      '.claude/agents',
      '.claude/rules',
    ];

    let copied = 0;
    for (const relPath of filesToCopy) {
      const src = path.join(projectDir, relPath);
      const dest = path.join(worktreeDir, relPath);

      if (!fs.existsSync(src)) continue;

      const stat = fs.statSync(src);
      if (stat.isDirectory()) {
        copyDirSync(src, dest);
      } else {
        const destDir = path.dirname(dest);
        if (!fs.existsSync(destDir)) {
          fs.mkdirSync(destDir, { recursive: true });
        }
        fs.copyFileSync(src, dest);
      }
      copied++;
    }

    process.stderr.write(`[Worktree Setup] Copied ${copied} config items to worktree\n`);

    // 输出绝对路径到 stdout（Claude Code 读取此路径）
    process.stdout.write(worktreeDir);
    process.exit(0);

  } catch (e) {
    process.stderr.write(`[Worktree Setup] Unexpected error: ${e.message}\n`);
    process.exit(1);
  }
});

function copyDirSync(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}
