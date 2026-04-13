---
story_id: "9.1"
epic_id: "9"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 8
depends_on: ["2.8", "4.3"]
blocks: []
trace:
  - "FR-MM-03"
---

# Story 9.1: 图片内容作为考察素材

Status: ready-for-dev

## Story
As a 学习者,
I want 图片内容在考察时作为出题素材,
So that 多模态学习更深入，图片中的知识也能被考察验证。

## Acceptance Criteria

1. **Given** 笔记中嵌入了图片（`![[image.png]]` 或 `![](path/to/image.png)`）且图片内容已通过 Claudian 视觉识别提取过描述文本（Story 2.8）**When** 系统为该概念生成考察题目（Story 4.3 三路融合管道）**Then** 图片描述文本作为第四路数据源参与出题 **And** 生成的题目可以引用图片中的内容（如"在你标注的流程图中，步骤 3 的作用是什么？"）

2. **Given** 图片描述文本已提取并存储在概念的 frontmatter `image_descriptions` 数组中 **When** generate_question MCP 工具组装 context **Then** image_descriptions 与三路数据（BKT 弱点 + Graphiti 错误 + LanceDB 邻居）合并注入 prompt **And** 图片描述在 prompt 中标注来源"[from image: image_name.png]"以区分文本来源

3. **Given** 图片描述文本参与出题 **When** AI 生成题目 **Then** 题目中不直接复现图片内容（防止简单抄写），而是要求学习者解释、应用或比较图片中的概念 **And** AI prompt 包含指令"题目应考察对图片内容的理解，不要要求背诵图片中的文字"

4. **Given** 笔记中的图片没有被识别过（无 image_descriptions 数据）**When** 系统组装出题 context **Then** 跳过图片数据源 **And** 出题仍基于三路融合正常工作 **And** 不因缺少图片数据导致出题失败

5. **Given** 图片描述文本 **When** 考察结束 **Then** 图片描述不自动持久化到 LanceDB 检索索引（降级策略）**And** 图片数据仅在出题时临时使用，不进入向量搜索 **And** 这是 FR-MM-03 的明确降级约束

6. **Given** 图片内容涉及代码截图或公式截图 **When** AI 基于图片描述出题 **Then** 题目格式适配内容类型（代码题要求写代码片段、公式题要求推导步骤）**And** AI prompt 根据 image_descriptions 中的 content_type 字段选择出题策略

## Tasks / Subtasks

- [ ] Task 1: 扩展三路融合管道支持图片数据 (AC: #1, #2)
  - [ ] 在 `backend/app/services/question_generation_service.py` 中扩展 context 组装
  - [ ] 新增第四路数据源：从 frontmatter image_descriptions 读取
  - [ ] 合并入 prompt context，标注 "[from image: name]" 来源
  - [ ] 图片数据为可选（三路 + 可选图片 = 3+1 路）

- [ ] Task 2: 实现图片感知出题 prompt (AC: #3, #6)
  - [ ] AI prompt 指令：基于图片内容考察理解而非背诵
  - [ ] 根据 content_type 选择出题策略：diagram → 解释关系、code → 写代码、formula → 推导
  - [ ] few-shot 示例：好的图片出题 vs 简单抄写的反例
  - [ ] 单元测试：prompt 包含图片指令 + 内容类型适配

- [ ] Task 3: 实现缺失数据降级 (AC: #4)
  - [ ] image_descriptions 为空或不存在时跳过图片路
  - [ ] 三路融合管道不受影响
  - [ ] 单元测试：无图片数据时正常出题

- [ ] Task 4: 确保降级约束——不自动持久化到索引 (AC: #5)
  - [ ] 验证图片描述不被写入 LanceDB 索引
  - [ ] 图片数据仅在出题 session 内临时使用
  - [ ] 单元测试：出题后 LanceDB 索引不包含 image_descriptions 内容

- [ ] Task 5: 实现 image_descriptions frontmatter schema (AC: #2)
  - [ ] 定义 schema：`image_descriptions: [{name, content_type, description, extracted_at}]`
  - [ ] content_type 枚举：diagram / code / formula / text / table / other
  - [ ] 验证 Story 2.8 的视觉识别输出与此 schema 兼容

## Dev Notes

### Architecture
- 图片作为考察素材是三路融合管道的可选第四路，架构上是"3+1"而非重新设计
- 降级约束（不持久化到索引）是 PRD 明确要求，原因是图片识别准确率不足以支撑搜索索引
- 图片描述数据来自 Story 2.8 的 Claudian 视觉识别，此处只消费不生产
- content_type 分类决定出题策略，是 multimodal learning 的关键适配点

### image_descriptions Schema

```yaml
image_descriptions:
  - name: "bfs-flowchart.png"
    content_type: "diagram"
    description: "A flowchart showing BFS traversal order: start node → queue → visit neighbors → repeat"
    extracted_at: "2026-04-10T14:30:00Z"
  - name: "time-complexity.png"
    content_type: "formula"
    description: "O(V + E) time complexity derivation for BFS on adjacency list"
    extracted_at: "2026-04-10T14:32:00Z"
```

### File Paths
- 出题管道：`backend/app/services/question_generation_service.py`（扩展 context）
- MCP 工具：`backend/app/mcp/tools/exam_tools.py`（generate_question 扩展）
- 概念 frontmatter：`wiki/concepts/*.md`（image_descriptions 数组）
- 图片识别（上游）：Story 2.8 Claudian 视觉 API
- LanceDB 索引：`backend/app/services/rag_service.py`（确认不写入图片数据）

### Testing
- 单元测试：图片描述正确注入 prompt context
- 单元测试：无图片数据时三路管道正常
- 单元测试：出题后 LanceDB 索引无图片数据（降级约束验证）
- 集成测试：含图片概念的完整出题流程

### References
- **From PRD**: §8.5 旅程 5 图片学习 (line 7046-7069)
- FR-MM-03: 图片内容作为考察素材（含降级约束）
- FR-MM-01: 图片识别纳入 AI 上下文（Story 2.8）
- Story 2.8: Claudian 图片识别
- Story 4.3: 三路融合出题管道

## UAT Script

> 1. 在某概念笔记中嵌入一张流程图，确保 Claudian 已识别并在 frontmatter 写入 image_descriptions
> 2. 为该概念启动考察
> 3. 看到生成的题目涉及图片内容（如"在流程图中，步骤 X 的作用是什么？"）
> 4. 确认题目要求理解/解释而非简单抄写图片文字
> 5. 考察结束后检查 LanceDB 索引，确认图片描述未被持久化
> 6. 对一个没有图片的概念启动考察，确认正常出题（三路融合不受影响）
> 7. 嵌入一张代码截图，确认出题策略适配为"写代码"类型

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 图片 context 注入 | unit | `pytest tests/unit/test_image_exam_context.py -x` | 0 failures |
| 出题 prompt 指令 | unit | `pytest tests/unit/test_image_question_prompt.py -x` | 0 failures |
| 缺失降级 | unit | `pytest tests/unit/test_image_exam_fallback.py -x` | 0 failures |
| 索引不持久化 | unit | `pytest tests/unit/test_image_no_index.py -x` | 0 failures |
| 内容类型适配 | unit | `pytest tests/unit/test_image_content_type.py -x` | 0 failures |
| 完整出题流程 | integration | `pytest tests/integration/test_image_exam_pipeline.py -x` | 0 failures |

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
