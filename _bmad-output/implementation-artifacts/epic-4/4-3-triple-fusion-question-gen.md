---
story_id: "4.3"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 12
depends_on: ["4.2"]
blocks: ["4.4", "4.5", "4.11"]
trace:
  - "FR-EXAM-03"
  - "FR-EXAM-13"
---

# Story 4.3: 三路融合出题 + 出题策略分化

Status: ready-for-dev

## Story
As a 系统,
I want 融合三路数据生成个人化题目,
So that 考察精准针对学习者的薄弱点和历史误解。

## Acceptance Criteria

1. **Given** Story 4.2 选出薄弱节点列表 **When** 系统为每个节点调用 `generate_question` MCP 工具 **Then** 后端在 context_enrichment_service 中融合三路数据：
   - 路线 1: Graphiti 个人记忆（学习者的 Tips/历史误解/自评校准）
   - 路线 2: Graphify 知识图谱关系（71x token 压缩检索，节点间的语义关系）
   - 路线 3: frontmatter 掌握度数据（BKT p_mastery + FSRS stability/retrievability）
   **And** 三路数据在 LLM prompt 中合并但不暴露给 skill 或用户

2. **Given** 源白板为知识点类型（canvas_type: concept）**When** 系统生成题目 **Then** 出题策略侧重定义辨析和概念理解 **And** Bloom 层级偏向 Remember(1)/Understand(2)/Analyze(4) **And** 题目形式倾向"用自己的话解释"/"对比 X 与 Y 的区别"

3. **Given** 源白板为题目类型（canvas_type: problem）**When** 系统生成题目 **Then** 出题策略侧重易错点意识和破题方法 **And** Bloom 层级偏向 Apply(3)/Analyze(4)/Evaluate(5) **And** 题目形式倾向"这段代码有什么错误"/"如何用 X 方法解决 Y 问题"

4. **Given** generate_question 被调用 **When** 后端生成题目 **Then** 返回的 `question_text` 基于学习者个人历史误解定制（非通用题库题）**And** 返回的 `pipeline_token` 可用于后续 score_answer 调用 **And** `reference_answer` 强制为 None（Story 4.1 隔离保证 3）

5. **Given** 出题过程 **When** 计时 LLM 响应 **Then** P95 延迟 < 5 秒（NFR-PERF）**And** 超时则返回降级的模板化题目并在 structlog 中记录

6. **Given** Graphiti 个人记忆查询失败 **When** 降级处理 **Then** 仅用 Graphify 知识图谱 + frontmatter 掌握度出题 **And** 在返回值中标记 `context_degraded: "graphiti_unavailable"` **And** 题目质量降低但流程不中断

7. **Given** 出题循环 **When** skill 为每个 selected_node 生成题目 **Then** 每个题目写入 exam_boards/*.md frontmatter 的 `questions[]` 数组 **And** 记录 question_id / concept / bloom_level / question_text / asked_at

## Tasks / Subtasks

- [ ] Task 1: 实现三路数据融合的 context 组装 (AC: #1)
  - [ ] Graphiti 路线：调用 search_memories 获取学习者的 Tips/错误/校准数据
  - [ ] Graphify 路线：查询节点的 1-2 hop 邻居关系和语义标签
  - [ ] Frontmatter 路线：读取 p_mastery / fsrs_stability / interaction_count
  - [ ] 三路数据合并为统一的 LLM context 结构
  - [ ] 单元测试：三路数据缺一时的降级行为

- [ ] Task 2: 实现出题策略分化 (AC: #2, #3)
  - [ ] 根据 canvas_type 选择策略模板（concept vs problem）
  - [ ] concept 策略：定义辨析 prompt template
  - [ ] problem 策略：易错点/破题 prompt template
  - [ ] 策略模板存放在 `backend/app/prompts/exam/` 目录
  - [ ] 单元测试：不同 canvas_type 下 Bloom 层级和题目形式的正确性

- [ ] Task 3: 扩展 generate_question MCP 工具 (AC: #4)
  - [ ] 添加 exam_mode / source_canvas_id 参数支持（exam_tools.py 已有字段）
  - [ ] 实现 exam 模式下的完整 ACP + 5 层 prompt pipeline
  - [ ] 确保 reference_answer 始终为 None
  - [ ] pipeline_token 正确生成（generate_question → score_answer 链）

- [ ] Task 4: 实现性能保障 (AC: #5)
  - [ ] LLM 调用添加 5 秒超时
  - [ ] 超时降级：返回基于 Bloom 层级的模板化题目
  - [ ] structlog 记录超时事件（含 node_id / 实际延迟）
  - [ ] P95 延迟监控指标

- [ ] Task 5: 实现 Graphiti 降级策略 (AC: #6)
  - [ ] Graphiti 查询失败时仅用 Graphify + frontmatter
  - [ ] context_degraded 标记传递到返回值
  - [ ] 单元测试：Graphiti 不可用时的降级路径

- [ ] Task 6: 实现出题结果写入 frontmatter (AC: #7)
  - [ ] 每个题目追加到 questions[] 数组
  - [ ] 记录完整元数据（question_id / concept / bloom_level / question_text / asked_at）
  - [ ] 同时 Edit exam_boards/*.md body 追加 `[!exam_question]+` callout

## Dev Notes

### Architecture
- generate_question MCP 工具已存在于 `backend/app/mcp/tools/exam_tools.py`
- 当前支持 exam_id / exam_mode / source_canvas_id 参数（Story 6.3 扩展）
- context_enrichment_service.py 负责内部读取 wiki/concepts 内容组装 LLM prompt
- 5 层数据流保证：后端内部读 Tips/errors 但只在组装 prompt 时用，不返回给 skill
- pipeline_token 链：generate_question → token_A → score_answer → token_B → update_fsrs/update_bkt

### File Paths
- MCP 工具：`backend/app/mcp/tools/exam_tools.py` (GenerateQuestionInput/Output)
- Context 组装：`backend/app/services/context_enrichment_service.py`
- 出题 prompt 模板：`backend/app/prompts/exam/` 目录
- Pipeline token：`backend/app/mcp/pipeline_token.py`

### Testing
- 单元测试：三路融合、策略分化、降级处理
- 性能测试：P95 < 5s 验证
- 集成测试：完整的选题 → 出题 → 写入 frontmatter 链路

### Project Structure Notes
- Graphify 71x token 压缩检索是知识图谱的核心能力（FR-KG-07）
- 出题策略按 Constructive Alignment (Biggs 1996) 与白板类型对齐

### References
- **From PRD**: §2.3 Step 7 — 出题循环 (line 1107-1155)
- **From PRD**: §2.4 保证 3 — MCP 工具返回值过滤 (line 1638-1693)
- `backend/app/mcp/tools/exam_tools.py`: generate_question 实现
- `backend/app/mcp/pipeline_token.py`: PIPELINE_STEPS 定义
- `backend/app/services/context_enrichment_service.py`: 三路数据融合

## UAT Script

> 1. 打开一个知识点类型的白板（含 3+ 个薄弱节点）
> 2. 触发 `/start_exam_board`
> 3. 等待出题完成（应在数秒内）
> 4. 查看 exam_boards/*.md 中的题目
> 5. 确认题目是个人化的（提及你之前的误解或薄弱点）
> 6. 确认知识点白板的题目侧重定义辨析
> 7. 对题目类型白板重复步骤 2-5
> 8. 确认题目白板的题目侧重易错点和破题方法

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 三路融合 | unit | `pytest tests/unit/test_triple_fusion.py -x` | 0 failures |
| 策略分化 | unit | `pytest tests/unit/test_question_strategy.py -x` | 0 failures |
| LLM 超时降级 | unit | `pytest tests/unit/test_question_gen_timeout.py -x` | 0 failures |
| Graphiti 降级 | unit | `pytest tests/unit/test_graphiti_fallback.py -x` | 0 failures |
| P95 < 5s | perf | `pytest tests/perf/test_question_gen_latency.py -x` | P95 < 5000ms |
| 出题集成 | integration | `pytest tests/integration/test_exam_question_gen.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
