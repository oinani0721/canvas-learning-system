/**
 * Session Start — v5 精简版
 *
 * v5 改进（基于 Gemini 上下文传递诊断报告 R1/R2）：
 * - 移除强制读取 4 个文件（减少 ~10,000 tokens 上下文污染）
 * - 改为直接注入 CURRENT_TASK.md 内容（唯一真相源）
 * - Graphiti 搜索从 3×30=90 facts 缩减为 1×10 facts（精准搜索）
 * - 规则按需注入（由 user-prompt-submit hook 负责），不在启动时全量加载
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
  taskContent = '(CURRENT_TASK.md 不存在，请创建)';
}

process.stdout.write(
  '=== Session 启动 ===\n\n' +
  '📋 当前任务状态（唯一真相源）:\n' +
  taskContent + '\n\n' +
  '--- 启动指令 ---\n' +
  '1. search_memory_facts("{用户首条消息关键词}", group_ids:["canvas-dev"], max_facts:10, exclude_invalidated:true)\n' +
  '2. add_memory("[Session-Start] {主题}", group_id:"canvas-dev")\n' +
  '3. 根据 CURRENT_TASK.md 的"当前步骤"继续工作。不要重新规划已完成的步骤。\n' +
  '4. 完成步骤后立即更新 CURRENT_TASK.md 的 checkbox。'
);
