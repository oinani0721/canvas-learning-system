# Story 4.3: EI+SE 双重学习策略激活

Status: ready-for-dev

## Story

As a 用户,
I want Edge 对话同时触发精细化追问和自我解释两种学习策略,
so that 一次连线交互能最大化学习效果。

## Acceptance Criteria

1. **AC-1: Elaborative Interrogation (EI) 策略激活**
   - **Given** Edge 对话进行中，Agent 追问用户连线理由
   - **When** Agent 与用户交互
   - **Then** Agent 追问遵循 Elaborative Interrogation 策略：
     - 追问"为什么"和"怎么样"类型的深层问题（如"为什么 A 是 B 的前提？"、"这种关系在什么条件下成立？"）
     - 引导用户生成深层解释，而非仅仅回忆表面事实
     - 追问基于用户已有知识（从 Graphiti 检索用户之前的 Tips/错误/理由），不重复已确认理解的内容
   - **And** EI 追问集成在 Edge 对话 prompt 中，不作为独立的显式步骤

2. **AC-2: Self-Explanation (SE) 策略激活**
   - **Given** Edge 对话进行中，用户解释连线理由
   - **When** Agent 检测到用户的解释不够深入或有潜在误解
   - **Then** Agent 引导用户进行 Self-Explanation：
     - 要求用户用自己的话重新解释关系（如"能用你自己的话解释一下这个关系吗？"）
     - 引导用户对比新旧知识（如"这和你之前理解的 X 有什么不同？"）
     - 鼓励用户识别自己理解中的不确定之处
   - **And** SE 引导在 Agent 判定解释不充分时自然触发，不每次强制

3. **AC-3: Active Recall 排除**
   - **Given** Edge 对话场景
   - **When** 策略选择
   - **Then** Active Recall 不在 Edge 对话场景激活
   - **And** 理由：连线时两端概念对用户可见（白板上同时看到两个节点），不构成回忆检索条件（Karpicke & Blunt, 2011）
   - **And** Active Recall 保留给检验白板考察场景（Epic 6）

4. **AC-4: 策略对用户透明**
   - **Given** EI + SE 双重策略在后台运作
   - **When** 用户与 Agent 交互
   - **Then** 用户体感为"自然对话"——Agent 像聪明的学伴追问和引导，而非"做练习"
   - **And** Agent 不使用教学术语（不说"现在进行精细化追问"或"请进行自我解释"）
   - **And** 对话流程不出现明显的"策略切换"断裂感
   - **And** Agent 的追问密度适度：不过度追问导致用户疲劳，也不过快接受表面回答

5. **AC-5: EI+SE 策略 Prompt 工程**
   - **Given** Edge 对话 prompt 模板
   - **When** Agent 加载 Edge 对话 prompt
   - **Then** Prompt 中隐式包含 EI+SE 策略指令（不暴露给用户）：
     - EI 指令：追问深层因果关系、条件限制、反例
     - SE 指令：检测解释深度不足时引导用自己的话解释、对比新旧知识
     - 排除指令：明确不使用 Active Recall 策略
     - 体感指令：保持自然对话风格，避免教学术语
   - **And** Prompt 模板可独立更新，不需要修改代码

6. **AC-6: 策略效果数据记录**
   - **Given** Edge 对话完成后
   - **When** 系统记录对话数据
   - **Then** 记录策略激活标记：`strategies_applied: ['EI', 'SE']`
   - **And** 记录 Agent 追问轮数和用户解释深度评分（由 Agent 内部评估，1-5 分）
   - **And** 数据写入 Graphiti（供后续分析策略有效性）
   - **And** 记录对用户透明（不显示在对话中）

## Tasks / Subtasks

- [ ] **Task 1: EI+SE 策略 Prompt 模板** (AC: #1, #2, #5)
  - [ ] 1.1 扩展 `backend/prompts/edge-dialog.md`（Story 4.2 创建），添加 EI+SE 策略指令：
    - EI 部分：追问"为什么"和"怎么样"深层问题的指令
    - SE 部分：检测解释深度不足时引导自我解释的指令
    - 排除 Active Recall 的明确指令
    - 自然对话风格指令
  - [ ] 1.2 设计追问策略流程模板：
    - 开放式提问 → EI 深层追问 → SE 自我解释引导（按需） → 确认理解 → 提取理由
  - [ ] 1.3 添加反例：不应该做什么（不用术语、不强制每次都追问、不打断用户思路）

- [ ] **Task 2: Agent 追问深度控制逻辑** (AC: #1, #2, #4)
  - [ ] 2.1 在 Edge 对话 prompt 中定义追问深度评估标准：
    - 用户仅给出"A 和 B 有关系"→ 深度 1（需 EI 追问）
    - 用户解释了因果关系但无条件限制 → 深度 2（需 EI 追问条件/反例）
    - 用户给出完整因果+条件+自己的话 → 深度 4-5（可结束）
  - [ ] 2.2 追问密度控制：最多 3-4 轮追问，避免用户疲劳
  - [ ] 2.3 SE 触发条件：用户解释深度 <= 2 时，自然引导"用自己的话说一下"

- [ ] **Task 3: 已有知识感知追问** (AC: #1)
  - [ ] 3.1 Edge 对话上下文组装时，从 Graphiti 检索用户关于两端概念的已有 Tips/错误/之前的 Edge 理由
  - [ ] 3.2 将已有知识注入 prompt，指令 Agent 不重复追问已确认理解的内容
  - [ ] 3.3 如用户之前有相关误解记录，指令 Agent 针对性追问该误解是否已修正

- [ ] **Task 4: 策略效果数据记录** (AC: #6)
  - [ ] 4.1 在 record_edge_rationale MCP 工具中扩展参数：strategies_applied、questioning_rounds、explanation_depth_score
  - [ ] 4.2 Edge 对话结束时 Agent 内部评估解释深度（1-5 分）
  - [ ] 4.3 策略标记和深度评分写入 Graphiti（附加在 EdgeRationale 记录上）

- [ ] **Task 5: 测试** (AC: #1-#6)
  - [ ] 5.1 创建 Prompt 回归测试用例 `backend/tests/regression/test_edge_dialog_prompt.py`：
    - 给定浅层回答（"A 和 B 有关系"），验证 Agent 进行 EI 追问
    - 给定深层回答（完整因果+条件），验证 Agent 不过度追问
    - 验证 Agent 不使用教学术语
    - 验证 Active Recall 不被触发
  - [ ] 5.2 策略数据记录验证：record_edge_rationale 端点正确存储 strategies_applied 和 depth_score
  - [ ] 5.3 编辑后运行 `ruff check` 确认 lint 通过

## Dev Notes

### EI + SE 学术依据

**Elaborative Interrogation (EI)**（[Source: architecture.md#能力域3]）：
- 通过"为什么"和"怎么样"类问题促进深层加工
- 学术来源：Dunlosky et al., "Improving Students' Learning With Effective Learning Techniques", 2013 — EI 被评为 moderate utility 学习策略
- 核心机制：要求学习者生成深层解释（不只是回忆），促进新旧知识整合

**Self-Explanation (SE)**：
- 要求学习者用自己的话解释材料，识别理解中的不确定
- 学术来源：Chi et al., "Eliciting Self-Explanations Improves Understanding", 1994
- 核心机制：监控自己的理解过程，发现知识缺口

**Active Recall 排除理由**：
- 连线时两端概念对用户可见（白板上同时看到两个节点），不构成回忆检索
- 学术来源：Karpicke & Blunt, "Retrieval Practice Produces More Learning than Elaborative Studying with Concept Mapping", 2011 — Active Recall 要求从记忆中提取信息，需要信息不可见

### 策略透明性设计原则

用户体感设计（[Source: ux-design-specification.md#Effortless Interactions]）：

| 实际策略 | 用户体感 |
|---------|---------|
| EI 追问因果 | "Agent 好奇地追问了一下" |
| SE 引导解释 | "Agent 让我换个方式说" |
| 深度不足检测 | "Agent 想更多了解我的理解" |
| 策略完成 | "聊完了，理由记下来了" |

### 与 Story 4.2 的关系

本 Story 扩展 Story 4.2 的 Edge 对话 prompt，不创建新的组件或端点：
- Story 4.2 负责：EdgeDialogTrigger + Agent 追问 + 理由结构化记录 + 双写
- Story 4.3 负责：EI+SE 策略集成到 prompt + 追问深度控制 + 策略效果记录

### Prompt 模板可独立更新

EI+SE 策略指令写在 `backend/prompts/edge-dialog.md` 模板中。修改策略只需更新 Prompt 文件，不需要修改代码。这符合 Prompt 版本管理规范（FR-QA-02）。

### Project Structure Notes

- `backend/prompts/edge-dialog.md` — 修改（Story 4.2 创建，本 Story 扩展 EI+SE 策略指令）
- `backend/app/api/v1/endpoints/edges.py` — 修改（扩展 record_edge_rationale 参数）
- `backend/app/models/edge_rationale.py` — 修改（扩展 strategies_applied 等字段）
- `src/services/agent-bridge.ts` — 修改（Edge 上下文组装增加已有知识注入）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story4.3] — AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域3] — EI+SE 双重策略激活（排除 Active Recall，Karpicke & Blunt 2011）
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Effortless Interactions] — Edge 连线体感为"自然对话"
- [Source: _bmad-output/planning-artifacts/prd.md#FR-EDGE-04] — Edge 对话同时激活 EI+SE 两种学习策略
- Dunlosky et al., 2013 — EI moderate utility 评级
- Chi et al., 1994 — Self-Explanation 促进理解
- Karpicke & Blunt, 2011 — Active Recall 需要信息不可见条件

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/prompts/edge-dialog.md` — 修改（扩展 EI+SE 策略指令）
- `backend/app/api/v1/endpoints/edges.py` — 修改（扩展参数）
- `backend/app/models/edge_rationale.py` — 修改（扩展字段）
- `src/services/agent-bridge.ts` — 修改（已有知识注入）
- `backend/tests/regression/test_edge_dialog_prompt.py` — 新建
