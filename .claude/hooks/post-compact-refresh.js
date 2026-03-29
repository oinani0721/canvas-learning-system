/**
 * PostCompact — v2 精简版
 *
 * v2 改进：不再强制读取整个 development-discipline.md（自相矛盾：
 * 压缩上下文后又立刻重新填满）。只注入 CURRENT_TASK.md 保持任务连续性。
 */
const fs = require('fs');
const path = require('path');

let taskContent = '';
try {
  const taskPath = path.join(
    process.env.CLAUDE_PROJECT_DIR || '.',
    '_decisions', 'CURRENT_TASK.md'
  );
  taskContent = fs.readFileSync(taskPath, 'utf-8');
} catch (e) {
  taskContent = '(CURRENT_TASK.md not found)';
}

process.stdout.write(
  '上下文已压缩。当前任务状态:\n' +
  taskContent + '\n\n' +
  '核心规则: DD-03禁mock | DD-13名实一致 | DD-11新函数需调用方 | DD-07提供验收步骤\n' +
  '继续 CURRENT_TASK.md 中标记为"当前步骤"的工作。'
);
