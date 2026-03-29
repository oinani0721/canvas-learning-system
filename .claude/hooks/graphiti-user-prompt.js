/**
 * Graphiti UserPromptSubmit — v4 精简版
 *
 * v4 改进（基于 Gemini 诊断 R2）：
 * - 移除全量 DD 规则注入（由 hooks 自动执行，不需要文字提醒）
 * - 保留精准场景检测，但只注入 1-2 条相关规则而非全部
 * - Graphiti 搜索从 max_facts:30 缩减到 max_facts:10
 * - 豁免短消息（≤3字符）
 */
const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const prompt = (data.prompt || data.user_message || '').trim();
    if (prompt.length <= 3) { process.exit(0); }

    let msg = 'search_memory_facts(group_id:"canvas-dev", query:"{关键词}", max_facts:10, exclude_invalidated:true)';

    // 只在明确匹配时注入精准提醒，不泛化
    if (/新功能|新增.*功能|添加.*功能/i.test(prompt)) {
      msg += '\n[DD-10] 新功能需对照 MVP 刚需清单。';
    }

    if (/前端.*设计|UI.*设计|界面.*设计|画.*界面/i.test(prompt)) {
      msg += '\n[DD-05] 前端设计先用 Pencil 创建范式。';
    }

    process.stdout.write(msg);
  } catch (e) {
    process.stdout.write('search_memory_facts(exclude_invalidated:true)');
  }
});
