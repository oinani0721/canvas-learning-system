/**
 * Graphiti UserPromptSubmit — v3 增加开发纪律场景检测 (DD-03/04/05/10)
 * 豁免：≤3 字符纯确认消息
 */
const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const prompt = (data.prompt || data.user_message || '').trim();
    if (prompt.length <= 3) { process.exit(0); }

    const isCodeExplore = /deep.?explore|代码.*分析|分析.*代码|brainstorm|调研|重构|code.*review/i.test(prompt);
    const isDecisionScene = /选型|方案|对比|比较|选择|推荐|建议|哪个好|怎么选|用什么|架构.*决策|技术.*路线|算法.*选/i.test(prompt);
    const isImplScene = /impl|实现|编码|开发|写代码|落地|实施|编写|创建.*服务|创建.*组件/i.test(prompt);
    const isNewFeature = /新功能|新增|引入|扩展|添加.*功能|加个|顺便/i.test(prompt);
    const isFrontend = /前端|UI|界面|组件|Svelte|样式|白板.*设计|面板/i.test(prompt);
    const isObsidianPlugin = /obsidian|plugin|插件|canvas.*plugin|modal|view|settings.*tab|css.*style|dom|createEl|main\.ts/i.test(prompt);

    let msg = '⛔ 回复前执行: search_memory_facts(graphiti-canvas, group_id:"canvas-dev", query:"{用户消息关键词}", max_facts:30, exclude_invalidated:true)';

    if (isCodeExplore) {
      msg += '\n⛔ 代码场景：必须启动独立 agent 对抗性审查，记录 [Code-Review]。详见 CLAUDE.md。';
    }

    if (isDecisionScene) {
      msg += '\n⛔ 决策场景：向用户解释技术方案时，MUST 先调用 Skill("深度澄清") 将技术概念翻译为用户可理解的语言。用户是甲方，听不懂专业术语。';
      msg += '\n⛔ DD-01/04 技术组合验证：提出任何多组件组合前，必须 WebSearch 验证组合的社区成功案例。未验证的组合必须标注❌并向用户增量提问确认。禁止拼凑未经验证的组合。';
    }

    if (isImplScene) {
      msg += '\n⛔ 实施场景[DD-03/04]: Context7+WebSearch查证成熟案例→参考落地→LSP检查→禁止mock';
      msg += '\n⛔ 开发完成后必须：(1) 启动独立 Agent 对抗性代码审查→记录[Code-Review] (2) commit + push backup';
      msg += '\n⛔ DD-11 管道打通性：并行Agent完成后，主Agent必须检查每个新函数是否有调用方。无调用方=死代码，必须接线。';
      msg += '\n⛔ DD-07 用户验收：代码修改后必须提供最小验收步骤（如何启动→如何操作→预期看到什么），让用户在实际产品中看到变化。';
    }

    if (isNewFeature) {
      msg += '\n⛔ 新功能[DD-10]: 先思考是否为用户刚需？search_memory_facts(exclude_invalidated:true)检索用户初衷和MVP刚需清单';
    }

    if (isFrontend) {
      msg += '\n⛔ 前端[DD-05]: 先用Pencil创建界面范式，展示给用户确认流程后再编码';
    }

    if (isObsidianPlugin) {
      msg += '\n⛔ DD-06 注意：产品已迁移至 Tauri+React（frontend/src/）。' +
        '\n  - 主产品前端用 React 规范，不用 Obsidian Plugin API' +
        '\n  - 如果修改 legacy Obsidian 插件（canvas-progress-tracker/），仍需遵守 Obsidian 规范' +
        '\n  - 禁止在 frontend/src/ 中使用 createEl/registerEvent/ItemView 等 Obsidian API';
    }

    process.stdout.write(msg);
  } catch (e) {
    process.stdout.write('⛔ 回复前执行 search_memory_facts(exclude_invalidated:true)。');
  }
});
