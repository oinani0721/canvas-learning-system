/**
 * Session Start — v2 增加开发纪律强制读取
 */
process.stdout.write(
  '⛔⛔⛔ Session启动强制执行（不可跳过）:\n' +
  '1. search_memory_facts("Session-Start", group_ids:["canvas-dev"])\n' +
  '2. search_memory_facts("{话题关键词}", group_ids:["canvas-dev"])\n' +
  '3. add_memory("[Session-Start] {主题}", group_id:"canvas-dev")\n' +
  '4. ⛔ 读取 .claude/rules/development-discipline.md 中的10条开发纪律(DD-01~DD-10)\n' +
  '⛔ 10条铁律摘要(违反=功能性错误):\n' +
  'DD-01:功能必须有论文/案例(Context7+WebSearch查证) | DD-02:符合用户初衷和实际代码 | DD-03:禁mock/模拟 | DD-04:参考成熟案例落地(禁东拼西凑)\n' +
  'DD-05:前端先Pencil范式 | DD-06:Obsidian适配 | DD-07:对抗性测试 | DD-08:Graphiti搜用户初衷 | DD-09:不确定就增量提问 | DD-10:新功能对照MVP刚需清单'
);
