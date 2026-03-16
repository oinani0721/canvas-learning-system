# ⛔ 开发纪律 + 决策沟通 + 代码审查（合并精简版）

## DD-01~DD-10 开发纪律

| # | 规则 | 执行要求 |
|---|------|---------|
| DD-01 | 学术实证 | Context7+WebSearch 查证论文/案例。功能组合也需证据 |
| DD-02 | 符合实际 | search_memory_facts 搜用户初衷。不脱离 Obsidian 环境和实际代码 |
| DD-03 | 禁 mock | 禁 mock API/模拟数据/TODO空函数。编辑后 LSP/ruff 检查 |
| DD-04 | 参考案例 | Context7+WebSearch 查参考实现。禁止东拼西凑 |
| DD-05 | 先 Pencil | 前后端先创建 UI 范式展示给用户确认后再编码 |
| DD-06 | Obsidian | CSS隔离/Plugin API/主题兼容/Electron。Context7 查文档 |
| DD-07 | 测试 | 真实数据严苛对抗性测试 |
| DD-08 | 用户初衷 | search_memory_facts 搜 Graphiti。功能开发以用户初衷为首位 |
| DD-09 | 增量提问 | 不确定就问用户。可用 Pencil 展示。技术决策先 Skill("深度澄清") |
| DD-10 | 防蔓延 | 对照 MVP 刚需 14 项清单。不在清单中的不做 |

## 决策沟通

- 禁微观选型（k=30? sparse? 用什么模型?）→ AI 直接选最成熟方案
- 需要用户决策 → 先 Skill("深度澄清") 翻译
- 每个决策 → `[Decision]` + `[Decision-Review]`(PENDING)

## 代码审查

- 参考/复用代码 → 必须独立 Agent 审查 → `[Code-Review]`(可复用/需修复/需重写)
- 已知问题：Agent API mock、内存查询 TODO、FSRS/BehaviorTracker 未调用、agent_graph 禁用
- ⛔ 不审查就说"可复用" = 严重违规
