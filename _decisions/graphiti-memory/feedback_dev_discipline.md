---
name: 10条开发纪律铁律 — 用户多次强调必须强制执行
description: 用户2026-03-16反复强调的10条开发纪律规则，新session仍然被无视，必须最高优先级执行
type: feedback
---

用户多次明确要求（2026-03-16反复强调，新session仍被无视）：

**⛔ 10条开发纪律（DD-01~DD-10）— 违反任何一条 = 功能性错误**

1. **DD-01** 每条功能必须有学术论文/成熟案例支撑 → ⛔ Context7+WebSearch 实际查证
2. **DD-02** 符合项目实际情况和用户初衷 → ⛔ search_memory_facts 搜索用户初衷
3. **DD-03** 禁止 mock/模拟实现 → 编辑后 LSP/ruff 审核
4. **DD-04** 参考成熟案例落地 → ⛔ Context7+WebSearch 查参考实现，禁止东拼西凑
5. **DD-05** 前后端先 Pencil 创建界面范式 → 展示给用户确认后再编码
6. **DD-06** Obsidian 环境适配 → CSS隔离/Plugin API/主题兼容
7. **DD-07** 对抗性测试 → 真实数据严苛测试
8. **DD-08** Graphiti 用户初衷 → 功能开发以用户初衷为首位
9. **DD-09** 增量提问 → 不确定就问用户，可用 Pencil 展示
10. **DD-10** 防功能蔓延 → 对照 MVP 刚需 14 项清单

**Why:** 用户已反复提出这些规则但 Claude Code 持续无视。这是用户最重要的反馈之一。

**How to apply:** 每轮回复前自检：编码→DD-03/04、新功能→DD-10、前端→DD-05、决策→DD-08。详见 `.claude/rules/development-discipline.md`。

**⛔ Story 开发后强制两步（2026-03-18 用户要求加强）：**
1. ⛔ 使用 `Skill("bmad-bmm-code-review")` 执行 BMAD 对抗性代码审查 → 记录 [Code-Review]
   - 不要用自定义 Agent 替代，必须用 BMAD 的 /bmad-bmm-code-review
2. 审查通过后立即 commit + push（post-commit hook 自动 push backup）
已通过 stop hook + user prompt hook + rules 三重强制。

**⛔ DD-11 管道打通性（2026-03-18 并行开发教训）：**
- 并行 Agent 按文件隔离时，"跨文件接线"会被系统性遗漏
- 新增函数必须有调用方，否则=死代码
- 并行 Agent prompt 必须包含"列出需要主 Agent 接线的函数"
- 主 Agent 完成后必须 Grep 验证每个新函数至少有 1 个调用点
- 已加入 stop hook + user prompt hook + rules 强制检查

**⛔ DD-12 前端调用链验证（2026-03-18 68场景审计教训）：**
- Story AC 只验证"后端 API 能工作"，不验证"前端能调用 API"
- 结果：58 Story done 但 68 场景只 59% 覆盖（检验白板 14 场景零 UI）
- 规则：Story 完成标准必须包含"前端→API 调用链存在"验证
- DD-11 检查函数级调用链，DD-12 检查前端→后端 API 层调用链
