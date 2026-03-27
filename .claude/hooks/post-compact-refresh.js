/**
 * PostCompact — 上下文压缩后重新注入核心规则
 * 防止压缩后规则权重衰减
 */
process.stdout.write(
  '⛔⛔⛔ 上下文已压缩 — 核心规则重新加载:\n' +
  '1. 每轮 Graphiti: search_memory_facts → 回复 → add_memory\n' +
  '2. DD-03 禁mock | DD-04 参考案例落地(Context7+WebSearch)\n' +
  '3. DD-05 前端先Pencil | DD-06 Obsidian适配(禁innerHTML/inline style/createElement)\n' +
  '4. DD-10 新功能对照MVP刚需14项 | DD-12 范围约束(frontend只改前端)\n' +
  '5. 代码审查必须独立Agent | 技术决策先 Skill("深度澄清")\n' +
  '6. Agent 完成后 add_memory("[Agent-Activity]") 记录修改文件+原因\n' +
  '7. Agent 错误记 "[Agent-Error]"\n' +
  '8. 读取 docs/known-gotchas.md 刷新已知Bug记忆\n' +
  '⛔ 读取 .claude/rules/development-discipline.md 刷新完整规则'
);
