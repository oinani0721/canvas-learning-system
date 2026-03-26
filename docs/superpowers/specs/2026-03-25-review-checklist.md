# 对抗性审查检查清单 — Writing Plans 必须逐条处理

> **来源**: S27 对抗性审查（4 Agent）| **状态**: Writing Plans 实施时逐条勾选
> **规则**: 每写一个 Story/Task 时，检查此清单中是否有对应项未处理

---

## 一级问题（阻塞性，必须在 Writing Plans 中有对应 Task）

- [ ] **MCP 6 工具迁移缺具体步骤** — record_learning_memory / search_memories / record_error / search_notes / archive_conversation / generate_question 每个工具需要单独的 Task，说明：改哪个文件、改什么调用、怎么验证
- [ ] **Phase 2→3 隐含依赖** — 3.5(格式修复)依赖 2.2(Worker)完成；3.6(补救策略消费)依赖 2.6(PostToolUse)完成。Writing Plans 中必须声明 blockedBy 关系
- [ ] **决策 #11 四层搜索 vs GDA 索引** — #11 是历史决策（2026-03-15），非 S27 GDA 系列。Phase 3 中需要有搜索路由的具体实施 Task

## 二级问题（验收标准缺失，每个 Task 必须有验收条件）

- [ ] Phase 2.1 删除死代码 → 验收："ruff check 无死代码调用失败"
- [ ] Phase 2.4 假命名清理 → 验收分级："CRITICAL 3个 + HIGH N个 + MEDIUM N个 各自确认"
- [ ] Phase 2.3 临界交换风险 → 风险："Bridge 层替换中部分调用未迁移" + 缓解："git 分支 + 回滚计划"
- [ ] Phase 1.1 .env.example 同步 → 验收：".env.example NEO4J_URI 已更新为 7691"
- [ ] Phase 1.1 CSP 配置 → 验收分阶段："开发 csp:null 验证 + 上线前定向放行验证"

## 三级问题（逻辑一致性，Writing Plans 中澄清）

- [ ] GDA-3 定义范围 → group_id 用于两处：Graphiti Worker group_id + vault_notes subject 参数。确认用同一命名规则
- [ ] PostToolUse BEA 4维度 → 待调研项，Writing Plans 前需完成调研，定义触发条件和数据字段
- [ ] Phase 3.3 prompt layer3 外部化 → 确认 layer1/2/4/5 已存在不需重建，仅 layer3 需新建
- [ ] 决策索引"10项"→ 仅指 S27-GDA 系列。GDR-P0/P1 和 DE 系列是历史决策，在正文中引用但不在 S27 索引中

## 四级问题（实施细节，每个 Story 中自然覆盖）

- [ ] Phase 3.8 /命令规则 → 指明具体文件 backend/prompts/exam/layer4_rules.md 的修改位置
- [ ] Phase 3.1 Sidecar 验收 → 补充深层验收：JSON流解析正确 / 4态状态机 / IPC<100KB / HTTP降级
- [ ] Phase 4.3 上下文管理 → 补充决策来源和优先级

## MVP 覆盖缺口（Writing Plans 中处理方式）

- [ ] #8 Edge 对话 2重策略 → Phase 3 补充 Edge Prompt 设计 Task（或延后到 Phase 4+）
- [ ] #12 Claude Code 迁移 → Phase 3.1 Sidecar 验证本质就是 #12，显式标注 "此 Task 覆盖 MVP #12"

## 用户批注未充分处理项（标记为"待调研"的不算遗漏）

- [ ] Session 上下文双层记忆 → 待调研（Claudian 参考），Writing Plans Phase 4 Task
- [ ] #5 record_learning_memory BEA 提取细节 → 待调研（DD-04），Writing Plans Phase 2 Task
- [ ] #6 检验白板拉出节点一致性 → create_exam_node 与 usePullToNode 行为对齐验证 Task
- [ ] #13 完整迁移 Claude Code 命令 → Claudian 命令清单调研 Task
