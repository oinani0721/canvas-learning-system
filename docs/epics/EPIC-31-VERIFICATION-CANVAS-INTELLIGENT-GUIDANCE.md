# Epic 31: 检验白板智能引导系统完整激活

## Epic 元数据

| 属性 | 值 |
|------|-----|
| **Epic ID** | EPIC-31 |
| **标题** | 检验白板智能引导系统完整激活 |
| **类型** | Brownfield Enhancement |
| **优先级** | P0 (Critical) |
| **状态** | Draft |
| **创建日期** | 2026-01-17 |
| **预计工时** | 13-16天 |
| **关联Bug** | Bug 4 (检验白板质量差) |
| **关联PRD需求** | 问题7 (Agent决策), 问题8 (历史关联) |

---

## Epic Goal

**激活检验白板的完整智能引导功能**，使用户能够：
1. 一键生成与原始Canvas关联的检验白板
2. 通过Socratic式问答验证概念理解
3. 根据回答质量获得智能引导（拆解/解释/继续）
4. 实时追踪检验进度和掌握度
5. 基于历史记录实现个性化难度自适应

---

## Epic Description

### 现有系统背景

**当前相关功能**:
- 11个Agent端点已真实实现（Gemini API调用）
- ScoringResultPanel前端决策按钮已实现
- VerificationHistoryService历史管理服务完整
- Graphiti时序记忆存储框架完整
- 记忆写入触发机制（Fire-and-Forget）已实现

**技术栈**:
- 后端: FastAPI + Python 3.11 + Gemini API
- 前端: Obsidian Plugin (TypeScript)
- 记忆: Graphiti + Neo4j + LanceDB
- 存储: Canvas JSON文件

**集成点**:
- `backend/app/services/verification_service.py` - 检验核心服务
- `backend/app/api/v1/endpoints/agents.py` - Agent端点
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 插件入口
- `backend/app/clients/graphiti_client.py` - 记忆客户端

### 增强详情

**核心问题诊断**:

经深度调研发现，检验白板"不能正式启用"的根本原因是 `verification_service.py` 中的3个关键方法为Mock实现：

| 方法 | 行号 | 当前实现 | 应有实现 |
|------|------|---------|---------|
| `start_session()` | L197 | 返回硬编码 `["概念1", "概念2"]` | 从Canvas读取红/紫节点 |
| `generate_question_with_rag()` | L751 | 返回 `f"请解释{concept}？"` | 调用Gemini API生成问题 |
| `process_answer()` | L279 | 基于字符长度评分 | 集成scoring-agent评估 |

**增强内容**:
1. 替换VerificationService的Mock实现为真实Gemini调用
2. 对接前端白板生成功能与后端API
3. 新增 `/agents/recommend-action` 智能决策端点
4. 实现检验问题去重机制
5. 基于历史得分的难度自适应算法
6. 实时进度追踪UI
7. 检验历史视图

**集成方式**:
- 遵循现有AgentService的Gemini调用模式
- 复用existing RAG上下文注入框架
- 利用已实现的记忆写入触发机制
- 扩展现有ScoringResultPanel决策按钮

**成功标准**:
- [ ] 用户可一键生成检验白板
- [ ] 检验问题与原Canvas内容高度相关
- [ ] 根据回答质量自动推荐下一步动作
- [ ] 实时显示检验进度（已验证 X/Y 个概念）
- [ ] 历史记录可查询和复用

---

## Stories

### Story 31.1: VerificationService核心逻辑激活 [P0 BLOCKER]

**描述**: 替换verification_service.py中的3个Mock实现，激活真实AI功能

**验收标准**:
- [ ] AC-31.1.1: `start_session()` 从Canvas文件读取红色(color="4")+紫色(color="3")节点并提取概念
- [ ] AC-31.1.2: `generate_question_with_rag()` 调用Gemini API生成个性化验证问题
- [ ] AC-31.1.3: `process_answer()` 集成scoring-agent评估回答（返回0-40分）
- [ ] AC-31.1.4: 所有方法支持RAG上下文注入（学习历史、教材、相关概念）
- [ ] AC-31.1.5: 500ms超时保护和优雅降级

**关键文件**:
- `backend/app/services/verification_service.py` (L197, L279, L751)
- `backend/app/services/agent_service.py` (score_node方法)

**依赖**: 无

---

### Story 31.2: 检验白板生成端到端对接 [P0 BLOCKER]

**描述**: 前端"生成检验白板"功能完整激活，从UI到后端API的完整链路

**验收标准**:
- [ ] AC-31.2.1: main.ts实现`generateVerificationCanvas`调用 `POST /review/generate` API
- [ ] AC-31.2.2: 创建新检验白板Canvas文件（命名: `{原名}_验证_{timestamp}.canvas`）
- [ ] AC-31.2.3: 在VerificationHistoryService中记录原Canvas与检验Canvas的关系
- [ ] AC-31.2.4: 生成完成后自动在Obsidian中打开新Canvas
- [ ] AC-31.2.5: 显示生成进度条（"正在生成检验白板... 预计30秒"）

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts` (L751-753)
- `canvas-progress-tracker/obsidian-plugin/src/services/ApiClient.ts`
- `backend/app/api/v1/endpoints/review.py`

**依赖**: Story 31.1

---

### Story 31.3: Agent决策推荐端点 [P1]

**描述**: 新增 `/agents/recommend-action` 智能决策端点，根据评分推荐下一步动作

**验收标准**:
- [ ] AC-31.3.1: 新增 `POST /agents/recommend-action` 端点
- [ ] AC-31.3.2: 请求参数包含 `score`, `node_id`, `canvas_name`
- [ ] AC-31.3.3: 根据评分返回推荐动作:
  - 分数 < 24: `{"action": "decompose", "agent": "/agents/decompose/basic", "reason": "概念理解不足"}`
  - 分数 24-31: `{"action": "explain", "agent": "/agents/explain/oral", "reason": "需要补充解释"}`
  - 分数 >= 32: `{"action": "next", "agent": null, "reason": "掌握良好"}`
- [ ] AC-31.3.4: 考虑历史得分趋势（如持续低分则推荐更基础的拆解）
- [ ] AC-31.3.5: 前端ScoringResultPanel对接此端点替代硬编码决策

**关键文件**:
- `backend/app/api/v1/endpoints/agents.py` (新增端点)
- `canvas-progress-tracker/obsidian-plugin/src/views/ScoringResultPanel.ts`

**依赖**: Story 31.1

---

### Story 31.4: 检验问题去重与历史查询 [P1]

**描述**: 防止生成重复检验问题，支持查询概念的检验历史

**验收标准**:
- [ ] AC-31.4.1: 问题生成前查询Graphiti检查是否已存在相同概念的验证问题
- [ ] AC-31.4.2: 若存在，生成新角度问题（应用、比较、反例等）或返回已有问题
- [ ] AC-31.4.3: 新增 `GET /verification/history/{concept}` 端点查询概念检验历史
- [ ] AC-31.4.4: 历史数据包含：问题内容、用户回答、得分、时间戳

**关键文件**:
- `backend/app/services/verification_service.py` (generate_question_with_rag)
- `backend/app/clients/graphiti_client.py` (新增search_verification_questions)

**依赖**: Story 31.1

---

### Story 31.5: 难度自适应算法 [P2]

**描述**: 根据历史得分自动调整问题难度，实现个性化学习

**验收标准**:
- [ ] AC-31.5.1: 查询概念的历史得分（最近5次）
- [ ] AC-31.5.2: 计算难度等级:
  - 平均分 >= 32 → `hard` (应用型问题)
  - 平均分 24-31 → `medium` (验证型问题)
  - 平均分 < 24 → `easy` (突破型问题)
- [ ] AC-31.5.3: 根据难度选择问题类型（突破/验证/应用）
- [ ] AC-31.5.4: 支持跳过已掌握概念（连续3次得分>=32）
- [ ] AC-31.5.5: 遗忘检测：若最近得分显著低于历史平均，标记为"需要复习"

**关键文件**:
- `backend/app/services/verification_service.py`
- `backend/app/services/memory_service.py` (get_learning_history)

**依赖**: Story 31.4

---

### Story 31.6: 实时检验进度追踪 [P2]

**描述**: 用户可实时查看检验进度和掌握度

**验收标准**:
- [ ] AC-31.6.1: 前端显示"已验证 X/Y 个概念"进度条
- [ ] AC-31.6.2: 颜色分布实时更新:
  - 绿色(>=32): 掌握
  - 黄色(24-31): 部分掌握
  - 紫色(16-23): 需复习
  - 红色(<16): 未掌握
- [ ] AC-31.6.3: 掌握度百分比计算 = 绿色数 / 总数 * 100%
- [ ] AC-31.6.4: 支持暂停/继续检验会话
- [ ] AC-31.6.5: 会话计时器显示已用时间

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/src/modals/VerificationProgressModal.ts`
- `backend/app/services/verification_service.py` (新增get_session_progress)

**依赖**: Story 31.2

---

### Story 31.7: 检验历史视图UI [P2]

**描述**: 在ReviewDashboardView中实现"验证"标签页，展示检验历史

**验收标准**:
- [ ] AC-31.7.1: ReviewDashboardView新增"验证"标签页
- [ ] AC-31.7.2: 显示检验白板列表（按创建时间排序）
- [ ] AC-31.7.3: 每个条目显示：原Canvas名、检验Canvas名、会话次数、最高得分、最近检验时间
- [ ] AC-31.7.4: 点击条目跳转到对应检验白板
- [ ] AC-31.7.5: 支持删除检验白板记录

**关键文件**:
- `canvas-progress-tracker/obsidian-plugin/src/views/ReviewDashboardView.ts`
- `canvas-progress-tracker/obsidian-plugin/src/services/VerificationHistoryService.ts`

**依赖**: 无（可与其他Story并行）

---

## Compatibility Requirements

- [x] 现有Agent API保持不变（仅新增端点）
- [x] Canvas文件格式遵循现有schema
- [x] VerificationHistoryService数据结构向后兼容
- [x] UI变更遵循现有Obsidian插件风格
- [x] 性能影响最小（记忆写入使用Fire-and-Forget模式）

---

## Risk Mitigation

**主要风险**: VerificationService重构可能影响现有review功能

**缓解措施**:
1. 保留原有Mock实现作为降级路径（USE_MOCK_VERIFICATION环境变量）
2. 分阶段发布：先激活核心功能(31.1-31.2)，再增强(31.3-31.7)
3. 全面的单元测试覆盖（目标95%）

**回滚计划**:
1. 恢复verification_service.py到Mock实现
2. 前端main.ts恢复"功能开发中"提示
3. 不影响其他Agent和Review功能

---

## Definition of Done

- [ ] Story 31.1-31.2 完成（P0 BLOCKER）
- [ ] Story 31.3-31.4 完成（P1）
- [ ] Story 31.5-31.7 完成（P2，可选）
- [ ] 单元测试覆盖率 >= 95%
- [ ] 端到端测试通过（生成 → 问答 → 决策 → 进度追踪）
- [ ] 无回归（现有Agent和Review功能正常）
- [ ] 文档更新（API文档、用户指南）

---

## Validation Checklist

### Scope Validation

- [x] Epic可在7个Stories内完成（符合brownfield标准）
- [x] 遵循现有AgentService和RAG模式
- [x] 集成复杂度可控（主要是替换Mock）
- [x] 风险可控（有降级和回滚方案）

### Risk Assessment

- [x] 对现有系统风险低（新增功能为主）
- [x] 回滚计划可行
- [x] 测试覆盖现有功能
- [x] 团队熟悉相关代码

### Completeness Check

- [x] Epic目标清晰
- [x] Stories范围合理
- [x] 成功标准可测量
- [x] 依赖关系明确

---

## Story Manager Handoff

> **Story Manager请开发以下Stories的详细用户故事**。关键注意事项：
>
> - 这是对现有Canvas学习系统的增强
> - 技术栈: FastAPI + TypeScript Obsidian Plugin + Gemini API
> - 集成点: verification_service.py, agents.py, main.ts
> - 现有模式: Fire-and-Forget记忆写入, RAG上下文注入, 500ms超时保护
> - 关键兼容性要求: 现有Agent API不变，Canvas格式不变
> - 每个Story必须包含验证现有功能完整性的测试
>
> Epic目标: **激活检验白板智能引导系统，实现一键生成、AI问答、智能决策、进度追踪**

---

## Appendix: 调研数据

### 当前实现完成度

| 组件 | 完成度 | 说明 |
|------|--------|------|
| 后端Agent端点 | 95% | 11个端点真实实现 |
| VerificationService | 15% | 核心逻辑为Mock |
| 前端评分面板 | 95% | 按钮已实现 |
| 前端白板生成 | 5% | 仅显示"开发中" |
| 记忆系统集成 | 65% | 框架完整，去重/自适应缺失 |

### 关键文件路径

```
backend/
├── app/services/verification_service.py    # 核心检验逻辑 (824行)
├── app/services/agent_service.py           # Agent执行 (3564行)
├── app/api/v1/endpoints/agents.py          # Agent端点 (1700行)
├── app/api/v1/endpoints/review.py          # Review端点 (500行)
└── app/clients/graphiti_client.py          # 记忆客户端 (754行)

canvas-progress-tracker/obsidian-plugin/
├── main.ts                                 # 插件入口 (L751: 白板生成)
├── src/views/ScoringResultPanel.ts         # 评分面板 (482行)
├── src/modals/VerificationProgressModal.ts # 进度Modal (680行)
└── src/services/VerificationHistoryService.ts # 历史服务 (304行)
```
