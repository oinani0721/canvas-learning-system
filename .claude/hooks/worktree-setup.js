/**
 * WorktreeCreate Hook
 *
 * worktree 创建时自动复制个人配置（CLAUDE.md、hooks、settings）到新 worktree。
 * 这些文件被 .gitignore 排除，不会出现在 worktree 的 git checkout 中，
 * 所以需要手动复制。
 */

const fs = require('fs');
const path = require('path');

const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const worktreePath = data.worktree_path || data.path;

    if (!worktreePath) {
      process.exit(0);
    }

    // 主项目根目录（WorktreeCreate hook 在主 session 中触发）
    const projectDir = data.project_dir || data.cwd || process.cwd();

    // 需要复制的个人配置文件/目录
    const filesToCopy = [
      'CLAUDE.md',
      '.claude/settings.json',
      '.claude/settings.local.json',
      '.claude/hooks',
      '.claude/commands',
      '.claude/agents',
    ];

    let copied = 0;

    for (const relPath of filesToCopy) {
      const src = path.join(projectDir, relPath);
      const dest = path.join(worktreePath, relPath);

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

    if (copied > 0) {
      process.stdout.write(
        `[Worktree Setup] 已复制 ${copied} 个个人配置到 worktree。Graphiti hooks 和 CLAUDE.md 已就绪。`
      );
    }
  } catch (e) {
    // 静默失败，不阻塞 worktree 创建
    process.exit(0);
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
