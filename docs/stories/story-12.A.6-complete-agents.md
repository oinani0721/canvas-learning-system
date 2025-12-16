# Story 12.A.6: 补齐剖析节点 Agent

## Status
**READY** - PO 验证通过 (2025-12-15)

## Priority
**P1** - 功能完整性，依赖 Story 12.A.1

## Story

**As a** Canvas 学习系统用户,
**I want** 右键菜单显示所有设计中的 Agent 选项,
**So that** 我可以使用完整的学习辅助功能来深度理解概念。

## Problem Statement

**当前问题**: 5个 Agent 后端端点未实现（提示词文件已存在）

```
当前可用端点 (9个):
├── 拆解类 (2个)
│   ├── /agents/decompose/basic (基础拆解)
│   └── /agents/decompose/deep (深度拆解)
├── 解释类 (6个)
│   ├── /agents/explain/oral (口语化解释)
│   ├── /agents/explain/four-level (四层次解答)
│   ├── /agents/explain/clarification (澄清路径)
│   ├── /agents/explain/comparison (对比表格)
│   ├── /agents/explain/example (例题教学)
│   └── /agents/explain/memory (记忆锚点)
└── 评分类 (1个)
    └── /agents/score (评分)

后端端点未实现 (5个，提示词已存在于 .claude/agents/):
├── verification-question (生成检验问题) ← P1 本Story实现
│   └── 提示词: .claude/agents/verification-question-agent.md ✅
├── question-decomposition (问题拆解) ← P1 本Story实现
│   └── 提示词: .claude/agents/question-decomposition.md ✅
├── canvas-orchestrator (Canvas 编排器)
│   └── 提示词: .claude/agents/canvas-orchestrator.md ✅
├── iteration-validator (迭代验证器)
│   └── 提示词: .claude/agents/iteration-validator.md ✅
└── graphiti-memory-agent (记忆图谱 Agent)
    └── 提示词: .claude/agents/graphiti-memory-agent.md ✅
```

**关键澄清**: Agent 提示词文件已完整存在，本 Story 目标是实现后端 API 端点和前端集成。

## Acceptance Criteria

1. 实现 `verification-question` Agent 后端端点 `/agents/verification/question`
2. 实现 `question-decomposition` Agent 后端端点 `/agents/decompose/question`
3. 所有新 Agent 端点必须:
   - a) 调用 `ContextEnrichmentService.enrich_with_adjacent_nodes()` 获取邻居节点上下文
   - b) 调用 `LearningMemoryClient.search_memories()` 注入历史学习记忆
   - c) 调用 `agent_service.record_learning_episode()` 记录学习事件
4. 右键菜单显示新增 Agent 选项
5. ApiClient 支持调用新 Agent 端点
6. 新 Agent 的响应格式与现有 `ExplainResponse`/`DecomposeResponse` 兼容

## Tasks / Subtasks

### Phase 1: verification-question Agent (P1)

- [ ] Task 1.1: 后端实现 (AC: 1, 3)
  - [ ] 在 `AgentType` 枚举中确认 `VERIFICATION_QUESTION` 存在
  - [ ] 在 agent_service.py 添加 `generate_verification_questions()` 方法
  - [ ] 定义 VerificationQuestionRequest/Response 模型
  - [ ] 复用现有提示词 `.claude/agents/verification-question-agent.md`
  - [ ] 在 agents.py 添加 `/agents/verification/question` 端点 (参考 `_call_explanation` 模式)

- [ ] Task 1.2: 前端集成 (AC: 4, 5)
  - [ ] 在 ApiClient.ts 添加 `generateVerificationQuestions()` 方法
  - [ ] 在 ContextMenuManager.ts 添加菜单项
  - [ ] 在 main.ts 注册命令

### Phase 2: question-decomposition Agent (P1)

- [ ] Task 2.1: 后端实现 (AC: 2, 3)
  - [ ] 在 `AgentType` 枚举中添加 `QUESTION_DECOMPOSITION = "question-decomposition"`
  - [ ] 在 agent_service.py 添加 `decompose_question()` 方法
  - [ ] 定义 QuestionDecomposeRequest/Response 模型
  - [ ] 复用现有提示词 `.claude/agents/question-decomposition.md`
  - [ ] 在 agents.py 添加 `/agents/decompose/question` 端点 (参考 `decompose_basic` 模式)

- [ ] Task 2.2: 前端集成 (AC: 4, 5)
  - [ ] 在 ApiClient.ts 添加 `decomposeQuestion()` 方法
  - [ ] 在 ContextMenuManager.ts 添加菜单项
  - [ ] 在 main.ts 注册命令

### Phase 3: 集成验证

- [ ] Task 3.1: RAG 桥接集成 (AC: 3)
  - [ ] 新端点调用 RAG 服务获取上下文
  - [ ] 新端点调用记忆服务获取历史
  - [ ] 新端点记录学习事件

- [ ] Task 3.2: 前端响应处理 (AC: 6)
  - [ ] 验证响应格式与前端兼容
  - [ ] 测试新菜单项的完整流程
  - [ ] 确保错误处理一致

## Dev Notes

### 关键文件

```
backend/app/
├── api/v1/endpoints/agents.py        # 新增端点
├── services/agent_service.py         # 新增方法
└── models/agent_models.py            # 新增模型

canvas-progress-tracker/obsidian-plugin/
├── src/api/ApiClient.ts              # 新增方法
├── src/managers/ContextMenuManager.ts # 新增菜单项
└── main.ts                           # 新增命令
```

### verification-question 实现

**AI 提示词**:
```python
VERIFICATION_QUESTION_PROMPT = """
你是一位严谨的教育评估专家。请基于以下概念生成检验问题。

## 概念内容
{content}

{rag_context}

{memory_context}

## 任务要求
请生成 5 个检验问题，用于测试学习者对此概念的理解程度：

1. **记忆层** - 直接考察定义或事实
2. **理解层** - 需要解释或举例
3. **应用层** - 需要在新情境中使用
4. **分析层** - 需要比较或推理
5. **综合层** - 需要创造性思考

## 输出格式
返回 JSON 格式：
{{
  "questions": [
    {{
      "level": "记忆层",
      "question": "...",
      "expected_answer_points": ["...", "..."]
    }}
  ]
}}
"""
```

**数据模型**:
```python
# agent_models.py
class VerificationQuestion(BaseModel):
    level: str  # 记忆层/理解层/应用层/分析层/综合层
    question: str
    expected_answer_points: list[str]

class VerificationQuestionResponse(BaseModel):
    questions: list[VerificationQuestion]
    concept: str
    generated_at: datetime
```

### question-decomposition 实现

**AI 提示词**:
```python
QUESTION_DECOMPOSE_PROMPT = """
你是一位教学设计专家。请将以下问题拆解为更小的子问题。

## 原问题
{question}

{rag_context}

## 任务要求
请将此问题拆解为 3-5 个子问题，帮助学习者逐步理解：

1. 每个子问题应该更简单、更具体
2. 子问题应该按逻辑顺序排列
3. 回答所有子问题后，应该能够回答原问题

## 输出格式
返回 JSON 格式：
{{
  "sub_questions": [
    {{
      "order": 1,
      "question": "...",
      "hint": "..."
    }}
  ],
  "synthesis_guidance": "如何将子问题答案整合为原问题答案"
}}
"""
```

### 右键菜单添加

```typescript
// ContextMenuManager.ts
const newMenuItems = [
  {
    id: 'generate-verification-questions',
    label: '生成检验问题',
    icon: '?',
    callback: async (context: NodeContext) => {
      const result = await this.plugin.apiClient.generateVerificationQuestions({
        content: context.nodeText,
        canvas_name: context.canvasName,
        node_id: context.nodeId
      });
      // 显示结果或创建新节点
    }
  },
  {
    id: 'decompose-question',
    label: '问题拆解',
    icon: '?',
    callback: async (context: NodeContext) => {
      const result = await this.plugin.apiClient.decomposeQuestion({
        question: context.nodeText,
        canvas_name: context.canvasName,
        node_id: context.nodeId
      });
      // 显示结果或创建子节点
    }
  }
];
```

### Agent 提示词文件位置

```
.claude/agents/
├── verification-question-agent.md    # 已存在
├── question-decomposition.md         # 已存在
└── ...
```

## Risk Assessment

**风险**: 低
- 遵循现有 Agent 模式
- 增量添加，不影响现有功能

**缓解措施**:
- 复用现有的 RAG 桥接层
- 复用现有的错误处理模式

**回滚计划**:
- 移除新端点和菜单项

## Dependencies

- Story 12.A.1 (Canvas 名称标准化)
- Story 12.A.2 (Agent-RAG 桥接层) - 新 Agent 需使用
- 现有 Agent 实现模式

## Estimated Effort
3 小时

## Definition of Done

- [ ] verification-question Agent 后端实现完成
- [ ] question-decomposition Agent 后端实现完成
- [ ] 两个新端点遵循 RAG 桥接模式
- [ ] ApiClient 支持新端点调用
- [ ] 右键菜单显示新选项
- [ ] 新 Agent 功能在 Obsidian 中可用
- [ ] 响应格式与前端兼容
- [ ] 单元测试通过
- [ ] 集成测试通过

---

## SDD 规范参考

| 规范文档 | 相关章节 | 用途 |
|----------|----------|------|
| docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md | Layer-2-服务层 | AgentService 方法模式 |
| specs/api/agent-api.openapi.yml | Agent endpoints | API 契约定义 |
| specs/data/agent-response.schema.json | agent_name enum | 响应格式验证 |
| backend/app/api/v1/endpoints/agents.py | _call_explanation | 端点实现模式参考 |

## ADR 决策关联

无相关 ADR

---

## Testing

### 单元测试 (Unit Tests)

| 测试用例 | 描述 | AC |
|----------|------|-----|
| `test_generate_verification_questions_success` | 正常生成5个层次的检验问题 | AC1 |
| `test_generate_verification_questions_empty_content` | 空内容返回友好错误 | AC1 |
| `test_decompose_question_success` | 正常拆解为3-5个子问题 | AC2 |
| `test_decompose_question_with_rag_context` | RAG 上下文正确注入 | AC3 |
| `test_endpoints_record_learning_episode` | 端点调用后记录学习事件 | AC3 |

### 集成测试 (Integration Tests)

| 测试用例 | 描述 | AC |
|----------|------|-----|
| `test_e2e_verification_question_flow` | 菜单项 → API → Canvas 节点创建 | AC4, AC5, AC6 |
| `test_e2e_question_decomposition_flow` | 菜单项 → API → 子节点创建 | AC4, AC5, AC6 |
| `test_api_error_handling` | API 超时、无效 node_id 错误处理 | AC6 |

### 测试命令

```bash
# 后端单元测试
cd backend && python -m pytest tests/test_agent_service.py -k "verification_question or decompose_question" -v

# 后端集成测试
cd backend && python -m pytest tests/integration/test_agents_endpoints.py -k "verification or decompose_question" -v

# 前端测试 (如有)
cd canvas-progress-tracker/obsidian-plugin && npm test
```

---

## Security Considerations

1. **输入验证**
   - `node_id` 格式验证 (防止注入)
   - `canvas_name` 路径验证 (防止路径遍历)
   - `content` 最大长度限制: 10000 字符

2. **速率限制**
   - 新端点应受全局速率限制保护
   - 建议: 每用户每分钟 30 次 Agent 调用

3. **内容过滤**
   - AI 提示词已包含安全约束
   - 输出不应包含敏感信息

---

## Change Log

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| 2025-12-15 | 0.1 | 初始草稿 | - |
| 2025-12-15 | 0.2 | PO 验证修复: 更新 Problem Statement, 添加 Testing/Security sections | Sarah (PO Agent) |

---

## Dev Agent Record

> 此 section 由 Dev Agent 在实现过程中填写

| 字段 | 值 |
|------|-----|
| Dev Agent 启动时间 | - |
| 完成时间 | - |
| 实现分支 | - |
| 遇到的问题 | - |
| 偏离原计划 | - |

---

## QA Results

### Review Date: 2025-12-15

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall**: Implementation follows existing patterns well, but contains **critical runtime bug** that will crash endpoints.

The implementation correctly:
- Follows existing endpoint patterns in agents.py (lines 822-995)
- Adds proper Pydantic models in schemas.py (lines 256-324)
- Implements service methods with Canvas node creation
- Integrates frontend ApiClient and ContextMenuManager

**Critical Issue Found**: Service methods missing `rag_context` parameter that endpoints pass.

### Requirements Traceability (Given-When-Then)

| AC | Test Coverage | Status |
|----|---------------|--------|
| AC1: verification-question endpoint | Endpoint implemented, **missing rag_context param** | FAIL |
| AC2: question-decomposition endpoint | Endpoint implemented, **missing rag_context param** | FAIL |
| AC3a: enrich_with_adjacent_nodes() | Called in endpoints | PASS |
| AC3b: search_memories() | Via _call_gemini_api | PASS |
| AC3c: record_learning_episode() | Called in service methods | PASS |
| AC4: Right-click menu items | Implemented in ContextMenuManager | PASS |
| AC5: ApiClient support | generateVerificationQuestions/decomposeQuestion added | PASS |
| AC6: Response format compatibility | Models match ExplainResponse/DecomposeResponse patterns | PASS |

### Refactoring Performed

None - critical bug found, returning for fix before proceeding.

### Compliance Check

- Coding Standards: ✓ Source comments present, follows patterns
- Project Structure: ✓ Files in correct locations
- Testing Strategy: ✗ No unit tests for new methods
- All ACs Met: ✗ AC3 broken due to rag_context parameter mismatch

### Improvements Checklist

**Must Fix (Blocking):**
- [ ] Add `rag_context: Optional[str] = None` to `generate_verification_questions()` (agent_service.py:2147)
- [ ] Add `rag_context: Optional[str] = None` to `decompose_question()` (agent_service.py:2297)
- [ ] Pass rag_context to context in `_call_gemini_api()` calls (lines 2213, 2355)

**Should Fix:**
- [ ] Add unit tests for new service methods
- [ ] Add integration tests for e2e endpoint flow

### Security Review

✓ No security concerns found:
- Input validation via Pydantic models
- No path traversal risks (canvas_name validated by ContextEnrichmentService)
- RAG timeout prevents DoS (2s limit)

### Performance Considerations

✓ Performance acceptable:
- RAG context retrieval has 2s timeout with graceful degradation
- Async pattern correctly implemented

### Files Modified During Review

None - returning for critical bug fix.

### Gate Status

**Gate: FAIL** → docs/qa/gates/12.A.6-complete-agents.yml

| Issue ID | Severity | Description |
|----------|----------|-------------|
| BUG-001 | HIGH | generate_verification_questions missing rag_context param |
| BUG-002 | HIGH | decompose_question missing rag_context param |
| AC-003 | MEDIUM | AC3 partial compliance |
| TEST-001 | MEDIUM | No unit tests for new methods |

### Recommended Status

**✗ Changes Required** - Fix rag_context parameter mismatch in service methods before proceeding.

---

### Historical Results

| 测试类型 | 状态 | 通过/失败 | 备注 |
|----------|------|-----------|------|
| 单元测试 | Blocked | 0/0 | No tests exist for new methods |
| 集成测试 | Blocked | 0/0 | Runtime bug prevents testing |
| E2E 测试 | Blocked | 0/0 | Runtime bug prevents testing |
| 手动测试 | Blocked | 0/0 | Runtime bug prevents testing |

---

## Conflict Resolutions

> PO 验证期间解决的 SoT 冲突记录

| # | 冲突 | 决定 | 理由 | 时间 |
|---|------|------|------|------|
| 1 | Problem Statement "缺失5个Agent" vs 实际代码库已有提示词 | Accept SoT (Code) | 更新 Story 描述为"后端端点未实现" | 2025-12-15 |
| 2 | 端点路径 `/verify/questions` vs 现有模式 | 使用 `/verification/question` | 与 health.py 引用和现有单数命名模式一致 | 2025-12-15 |
| 3 | 缺失模板 sections | 补充所有 sections | 符合 story-tmpl.yaml 要求 | 2025-12-15 |
