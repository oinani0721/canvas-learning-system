# Story 6.4: AutoSCORE 隐形评分

Status: ready-for-dev

## Story

As a 系统,
I want 在 Agent 切换考察节点时后台自动评分，评分对用户隐形，通过节点颜色变化传达，
so that 考察流程不被评分打断。

## Acceptance Criteria

1. **AC-1: Topic-level 评分触发时机（FR-EXAM-16）**
   - **Given** Agent 正在考察当前节点
   - **When** Agent 完成当前节点考察并切换到下一个节点
   - **Then** 后台自动对已讨论节点执行 AutoSCORE 评分
   - **And** 评分触发时机为 Topic-level（知识节点切换时），不是每轮对话后
   - **And** 评分对用户隐形——不显示分数/评级弹窗/进度条
   - **And** 评分结果通过节点颜色变化隐形传达（Stealth Assessment）

2. **AC-2: AutoSCORE 两阶段执行（FR-EXAM-04）**
   - **Given** 评分触发
   - **When** AutoSCORE 执行
   - **Then** 严格分两阶段执行：
     - **Stage 1 证据提取**：从对话记录中提取学生回答的关键证据点（事实陈述、推理链、举例等）
     - **Stage 2 逐维 Rubric 打分**：基于提取的证据，按 4 维 4 分制 Rubric 打分
   - **And** 4 维 Rubric（SOLO 锚定）：
     - 概念准确性（1-4 分）：定义/术语/核心属性的正确性
     - 推理质量（1-4 分）：逻辑链完整性、因果关系正确性
     - 知识覆盖（1-4 分）：回答覆盖的知识点广度
     - 知识整合（1-4 分）：跨概念联系和迁移能力
   - **And** 两阶段分开调用 LLM（不在同一 prompt 中完成），避免证据提取偏差影响打分

3. **AC-3: 3 次采样多数投票 + 低信心标记（FR-EXAM-04）**
   - **Given** AutoSCORE Stage 2 打分
   - **When** 执行 3 次独立采样
   - **Then** 每维取 3 次评分的多数投票结果（众数）
   - **And** 如果任一维度 3 次评分中最大值与最小值之差 > 1 分，标记该维度为"AI 低信心"
   - **And** 综合 grade 映射：4 维平均 → grade 1-4（Again/Hard/Good/Easy）
   - **And** 整体低信心（2+ 维度低信心）时，邀请用户复核（FR-EXAM-15 相关）

4. **AC-4: BKT/FSRS 更新与节点颜色变化（FR-EXAM-04, FR-MAST-01/02）**
   - **Given** AutoSCORE 产出 grade 1-4
   - **When** 评分结果提交到 mastery_engine
   - **Then** EventBus 发出 SCORE_SUBMITTED 事件（Tier1, await）
   - **And** mastery_engine 执行 BKT 贝叶斯更新 + FSRS 更新（复用 Story 5.1）
   - **And** EventBus 发出 BKT_UPDATED 事件（Tier2, fire+retry）
   - **And** Graphiti 写入评分记录 + Neo4j 更新 pMastery
   - **And** WebSocket 推送 mastery_update → mastery-state → 节点颜色变化
   - **And** 精通度仅通过考察评分更新，不接受自评直接修改

5. **AC-5: Agent 顺带询问评分校准（FR-EXAM-15）**
   - **Given** Agent 切换到下一个考察节点
   - **When** 后台评分完成
   - **Then** Agent 在话题切换时顺带询问"你觉得评分准确吗？"（可选不强制）
   - **And** 用户可回应：偏高 / 偏低 / 准确 / 忽略（不回应视为"准确"）
   - **And** 用户反馈标记为 few-shot 校准样本，存储到 Graphiti
   - **And** 不弹出专门的评分 UI，通过对话消息自然呈现

6. **AC-6: MCP 工具 score_answer 接口**
   - **Given** Agent 需要评分
   - **When** 调用 MCP 工具 `score_answer`
   - **Then** 工具参数包含：exam_id, node_id, conversation_segment, token_A（来自 generate_question）
   - **And** 返回结果包含：scores（4 维）, grade（1-4）, confidence（高/低）, evidence_points, token_B
   - **And** 密码学令牌验证：token_A 必须匹配当前 exam_session + node_id
   - **And** token_B 用于后续 update_fsrs 调用（令牌链延续）

7. **AC-7: 后端 autoscore 服务**
   - **Given** 后端接收到评分请求
   - **When** autoscore.py 执行
   - **Then** Stage 1：证据提取 Prompt 独立调用 LLM → 返回证据列表
   - **And** Stage 2：Rubric 打分 Prompt 独立调用 LLM（3 次采样）→ 4 维分数
   - **And** 多数投票 + 低信心检测
   - **And** grade 映射 + EventBus 发出 SCORE_SUBMITTED
   - **And** 所有 LLM 调用记录结构化日志（FR-QA-03）
   - **And** 使用 LiteLLM 统一调用层（评分模型配置）

## Tasks / Subtasks

- [ ] **Task 1: 后端 autoscore 服务** (AC: #2, #3, #7)
  - [ ] 1.1 创建 `backend/app/services/autoscore.py`：AutoScorer 类
  - [ ] 1.2 实现 Stage 1 证据提取：独立 LLM 调用，提取学生回答证据
  - [ ] 1.3 实现 Stage 2 Rubric 打分：4 维 4 分制，独立 LLM 调用
  - [ ] 1.4 实现 3 次采样多数投票逻辑
  - [ ] 1.5 实现低信心检测：分差 > 1 标记低信心维度
  - [ ] 1.6 实现 grade 映射：4 维平均 → grade 1-4
  - [ ] 1.7 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 2: AutoSCORE Prompt 模板** (AC: #2)
  - [ ] 2.1 创建 `backend/app/prompts/scoring/stage1_evidence.md`：证据提取 Prompt
  - [ ] 2.2 创建 `backend/app/prompts/scoring/stage2_rubric.md`：4 维 Rubric 打分 Prompt
  - [ ] 2.3 Rubric 使用 SOLO 锚定描述（每维 4 个等级的具体描述）

- [ ] **Task 3: EventBus 集成——评分完成流** (AC: #4)
  - [ ] 3.1 在 autoscore 完成后发出 SCORE_SUBMITTED 事件
  - [ ] 3.2 mastery_engine 监听 SCORE_SUBMITTED → BKT+FSRS 更新
  - [ ] 3.3 发出 BKT_UPDATED → Graphiti 写入 + WebSocket 推送
  - [ ] 3.4 前端 mastery-state 接收推送 → 节点颜色变化

- [ ] **Task 4: MCP 工具 score_answer** (AC: #6)
  - [ ] 4.1 在 MCP Server 中注册 `score_answer` 工具
  - [ ] 4.2 实现密码学令牌验证（token_A 校验）
  - [ ] 4.3 实现 token_B 生成（用于后续 update_fsrs）
  - [ ] 4.4 Pydantic Schema 定义请求/响应

- [ ] **Task 5: Agent 评分校准交互** (AC: #5)
  - [ ] 5.1 在评分完成后通过 ChatPanel 展示校准询问消息
  - [ ] 5.2 实现用户反馈收集（偏高/偏低/准确/忽略）
  - [ ] 5.3 反馈数据写入 Graphiti 作为 few-shot 校准样本

- [ ] **Task 6: Topic-level 触发逻辑** (AC: #1)
  - [ ] 6.1 在 exam_service 中实现节点切换检测逻辑
  - [ ] 6.2 Agent 切换话题时自动触发 score_answer MCP 调用
  - [ ] 6.3 评分过程对用户隐形（不显示任何评分 UI）

- [ ] **Task 7: 端到端测试** (AC: #1-#7)
  - [ ] 7.1 测试：Agent 考完节点 A 切换到 B → A 被评分 → 颜色变化
  - [ ] 7.2 测试：3 次采样分差 > 1 → 低信心标记
  - [ ] 7.3 测试：grade 4 → BKT p_mastery 上升 → 节点颜色变绿
  - [ ] 7.4 测试：token_A 不匹配 → 后端拒绝

## Dev Notes

### 架构定位

本 Story 是检验白板的评分核心，连接 AI 出题（Story 6.3）和精通度更新（Story 5.1）。AutoSCORE 两阶段设计是评分质量的关键保障。

### 依赖关系

- **依赖 Story 5.1**：BKT+FSRS 精通度更新（mastery_engine.record_grade）
- **依赖 Story 5.2**：节点颜色精通度可视化（颜色变化展示）
- **依赖 Story 5.7**：EventBus 三系统联通（SCORE_SUBMITTED / BKT_UPDATED 事件）
- **依赖 Story 6.3**：generate_question 的 token_A（密码学令牌链）
- **被 Story 6.5 依赖**：递归考察中的新节点也需要评分
- **被 Story 6.8 依赖**：评分历史永久保存

### AutoSCORE 两阶段设计理据

分离证据提取和打分有两个核心好处：
1. **减少评分偏差**：如果在同一 Prompt 中同时提取证据和打分，LLM 容易产生"先入为主"偏差
2. **可审计性**：证据提取结果可被人工抽验（FR-QA-07），确保评分有据可查

### 自一致性 3 次采样

参考 ICLR 2025 Oral "Trust or Escalate"：
- 3 次独立采样（temperature > 0）取多数投票
- 分差 > 1 标记低信心 → 邀请用户复核
- 整体低信心（2+ 维度）→ 降级为用户自评辅助

### Stealth Assessment 原则

AutoTutor 期望覆盖机制：
- 评分不打断学习流程
- 通过环境变化（节点颜色）间接传达评估结果
- 用户感知为"学习"而非"考试"

### Project Structure Notes

- autoscore 在 `backend/app/services/autoscore.py`（新建）
- 评分 Prompt 在 `backend/app/prompts/scoring/` 目录（新建）
- EventBus 事件在 `backend/app/models/canvas_events.py` 中追加 SCORE_SUBMITTED

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.4] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-04/15/16
- [Source: _bmad-output/planning-artifacts/prd.md#评分公正性] — 4 维 Rubric + 自一致性 + AutoSCORE 两阶段
- [Source: _bmad-output/planning-artifacts/architecture.md#评分完成流] — SCORE_SUBMITTED → mastery_engine → BKT_UPDATED
- [Source: _bmad-output/planning-artifacts/architecture.md#算法管道完整性] — 信号从采集→评估(AutoSCORE)→更新(BKT/FSRS)→展示
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — MCP 令牌链 + EventBus 事件定义
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#反馈模式] — 评分更新通过节点颜色变化

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/autoscore.py` — 新建
- `backend/app/prompts/scoring/stage1_evidence.md` — 新建
- `backend/app/prompts/scoring/stage2_rubric.md` — 新建
- `backend/app/mcp/server.py` — 修改（注册 score_answer 工具）
- `backend/app/models/canvas_events.py` — 修改（追加 SCORE_SUBMITTED 事件）
- `backend/app/services/exam_service.py` — 修改（添加 Topic-level 触发逻辑）
