# Decision Log（本地索引 — Graphiti 双写保底）

> **每次 add_memory [Decision] 时，同步追加一行到此文件。**
> **新 session 启动时 Read 此文件获取所有历史决策。**
> **格式：日期 | 决策编号 | 标题 | 状态 | 简述**

---

## 已确认决策

| 日期 | 编号 | 标题 | 状态 | 简述 |
|------|------|------|------|------|
| 2026-03-15 | #11 | 四层搜索+A-RAG | ✅ 确认 | RAG+CLI+Graphiti+Grep 四层路由 + A-RAG 回源验证 + Reranker 升级 |
| 2026-03-15 | #1-15 | 15项PRD决策 | ✅ 全部确认 | 用户逐项增量确认，详见 memory/decision_15_incremental_confirmed.md |
| 2026-03-15 | Mode D | Mode D 架构 | ✅ 确认(Review PENDING) | MCP暴露+Tool-UI Bridge+LiteLLM+Ollama+6层防御 |
| 2026-03-16 | DD-01~10 | 10条开发纪律 | ✅ 固化 | 学术实证/符合实际/禁mock/参考案例/Pencil/Obsidian/测试/Graphiti/增量提问/防蔓延 |
| 2026-03-16 | MVP刚需 | 14项+2底层 | ✅ 用户确认 | 见 memory/project_mvp_essentials.md |
| 2026-03-16 | Edge策略 | Edge对话2重策略 | ✅ 确认 | 用户改为2重（非PRD原版3重） |
| 2026-03-16 | RAG级别 | L1+L2都要 | ✅ 确认 | 智能路由+自动重检索 |
| 2026-03-16 | 安装引导 | 延后 | ✅ 确认 | 先写文档 |
| 2026-03-16 | 精通度通知 | 延后 | ✅ 确认 | 先能考就行 |
| 2026-03-16 | 冷启动诊断 | 删除 | ✅ 确认 | V-01：设计前提不成立 |
| 2026-03-16 | Hook强制读取 | session-start强制Read+Stop阻止未读 | Review PENDING | 验证session未分配 |
| 2026-03-16 | 规则精简 | 616行→140行 | ✅ 实施 | 官方建议<150行，合并3个rules为1个 |
| 2026-03-16 | 双写模式 | Graphiti+本地decision-log | ✅ 实施中 | 解决Graphiti搜索不到已记录决策的问题 |
| 2026-03-16 | Epic结构 | 7个Epic覆盖96FR | ✅ 用户确认 | E1画布→E2检索→E3对话→E4Edge→E5精通度→E6检验白板→E7质量 |
| 2026-03-16 | 对话引擎 | Spawn官方CLI+订阅额度 | ✅ 确认(Review PENDING) | Claude Agent SDK spawn官方Claude Code CLI，用户订阅额度。参考Claudian/Pencil/Zed ACP。Fallback: API Key |

## 待验证决策（Decision-Review PENDING）

| 日期 | 标题 | 需验证的维度 |
|------|------|------------|
| 2026-03-15 | Mode D 架构 | MCP暴露可行性、Tool-UI Bridge延迟、LiteLLM稳定性 |
| 2026-03-16 | Hook强制读取规则 | 新session是否实际Read文件并遵守规则 |
| 2026-03-16 | Epic结构 | Epic边界清晰、FR覆盖完整、依赖链正确、Story可独立交付 |
| 2026-03-16 | 对话引擎Spawn CLI | spawn模式长期稳定性(政策风险)、per-node session性能、stream-json实时性、MCP动态注入可靠性、Fallback切换成本 |
