/**
 * Session Start — v4 强制读取决策索引+刚需+规则 + max_facts=30
 */
process.stdout.write(
  '⛔⛔⛔ Session启动强制执行（不可跳过）:\n' +
  '1. search_memory_facts("Session-Start", group_ids:["canvas-dev"], max_facts:30)\n' +
  '2. search_memory_facts("{话题关键词}", group_ids:["canvas-dev"], max_facts:30)\n' +
  '3. add_memory("[Session-Start] {主题}", group_id:"canvas-dev")\n' +
  '4. ⛔⛔⛔ 使用Read工具读取以下3个文件（不可跳过）:\n' +
  '   - Read("_decisions/decision-log.md") — 所有历史决策索引（Graphiti保底）\n' +
  '   - Read(".claude/rules/development-discipline.md") — 10条开发纪律+决策沟通+代码审查\n' +
  '   - search_memory_facts("MVP 刚需 14项", group_ids:["canvas-dev"], max_facts:30) — 刚需清单\n' +
  '5. 所有search_memory_facts调用必须传 max_facts:30（默认10太少会漏掉决策）\n' +
  '6. 在第一次回复中确认已读取规则、刚需和决策索引'
);
