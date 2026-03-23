/**
 * Graphiti Stop Hook — JSON Decision Blocking v7
 *
 * v7 新增：读取审计日志检查未 commit 的文件修改
 *
 * 关键设计：stop_hook_active 时只跳过低优先级检测（层4/5），
 * 高优先级检测（Decision-Review 闭环、Code-Review、深度澄清、开发纪律、commit）仍然执行。
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
    const hasSearch = /search_memory_facts|search_nodes/i.test(msg) && !hasAdd;

    function block(reason) {
      console.log(JSON.stringify({ decision: 'block', reason }));
      process.exit(0);
    }

    // ===== 高优先级检测（即使 stop_hook_active 也执行）=====

    // 0. Session首轮回复必须确认已读取规则和刚需清单
    const hasSessionStart = /\[Session-Start\]/i.test(msg);
    const hasReadRules = /development-discipline|DD-01|DD-03|DD-10|10.*条.*纪律|10.*rules/i.test(msg);
    const hasReadEssentials = /MVP.*刚需.*14|刚需.*清单|project_mvp_essentials|decision-log/i.test(msg);
    if (hasSessionStart && !hasReadRules && !hasReadEssentials && !isRetry) {
      block('Session首轮未确认读取规则和刚需清单。⛔ 必须 Read development-discipline.md 和 MVP刚需清单，并在回复中确认。');
    }

    // 1a. 记录了 [Decision] 但没有 [Decision-Review]
    if (/\[Decision\]/i.test(msg) && !/\[Decision-Review\]/i.test(msg)) {
      block('有 [Decision] 但没有 [Decision-Review]。立即 add_memory("[Decision-Review] ... — 待验证", PENDING 状态)。');
    }

    // 1b. 疑似决策但没用 [Decision] 前缀（扩大检测范围）
    const decisionVerbs = /确认|选定|采用|决定用|推荐|建议采用|选择了|最终选|采纳|敲定/i;
    const decisionObjects = /方案|架构|算法|选型|框架|路线|技术栈|模型|工具|引擎|策略|组件|库|approach|solution/i;
    if (decisionVerbs.test(msg) && decisionObjects.test(msg) && !/\[Decision\]/i.test(msg) && !/\[Decision-Review\]/i.test(msg)) {
      block('疑似决策未记录。如果本轮做出了技术决策，必须 add_memory [Decision] + [Decision-Review](PENDING)。');
    }

    // 1c. 向用户展示技术方案但未调用 /深度澄清
    const askedUserDecision = /你(觉得|认为|看|倾向|选|认可|接受).*[？?]|符合.*预期.*[？?]|你.*意见|认可.*方向.*[？?]|选.*还是/i.test(msg);
    const hasTechContent = /算法|架构|模型|pipeline|向量|embedding|索引|检索|分布式|缓存|数据库|API|微服务|中间件/i.test(msg);
    const usedClarify = /深度澄清|Skill.*深度澄清|Skill.*clarif/i.test(msg);
    if (askedUserDecision && hasTechContent && !usedClarify) {
      block('向用户提了技术决策问题但未调用 /深度澄清。用户是甲方，听不懂专业术语。MUST 先 Skill("深度澄清") 翻译后再提问。');
    }

    // 1d. [DD-04] 编写了代码但未提及参考的成熟案例或论文
    const wroteCode = /```(python|typescript|javascript|svelte|tsx?|jsx?)/i.test(msg);
    const hasReference = /参考|reference|论文|paper|案例|example|github.*实现|成熟.*方案|文档.*示例|官方.*文档/i.test(msg);
    if (wroteCode && !hasReference && !isRetry) {
      block('[DD-04] 编写了代码但未提及参考的成熟案例或论文。请补充实现依据（论文/GitHub repo/官方文档示例）。');
    }

    // 1e. [DD-06] Obsidian 插件代码包含反模式
    const wrotePluginCode = /createEl|createDiv|obsidian|Plugin|ItemView|Modal|SettingTab|styles\.css/i.test(msg);
    const hasAntiPattern = /innerHTML|\.style\.\w+\s*=|document\.createElement|addEventListener(?!.*registerEvent)/i.test(msg);
    if (wrotePluginCode && hasAntiPattern && !isRetry) {
      block('[DD-06] Obsidian 代码包含反模式。修复：innerHTML→setText/createEl, style.X→addClass+CSS, createElement→createEl, addEventListener→registerEvent。编辑后跑 lint:obsidian');
    }

    // 1f. Agent 完成但未记录 [Agent-Activity]
    const agentCompleted = /Agent.*完成|Agent.*returned|agent.*completed|背景.*任务.*完成|Agent.*已完成/i.test(msg);
    const hasAgentRecord = /\[Agent-Activity\]|\[Agent-Error\]/i.test(msg);
    if (agentCompleted && !hasAgentRecord && !isRetry) {
      block('Agent 完成但未记录。请 add_memory("[Agent-Activity] {agent类型} — 修改了哪些文件+原因", group_id: "canvas-dev")。如有错误记 "[Agent-Error]"。');
    }

    // 1g. [DD-10] 引入新功能但未评估用户刚需
    const introducedFeature = /新增.*功能|添加.*功能|引入.*功能|实现.*新.*特性|加入.*能力/i.test(msg);
    const checkedNeed = /刚需|MVP.*清单|用户.*需求|用户.*初衷|search_memory_facts.*初衷|search_memory_facts.*刚需/i.test(msg);
    if (introducedFeature && !checkedNeed && !isRetry) {
      block('[DD-10] 引入了新功能但未评估是否为用户刚需。请对照 MVP 刚需 14 项清单，或 search_memory_facts 检索用户初衷。');
    }

    // 2. 代码审查闭环（brainstorm/deep explore 场景）
    const inExplore = /brainstorm|deep.?explore|方案.*调研|技术.*调研/i.test(msg);
    const analyzedCode = /成熟度.*%|已实现.*%|可复用|可直接复用|需修复|需重写|代码.*分析|逐文件/i.test(msg);
    if (inExplore && analyzedCode && !/\[Code-Review\]|独立.*审查|adversarial.*review/i.test(msg)) {
      block('代码分析无独立审查。启动独立 agent 记录 [Code-Review]（可复用/需修复/需重写）。');
    }

    // 2b. ⛔ 有文件修改但未 commit — 用 git status 检查实际未提交文件
    const mentionedCommit = /git commit|git add|git push|已提交|已推送|commit.*完成|push.*完成|备份.*完成/i.test(msg);
    if (!mentionedCommit && !isRetry) {
      try {
        const { execSync } = require('child_process');
        const projectDir = process.env.CLAUDE_PROJECT_DIR || '';
        const gitOut = execSync('git status --porcelain', { cwd: projectDir, encoding: 'utf8', timeout: 5000 });
        // Filter to only modified/added tracked files (M/A/??), exclude .claude/ and non-code files
        const uncommitted = gitOut.split('\n').filter(l => {
          if (!l.trim()) return false;
          const f = l.slice(3).trim();
          // Skip files outside git repo or in .claude/ directory
          if (f.startsWith('.claude/') || f.startsWith('"')) return false;
          // Only flag source code files
          return /\.(tsx?|jsx?|py|rs|css|html|json)$/i.test(f);
        });
        if (uncommitted.length > 0) {
          const fileList = uncommitted.map(l => l.slice(3).trim()).slice(0, 5);
          block('⛔ git status 发现 ' + uncommitted.length + ' 个源码文件未 commit。文件：' + fileList.join(', ') + '。请 git add + git commit + git push。');
        }
      } catch (e) { /* git status 失败时不阻止 */ }
    }

    // 2c. ⛔ DD-11 并行Agent完成后未验证管道打通性
    const parallelAgentsDone = /并行.*完成|Agent.*全部完成|3.*个.*Agent.*完成|两个.*Agent.*完成/i.test(msg);
    const mentionedWiring = /接线|管道.*打通|调用链|调用方|Grep.*调用|wir(e|ing)|pipeline.*connect/i.test(msg);
    const mentionedReview = /\[Code-Review\]|代码审查|code.?review|BMAD.*审查|对抗性.*审查/i.test(msg);
    if (parallelAgentsDone && !mentionedWiring && !mentionedReview && !isRetry) {
      block('⛔ DD-11 并行Agent完成但未验证管道打通性。必须检查每个新函数是否有调用方（Grep验证），无调用方=死代码，必须接线。');
    }

    // ===== 低优先级检测（stop_hook_active 时跳过，防无限循环）=====
    if (isRetry) { process.exit(0); }

    // 3. 已 add_memory → 放行
    if (hasAdd) { process.exit(0); }

    // 4. 只搜索 + 有重要产出 → block
    const hasImportant = /决策|选定|结论|共识|发现.*bug|修复了|新增.*功能|确认.*方向|方案确定|反馈.*规则/i.test(msg);
    if (hasSearch && hasImportant) {
      block('搜索了但未记录。本轮有重要产出，请 add_memory。');
    }

    // 5. 无任何 Graphiti 操作 → block
    if (!hasAdd && !hasSearch) {
      block('无 Graphiti 操作。评估是否需要 add_memory 记录本轮新信息。');
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write('Stop hook error: 检查是否需要 add_memory。');
    process.exit(2);
  }
});
