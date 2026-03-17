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

    let msg = '⛔ 回复前执行: search_memory_facts(graphiti-canvas, group_id:"canvas-dev", query:"{用户消息关键词}", max_facts:30)';

    if (isCodeExplore) {
      msg += '\n⛔ 代码场景：必须启动独立 agent 对抗性审查，记录 [Code-Review]。详见 CLAUDE.md。';
    }

    if (isDecisionScene) {
      msg += '\n⛔ 决策场景：向用户解释技术方案时，MUST 先调用 Skill("深度澄清") 将技术概念翻译为用户可理解的语言。用户是甲方，听不懂专业术语。';
    }

    if (isImplScene) {
      msg += '\n⛔ 实施场景[DD-03/04]: Context7+WebSearch查证成熟案例→参考落地→LSP检查→禁止mock';
    }

    if (isNewFeature) {
      msg += '\n⛔ 新功能[DD-10]: 先思考是否为用户刚需？search_memory_facts检索用户初衷和MVP刚需清单';
    }

    if (isFrontend) {
      msg += '\n⛔ 前端[DD-05]: 先用Pencil创建界面范式，展示给用户确认流程后再编码';
    }

    process.stdout.write(msg);
  } catch (e) {
    process.stdout.write('⛔ 回复前执行 search_memory_facts。');
  }
});
