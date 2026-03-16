# CLAUDE.md

> ## ⛔⛔⛔ 铁律（违反 = 功能性错误）
>
> 1. **每轮 Graphiti** — 回复前 `search_memory_facts(group_id:"canvas-dev")`，回复后评估 `add_memory`
> 2. **决策必须 `[Decision-Review]`** — PENDING，独立 session 验证
> 3. **代码审查必须独立 Agent** — 代码库有 mock/stub/断裂管道，不可默认正确。记录 `[Code-Review]`
> 4. **技术决策先 `Skill("深度澄清")`** — 用户是甲方，听不懂术语
> 5. **DD-01 学术实证** — Context7+WebSearch 查证论文/案例，功能组合也需证据
> 6. **DD-02 符合实际** — search_memory_facts 搜用户初衷，不脱离 Obsidian 环境
> 7. **DD-03 禁 mock** — 禁止假 API/模拟数据/TODO空函数，编辑后 LSP 检查
> 8. **DD-04 参考案例落地** — Context7+WebSearch 查参考实现，禁止东拼西凑
> 9. **DD-05 先 Pencil** — 前后端先创建 UI 范式展示给用户确认
> 10. **DD-06 Obsidian 适配** — CSS隔离/Plugin API/主题兼容
> 11. **DD-07 对抗性测试** — 真实数据严苛测试
> 12. **DD-09 增量提问** — 不确定就问用户
> 13. **DD-10 防功能蔓延** — 对照 MVP 刚需 14 项清单，不在清单中不做

## Graphiti 协议

- **MCP**：`graphiti-canvas`（group_id: `canvas-dev`）
- **流程**：搜索→回复→记录。name 用 `[前缀] 标题` 格式
- **Session**：启动记 `[Session-Start]`，结束记 `[Session-End]`
- **兜底**：不确定是否记录 → 记录

## 权限

- 破坏性操作：先确认。其余：直接执行
