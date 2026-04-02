# Canvas Learning System — PRD 执行清单 v3

> 日期：2026-03-31
> 数据来源：GDA 全量审核（40 条决策）+ 代码实现审查（13 模块）+ SuperPower PRD 审查（45 项需求）
> 格式：每条只写"做什么"，供用户逐条审核

---

## 当前状态总览

| 类别 | 已完成 | 部分完成 | 未实现 |
|------|--------|---------|--------|
| 后端模块 | 5/7 | 2/7 (RAG + Graphiti) | 0 |
| 前端模块 | 6/6 | 0 | 0 |
| SuperPower PRD 需求 | 24/45 | 11/45 | 10/45 |

---

## Epic 1: 关键 Bug 修复（阻塞其他所有工作）

### S-1: 修复后端评分 x100 溢出 Bug
- **做什么**: `agent_service.py:4052` 仍然把评分 `total_score * 100`，导致 1 分变 100 分。删除这个乘法或改为正确的归一化逻辑
- **改哪些文件**: `backend/app/services/agent_service.py`
- **怎么验证**: `pytest tests/ -k "score" && grep -n "total_score \* 100" backend/app/services/agent_service.py` 应返回 0 匹配
- **不要做**: 不要只改阈值（从 `<=1.0` 改 `<2`），要彻底删除错误的乘法逻辑
- **状态**: TODO

### S-2: 清理 ENABLE_GRAPHITI_JSON_DUAL_WRITE 残留
- **做什么**: 这个 flag 已决策废弃，但 canvas_service.py 中仍有 5+ 处引用。全部删除，直接走 Neo4j 写入
- **改哪些文件**: `backend/app/services/canvas_service.py`, `backend/.env.example`
- **怎么验证**: `grep -r "GRAPHITI_JSON_DUAL_WRITE" backend/app/` 应返回 0 匹配
- **不要做**: 不要保留 flag 作为"兼容"——决策已明确废弃
- **状态**: TODO

---

## Epic 2: 管道打通（代码存在但未连接）

### S-3: 接线 Profile Click-to-Jump（onNavigateToSource）
- **做什么**: `LearningProfile.tsx` 定义了 `onNavigateToSource` prop 但 `App.tsx:1164` 从未传入。实现导航回调，点击 Tip/Weakness 的 source 按钮跳转到对应白板节点
- **改哪些文件**: `frontend/src/App.tsx`, `frontend/src/components/profile/LearningProfile.tsx`
- **怎么验证**: 在 Profile 面板点击某个 Tip 的"跳转"按钮 → 白板应滚动到对应节点并高亮
- **不要做**: 不要只传空函数 `() => {}`，要真正实现 `reactFlowInstance.fitView({nodes: [targetNode]})`
- **状态**: TODO

### S-4: 启用 RAG LangGraph 管道（解除 env-gate）
- **做什么**: RAG 管道被 `LANGGRAPH_AVAILABLE` flag 控制，import 失败时返回空结果。确保 LangGraph 正确安装并启用
- **改哪些文件**: `backend/app/services/rag_service.py`, `backend/requirements.txt`
- **怎么验证**: `python -c "from langgraph.graph import StateGraph; print('OK')"` 且 `/api/v1/rag/search` 返回非空结果
- **不要做**: 不要删除 graceful degradation 逻辑（保留 try/except），只确保依赖正确安装
- **状态**: TODO
User: 请你解释一下这个是做什么？
### S-5: 启用 Agent Phase 2-4（解除 env-gate）
- **做什么**: agent_service.py 有 4 个 Phase 但 Phase 2-4 默认关闭。评估哪些 Phase 应该默认开启
- **改哪些文件**: `backend/.env`, `backend/app/services/agent_service.py`
- **怎么验证**: 对话中 Agent 能使用 tool calling（Phase 2）而非仅 direct API（Phase 1）
- **不要做**: 不要一次性全开——Phase 3 (Agent Graph) 和 Phase 4 (React Agent) 可能有稳定性问题
- **状态**: TODO（需用户确认开启哪些 Phase）
User：请你给我解释一下，这里你要做什么？

### S-6: Dashboard Exam History + Review 面板打通
- **做什么**: ExamCard.tsx 和 ReviewItem.tsx 组件存在但用户确认"假实现"。接入真实后端数据
- **改哪些文件**: `frontend/src/components/dashboard/ExamCard.tsx`, `frontend/src/components/dashboard/ReviewItem.tsx`
- **怎么验证**: Dashboard 显示真实的历史考试记录和复习建议（从 Neo4j 查询）
- **不要做**: 不要用 mock 数据填充
- **状态**: TODO
User：请你给我解释一下，这里你要做什么？

---

## Epic 3: Graphiti 真实集成（最大技术债）

### S-7: 修复 graphiti_client.py 假命名
- **做什么**: `graphiti_client.py` 是 4 行 stub，只 re-export neo4j_edge_client.py。函数名含"graphiti"但实际是 Neo4j Cypher。要么重命名为 `neo4j_learning_client.py`，要么真正接入 graphiti-core SDK
- **改哪些文件**: `backend/app/clients/graphiti_client.py`, 所有 import 它的文件
- **怎么验证**: `grep -r "from.*graphiti_client import" backend/app/` → 所有引用更新为新名称
- **不要做**: 不要保留误导性名称
- **状态**: TODO

### S-8: 扩展 episode_worker.py 为唯一的 Graphiti 写入路径
- **做什么**: 目前只有 episode_worker.py 真正调用 graphiti-core。确保所有学习事件都通过 `_enqueue_episode` → episode_worker → graphiti-core.add_episode 路径
- **改哪些文件**: `backend/app/services/memory_service.py`, `backend/app/services/episode_worker.py`
- **怎么验证**: 触发一次学习事件 → 检查 Neo4j 7689（Graphiti 容器）是否有新的 EpisodicNode
- **不要做**: 不要绕过队列直接调 graphiti-core（已有的队列+死信机制是正确设计）
- **状态**: TODO

### S-9: 实现 4 层搜索路由
- **做什么**: 当前只有 3 层基础搜索（Graphiti + Neo4j fulltext + memory cache），缺少决策 #11 要求的智能路由。需要实现：根据查询类型自动路由到 LanceDB / Vault Notes / Graphiti / Grep
- **改哪些文件**: `backend/app/services/memory_service.py`（或新建 `search_router.py`）
- **怎么验证**: 不同类型查询走不同通道——概念查询走 LanceDB，事实查询走 Graphiti，代码查询走 Grep
- **不要做**: 不要硬编码路由规则——用 regex 主路径 + LLM fallback（决策 S35-Step3 已确认）
- **状态**: TODO
User：我觉得你这里的相关决策还是有点过时了

---

## Epic 4: 检验白板补全

### S-10: 实现错误分类差异化补救策略
- **做什么**: layer4_rules.md 中描述了 4 种错误类型（破题/推理谬误/知识点缺失/似懂非懂）的补救策略，但没有代码消费这些策略。在 question_generator 中根据错误类型选择对应的补救方案
- **改哪些文件**: `backend/app/services/question_generator.py`, `backend/app/prompts/exam/layer4_rules.md`
- **怎么验证**: 考察中答错 → 系统根据错误类型给出不同的补救引导（而非千篇一律的"再想想"）
- **不要做**: 不要用 if-else 硬编码——用 prompt 模板 + 错误类型变量注入
- **状态**: TODO

### S-11: 考察中允许 /explain 等命令（Layer4 规则）
- **做什么**: 决策 GDA-9 确认考察中可用 /explain 等命令，AI 引导思考但不暴露答案。需要在 Layer4 prompt 中明确这个规则
- **改哪些文件**: `backend/app/prompts/exam/layer4_rules.md`
- **怎么验证**: 考察中输入 /explain → AI 给出引导性解释但不直接给答案
- **不要做**: 不要完全禁止命令——这违反了 GDA-9 决策
- **状态**: TODO（部分实现）

---

## Epic 5: 前端体验打磨

### S-12: 全局主题系统化（消除硬编码颜色）
- **做什么**: 当前 10+ 组件文件中有 169 处硬编码 Catppuccin hex 颜色。改用 CSS 变量 / Tailwind token
- **改哪些文件**: `frontend/tailwind.config.ts`, 各组件文件
- **怎么验证**: `grep -r "#1e1e2e\|#313244\|#89b4fa" frontend/src/components/` 应返回 0 匹配（全部改用变量）
- **不要做**: 不要只改部分组件——全局统一
- **状态**: TODO
User：请你给我解释一下，这里你要做什么？

### S-13: Dashboard LLM 模型管理面板
- **做什么**: Settings 页面已有 API key 管理，但缺少模型状态面板。添加一个显示当前使用的 LLM/Embedding/Reranker 模型及其状态的面板
- **改哪些文件**: `frontend/src/components/Settings.tsx`（或新建 `ModelStatusPanel.tsx`）
- **怎么验证**: Settings 页面显示当前模型名称、连接状态、最近调用耗时
- **不要做**: 不要做成复杂的模型切换器——Phase 4 只需显示状态
- **状态**: TODO

---

## Epic 6: 开发工作流基础设施

### S-14: 创建 PRD Compiler Skill（Markdown → prd.json）
- **做什么**: 编写一个 Claude Code Skill，读取审核通过的 PRD.md → 解析每个 Story → 输出 prd.json（含 id, target_files, acceptance_cmd, passes 字段）
- **改哪些文件**: 新建 `.claude/commands/compile-prd.md`
- **怎么验证**: 运行 `/compile-prd` → 生成 prd.json → `jq '.stories[] | select(.passes == false) | .id' prd.json` 输出未完成 story 列表
- **不要做**: 不要手写 prd.json——应该从 PRD.md 自动编译
- **状态**: TODO
User：这里的PRD 编写，你本身也不成熟不够全，我需要知道 像Bmad V6以及GSD 是否可以更加准确理解我的需求 ，来编写高质量的PRD？


### S-15: 修复 PostToolUse Hook 架构（mutmut → Stop hook）
- **做什么**: 当前 post-tool-router.sh 在每次编辑后运行 mutmut（太慢，3 分钟/次）。改为：PostToolUse 只运行 pytest + ruff（<5s），Stop hook 运行 mutmut + vulture（Agent 结束前一次性验证）
- **改哪些文件**: `.claude/hooks/post-tool-router.sh`, `.claude/settings.json`（新增 Stop hook）
- **怎么验证**: 编辑文件后 <5s 内收到 pytest 反馈；Agent 尝试结束时 mutmut 运行并报告存活变异体
- **不要做**: 不要完全删除 mutmut——只是换位置（PostToolUse → Stop）
- **状态**: TODO

### S-16: integrity-auditor 权限降级
- **做什么**: 当前 integrity-auditor 有 Write 权限（导致"回归平庸"）。剥夺 Write/Edit 权限，只保留 Read/Grep/Glob/Bash
- **改哪些文件**: `.claude/agents/integrity-auditor.md`
- **怎么验证**: `grep "Write\|Edit" .claude/agents/integrity-auditor.md` 应返回 0 匹配
- **不要做**: 不要给审计 Agent 任何修改代码的能力
- **状态**: TODO

---

## 已完成（不需要做）

以下模块已通过代码审查确认完成，不在 PRD 范围内：

| 模块 | 状态 | 关键文件 |
|------|------|---------|
| 检验白板考试系统 | ✅ DONE | exam_service.py (479L), ExamCanvas.tsx |
| 精通度引擎 | ✅ DONE | mastery_engine.py (656L), BKT+FSRS |
| Agent 对话引擎 | ✅ DONE | agent_service.py (5704L), sidecar.js |
| Profile 学习档案 | ✅ DONE | profile.py, LearningProfile.tsx |
| 笔记索引 | ✅ DONE | lancedb_index_service.py |
| ReactFlow 白板 | ✅ DONE | App.tsx (1220L) |
| 考试界面 | ✅ DONE | ExamCanvas.tsx, HintButton, SkipButton |
| 对话侧边栏 | ✅ DONE | ChatPanel.tsx (376L), 12+ 子组件 |
| 暗色主题基础 | ✅ DONE | index.css (Catppuccin Mocha 变量) |
| Settings 页面 | ✅ DONE | Settings.tsx (1137L) |
| Phase 3 架构裁剪 | ✅ DONE | cross_canvas + textbook 已删除 |
| Phase 3 ACP 外置 | ✅ DONE | layer3.md 模板化 |
| Phase 3 group_id 动态绑定 | ✅ DONE | extract_canvas_name + sanitize |
| Phase 3 Neo4j fulltext 索引 | ✅ DONE | ensure_fulltext_index |
| Phase 3 中文混合搜索 | ✅ DONE | jieba + hybrid search |

---

## 决策状态备忘（GDA 审核结果）

| 决策 | 状态 | 备注 |
|------|------|------|
| Agent SDK sidecar | ✅ 有效 | Tauri 2 + React + Node.js sidecar |
| 不用原生 Graphiti MCP | ✅ 有效 | 改用 FastAPI-MCP |
| SuperPower 框架 | ❌ 已废弃 | 造成高返工率 |
| Mode D → SDK → Tier B | ❌ 已被 sidecar 取代 | 3 次演化后稳定 |
| 4 层搜索 + A-RAG | ✅ 有效 | 但搜索路由未实现（S-9） |
| DD-01~DD-13 | ✅ 有效 | DD-12/DD-13 只是文本规则（hook 已移除） |
| 8 条 PENDING Decision-Review | ⚠️ 积压 | 最老的已 17 天未验证 |
