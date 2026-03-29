/**
 * Graphiti Stop Hook — v8 降噪版
 *
 * v8 改进（基于 Gemini 上下文传递诊断报告 R4）：
 * - 大多数检查从"阻断"降级为"追加警告"，保持 AI 思维连贯性
 * - 只保留 2 个硬阻断：(1) Decision无Review (2) 未commit源码文件
 * - 其余检查改为 stderr 警告（显示在 feedback 中但不阻断）
 */
const fs = require('fs');
const path = require('path');

const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const isRetry = data.stop_hook_active === true;
    const msg = data.last_assistant_message || '';
    const hasAdd = /add_memory/i.test(msg);
    const hasSearch = /search_memory_facts|search_nodes/i.test(msg);

    function block(reason) {
      console.log(JSON.stringify({ decision: 'block', reason }));
      process.exit(0);
    }

    function warn(reason) {
      process.stderr.write('Stop hook feedback:\n' + reason + '\n');
    }

    // ===== 硬阻断（仅 2 项）=====

    // 1. Decision 无 Review — 必须闭环
    if (/\[Decision\]/i.test(msg) && !/\[Decision-Review\]/i.test(msg)) {
      block('有 [Decision] 但没有 [Decision-Review]。立即 add_memory("[Decision-Review] ... — 待验证", PENDING 状态)。');
    }

    // 2. 未 commit 源码文件 — 防止丢失工作
    if (!isRetry && !/git commit|已提交|已推送/i.test(msg)) {
      try {
        const { execSync } = require('child_process');
        const projectDir = process.env.CLAUDE_PROJECT_DIR || '';
        const gitOut = execSync('git status --porcelain', { cwd: projectDir, encoding: 'utf8', timeout: 5000 });
        const uncommitted = gitOut.split('\n').filter(l => {
          if (!l.trim()) return false;
          const f = l.slice(3).trim();
          if (f.startsWith('.claude/') || f.startsWith('"')) return false;
          return /\.(tsx?|jsx?|py|rs|css|html)$/i.test(f);
        });
        if (uncommitted.length > 0) {
          const fileList = uncommitted.map(l => l.slice(3).trim()).slice(0, 5);
          warn('git status 发现 ' + uncommitted.length + ' 个源码文件未 commit: ' + fileList.join(', '));
        }
      } catch (e) { /* ignore */ }
    }

    // ===== 软警告（不阻断，仅提醒）=====

    if (isRetry) { process.exit(0); }

    // 疑似决策未记录
    const decisionVerbs = /确认|选定|采用|决定用|推荐|建议采用|选择了|敲定/i;
    const decisionObjects = /方案|架构|算法|选型|框架|路线|技术栈/i;
    if (decisionVerbs.test(msg) && decisionObjects.test(msg) && !/\[Decision\]/i.test(msg)) {
      warn('疑似决策未记录。如果本轮做出了技术决策，建议 add_memory [Decision]。');
    }

    // 无 Graphiti 操作
    if (!hasAdd && !hasSearch) {
      warn('本轮无 Graphiti 操作。评估是否需要 add_memory。');
    }

    // CURRENT_TASK.md 更新提醒
    const completedStep = /Step.*完成|✅.*Step|已完成.*Step|commit.*[a-f0-9]{7}/i.test(msg);
    if (completedStep) {
      warn('检测到完成了步骤。请更新 _decisions/CURRENT_TASK.md 的 checkbox。');
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
});
