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

## ⛔ DD-11 管道打通性验证（并行开发铁律）

> **历史教训（S18-4）**：并行 Agent 按文件隔离开发时，"跨文件接线"被系统性遗漏——函数实现了但没人调用。
> 2-8 的 progressive_scope_search、expand_neighbors，2-9 的 multimodal 检索节点全是死代码。

### 规则
- **新增任何函数/方法后**，必须验证其调用链：谁调用它？从 API 入口到此函数的完整路径是否存在？
- **并行开发时**，如果 Agent 被限制"只改文件 X"，则必须在 prompt 中明确要求："完成后列出需要在其他文件中添加的调用点"
- **开发 Agent 完成后，主 Agent 负责跨文件接线**——检查每个新函数是否有调用方，没有则立即接入

### 并行开发 Agent prompt 模板
```
⛔ 管道打通性：你新增的每个函数/方法，必须在输出 summary 中列出：
1. 函数名 + 文件路径
2. 预期调用方（哪个文件的哪个函数应该调用它）
3. 如果你被限制不能修改调用方文件，明确标注"⚠️ 需要主 Agent 接线"
```

### 主 Agent 接线检查
并行 Agent 完成后，主 Agent 必须：
1. 收集所有"⚠️ 需要主 Agent 接线"标注
2. 逐个在调用方文件中添加调用
3. 运行 Grep 验证每个新函数至少有 1 个调用点（排除定义自身和测试）

## ⛔ Story 开发完成后强制检查清单

每个 Story 开发完成后，**必须执行以下两步，缺一不可**：

1. **⛔ 对抗性代码审查** — 使用 `Skill("bmad-bmm-code-review")` 执行 BMAD 规定的对抗性审查
   - ⛔ 优先使用 `/bmad-bmm-code-review`，不要用自定义 Agent 替代
   - 审查维度：Mock/假实现、管道打通性、逻辑正确性、安全性、错误处理
   - 输出 `[Code-Review]` 评级（可复用/需修复/需重写）+ 问题清单
   - 审查发现的问题必须修复后再 commit
   - ⛔ 开发 Agent 和审查 Agent 必须是不同的 Agent

2. **⛔ Commit + Push** — 审查通过后立即提交
   - `git add` 相关文件 → `git commit` → post-commit hook 自动 push backup
   - 不要积攒多个 Story 的改动再一起提交
   - commit message 需注明 Story 编号和关键改动
