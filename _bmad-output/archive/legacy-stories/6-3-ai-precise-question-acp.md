# Story 6.3: AI 精准出题（ACP 数据包）

Status: ready-for-dev

## Story

As a AI Agent,
I want 基于 FSRS+BKT 选择用户最薄弱节点，利用 Tips/Edge 理由/错误历史精准出题，
so that 考察精准命中知识盲区。

## Acceptance Criteria

1. **AC-1: FSRS+BKT+KG 三角协作选题（FR-EXAM-02）**
   - **Given** 检验白板考察开始，原白板有多个知识节点
   - **When** Agent 选择考察目标节点
   - **Then** 通过 MCP 工具 `generate_question` 调用后端选题算法
   - **And** 选题逻辑三角协作：
     - FSRS 提供记忆衰减信息（retrievability 低 = 该复习了）
     - BKT 提供掌握概率（p_mastery 低 = 理解薄弱）
     - KG 提供关联性排序（图遍历找到关联度高但掌握差的节点）
   - **And** 综合排序公式：`priority = w1 * (1 - p_mastery) + w2 * (1 - R) + w3 * kg_relevance`
   - **And** 已考察过的节点在本次 session 内降低优先级（避免重复考察）

2. **AC-2: ACP 考察数据包注入 Prompt 第 3 层（FR-EXAM-03）**
   - **Given** 选定考察目标节点
   - **When** 组装出题 Prompt
   - **Then** ACP（Assessment Context Package）数据包通过 `--append-system-prompt` 注入 Prompt 第 3 层
   - **And** ACP 包含以下学习者数据：
     - 该节点的 Tips（用户标注的关键知识点）
     - 该节点的错误历史（4 类：破题错误/推理谬误/知识点缺失/似懂非懂）
     - 该节点的 Edge 理由（与其他概念的关系解释）
     - 该节点的精通度数据（effective_proficiency + mastery_level）
     - 该节点的对话历史摘要（Tier 2 摘要级）
   - **And** ACP 数据从 Graphiti + mastery_engine + SQLite 三源聚合
   - **And** ACP token budget 控制在 3K token 以内（句子级提取，公式/代码整块保护）

3. **AC-3: Prompt 5 层结构完整（Bloom's Taxonomy PS4 策略）**
   - **Given** 出题 Prompt 组装
   - **When** 发送给 LLM
   - **Then** Prompt 严格遵循 5 层结构：
     - **第 1 层（静态）**：角色定义——"你是考官，通过提问检验学生理解"
     - **第 2 层（用户选）**：考察模式——来自 Story 6.2 的 examMode
     - **第 3 层（动态）**：ACP 学生数据包——Tips/错误/Edge 理由/精通度/对话历史
     - **第 4 层（静态）**：出题规则——一次一题、从弱点出题、不暗示答案、难度适配
     - **第 5 层（静态）**：评分预设——告知 AI 将按 4 维 Rubric 评分，出的题需有区分度
   - **And** 第 1/4/5 层存储为 Prompt 模板文件（可版本管理，FR-QA-02）
   - **And** 学术来源：arXiv:2408.04394 验证 PS4（Prompt Strategy 4）最佳

4. **AC-4: 按白板类型定制出题策略（FR-EXAM-13）**
   - **Given** 考察模式为"点对点突破"
   - **When** Agent 对不同内容类型的节点出题
   - **Then** 知识点节点侧重：定义准确性 + 概念解释能力 + 辨析混淆概念
   - **And** 题目节点侧重：易错点意识 + 破题方法 + 混淆排除
   - **And** 出题策略通过 Prompt 第 4 层规则中的条件分支实现
   - **And** 综合题模式：跨概念整合题，考察知识间的联系和应用

5. **AC-5: MCP 工具 generate_question 接口**
   - **Given** Agent 需要出题
   - **When** 调用 MCP 工具 `generate_question`
   - **Then** 工具参数包含：exam_id, exam_mode, target_node_id（可选，为空则自动选题）
   - **And** 返回结果包含：question_text, target_node_id, difficulty_level, token_A（令牌链）
   - **And** 后端 `question_generator.py` 执行选题 + ACP 组装 + LLM 出题
   - **And** token_A 用于后续 score_answer 调用（密码学令牌管道，FR-MCP-02）
   - **And** 出题延迟目标 < 5s（含 LLM 调用）

6. **AC-6: 后端 question_generator 服务**
   - **Given** 后端接收到出题请求
   - **When** question_generator.py 执行
   - **Then** 调用 mastery_engine 获取所有节点精通度 → 三角协作排序 → 选定目标节点
   - **And** 调用 graphiti_memory 获取目标节点的 Tips/错误/Edge 理由
   - **And** 调用 conversation_archive 获取对话历史摘要
   - **And** 组装 ACP 数据包 + 5 层 Prompt → 调用 LLM（通过 LiteLLM）
   - **And** 使用 LiteLLM 统一调用层，模型从配置读取（评分模型配置）
   - **And** 所有 LLM 调用记录结构化日志（FR-QA-03）

## Tasks / Subtasks

- [ ] **Task 1: 后端选题算法** (AC: #1)
  - [ ] 1.1 在 `backend/app/services/question_generator.py` 中创建 QuestionGenerator 类
  - [ ] 1.2 实现 select_target_node() 方法：FSRS+BKT+KG 三角协作选题排序
  - [ ] 1.3 实现 priority 排序公式：`w1*(1-p_mastery) + w2*(1-R) + w3*kg_relevance`
  - [ ] 1.4 实现已考察节点本 session 内降优先级逻辑
  - [ ] 1.5 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 2: ACP 数据包组装** (AC: #2)
  - [ ] 2.1 在 question_generator 中实现 assemble_acp() 方法
  - [ ] 2.2 从 Graphiti 获取 Tips/错误/Edge 理由
  - [ ] 2.3 从 mastery_engine 获取精通度数据
  - [ ] 2.4 从 conversation_archive 获取对话历史摘要
  - [ ] 2.5 实现 ACP token budget 控制（3K token 上限，句子级压缩）

- [ ] **Task 3: Prompt 5 层模板** (AC: #3)
  - [ ] 3.1 创建 `backend/app/prompts/exam/layer1_role.md`：考官角色定义
  - [ ] 3.2 创建 `backend/app/prompts/exam/layer2_mode.md`：三种模式模板（含变量插槽）
  - [ ] 3.3 实现 ACP 第 3 层动态注入逻辑
  - [ ] 3.4 创建 `backend/app/prompts/exam/layer4_rules.md`：出题规则（含内容类型条件分支）
  - [ ] 3.5 创建 `backend/app/prompts/exam/layer5_scoring_preset.md`：评分预设

- [ ] **Task 4: 内容类型定制出题** (AC: #4)
  - [ ] 4.1 在 Prompt 第 4 层中实现知识点/题目节点的差异化出题规则
  - [ ] 4.2 知识点节点：定义+解释+辨析模板
  - [ ] 4.3 题目节点：易错点+破题方法+混淆排除模板
  - [ ] 4.4 综合题模式：跨概念整合题模板

- [ ] **Task 5: MCP 工具暴露** (AC: #5)
  - [ ] 5.1 在 MCP Server 中注册 `generate_question` 工具
  - [ ] 5.2 实现密码学令牌生成（token_A 用于后续 score_answer）
  - [ ] 5.3 工具参数和返回值的 Pydantic Schema 定义

- [ ] **Task 6: 端到端验证** (AC: #1-#6)
  - [ ] 6.1 测试：有 5 个节点、精通度不同 → 选出最薄弱节点
  - [ ] 6.2 测试：节点有 Tips/错误 → ACP 包含这些数据
  - [ ] 6.3 测试：不同 examMode → Prompt 第 2 层切换正确
  - [ ] 6.4 测试：知识点 vs 题目节点 → 出题风格不同
  - [ ] 6.5 运行 `ruff check` 确认 lint 通过

## Dev Notes

### 架构定位

本 Story 是检验白板的核心智能层——选题和出题。它是连接精通度系统（Epic 5）和检验白板 UI（Epic 6 其他 Story）的桥梁。

### 依赖关系

- **依赖 Story 5.1**：BKT+FSRS 精通度数据（mastery_engine API）
- **依赖 Story 6.1**：exam_service 基础框架（exam_session 数据）
- **依赖 Story 6.2**：examMode 参数（Prompt 第 2 层）
- **依赖 Epic 3**：MCP 工具暴露框架 + Graphiti 记忆检索 + conversation_archive
- **被 Story 6.4 依赖**：AutoSCORE 需要 generate_question 返回的 token_A

### Prompt 5 层结构（学术来源）

arXiv:2408.04394 验证 Bloom's Taxonomy PS4 策略在 AI 出题场景下效果最佳：
- 明确角色 + 指定认知层次 + 提供学生上下文 + 约束出题规则 + 预设评分标准

### ACP 数据包组装（LPITutor 双层架构）

ACP 参考 LPITutor 的 Learner Profile 注入架构：
- 将学习者的历史数据结构化组装为 Prompt 上下文
- 控制 token 预算，避免上下文过长稀释核心指令

### FSRS+BKT+KG 三角协作

- FSRS 维度：retrievability R 越低 → 该复习了（时间维度）
- BKT 维度：p_mastery 越低 → 理解越薄弱（掌握维度）
- KG 维度：与已掌握节点关联度高但自身未掌握 → 知识断层（结构维度）
- 三者互补，覆盖时间、掌握、结构三个维度

### Project Structure Notes

- 出题服务在 `backend/app/services/question_generator.py`（新建）
- Prompt 模板在 `backend/app/prompts/exam/` 目录（新建）
- MCP 工具在 `backend/app/mcp/server.py` 中注册

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.3] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-02/03/13
- [Source: _bmad-output/planning-artifacts/prd.md#出题Prompt5层结构] — Bloom's Taxonomy PS4
- [Source: _bmad-output/planning-artifacts/architecture.md#算法架构] — BKT+FSRS+KG 三角协作 + ACP
- [Source: _bmad-output/planning-artifacts/architecture.md#考察启动流] — question_generator 数据流
- [Source: _bmad-output/planning-artifacts/architecture.md#MCP工具名] — generate_question 工具命名
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — MCP 令牌链

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/question_generator.py` — 新建
- `backend/app/prompts/exam/layer1_role.md` — 新建
- `backend/app/prompts/exam/layer2_mode.md` — 新建
- `backend/app/prompts/exam/layer4_rules.md` — 新建
- `backend/app/prompts/exam/layer5_scoring_preset.md` — 新建
- `backend/app/mcp/server.py` — 修改（注册 generate_question 工具）
- `backend/app/api/v1/endpoints/exam.py` — 修改（添加出题端点）
