---
story_id: "2.5"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 10
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-06"
---

# Story 2.5: 错误自动提取与分类

Status: ready-for-dev

## Story

As a 学习者,
I want 系统自动从对话中提取我的错误并分类,
So that 我的错误被记录用于个人化出题和间隔复习。

## Acceptance Criteria

1. **Given** AI 对话中检测到学习者的误解或错误理解
   **When** 对话轮次结束（学习者发送消息后 AI 回复完成）
   **Then** 系统自动分析对话内容，提取学习者的错误
   **And** 每个提取的错误包含 `description`（错误描述）和 `context`（触发上下文）

2. **Given** 错误已提取
   **When** 系统调用错误分类器
   **Then** 每个错误被分类为 4 主类之一：
   - `conceptual_confusion`（概念混淆）：混淆了两个相关但不同的概念
   - `procedural_error`（推理谬误）：逻辑跳跃、因果倒置、无效归纳/演绎
   - `careless_slip`（粗心）：已掌握但笔误、计算错误、遗漏条件
   - `metacognitive_error`（元认知错误）：能背定义但不能迁移应用、过度自信
   **And** 分类附带置信度分数（0.0-1.0），置信度 < 0.6 标记为 `AMBIGUOUS`

3. **Given** 错误分类为特定类型
   **When** 系统关联补救策略（AR3）
   **Then** 不同错误类型触发差异化补救策略：
   - `conceptual_confusion` → 辨析题 + 对比练习
   - `procedural_error` → 找错练习 + 反例构造
   - `careless_slip` → 同结构新题练习（强化注意力）
   - `metacognitive_error` → 迁移应用题 + 自我解释
   **And** 补救策略作为 metadata 写入错误记录

4. **Given** 错误已分类并关联补救策略
   **When** 系统执行双写
   **Then** 错误写入 frontmatter `errors[]` 数组，每条含 `type` / `description` / `corrected_at: null` / `tags`
   **And** 错误通过 `record_error` MCP 工具写入 Graphiti
   **And** 双写使用 fire-and-forget 模式（Graphiti 写入不阻塞主流程）

5. **Given** 对话中未检测到错误
   **When** 对话轮次结束
   **Then** 不触发错误提取和分类
   **And** 不产生空错误记录

6. **Given** Graphiti 写入失败
   **When** `record_error` MCP 调用异常
   **Then** frontmatter 写入仍然成功（本地优先）
   **And** Graphiti 写入失败记录到 structlog warning
   **And** 自动重试 3 次后放弃（NFR 降级：记忆写入失败）

## Tasks / Subtasks

- [ ] Task 1: 对话错误检测与提取 (AC: #1, #5)
  - [ ] 1.1: 在 `backend/app/services/` 下创建 `error_extractor.py`
  - [ ] 1.2: 实现 `extract_errors_from_dialog(messages: List[Message], node_id: str) -> List[ExtractedError]`
  - [ ] 1.3: 使用 LLM 分析对话历史，通过 prompt 指示模型识别学习者的误解（参考 `error_classifier.py` 中的 prompt 模式）
  - [ ] 1.4: extraction prompt 包含示例：`"学习者说 X 但正确答案是 Y"` → 提取为 `{description: "混淆了 X 和 Y", context: "对话第 N 轮"}`
  - [ ] 1.5: 无错误时返回空列表，不产生 false positive

- [ ] Task 2: 4 主类分类 + 2 子类扩展 (AC: #2)
  - [ ] 2.1: 复用已有 `backend/app/services/error_classifier.py` 的分类逻辑
  - [ ] 2.2: 扩展分类 prompt 支持 4 主类（conceptual_confusion / procedural_error / careless_slip / metacognitive_error）— 注意现有 classifier 使用不同的 4 分类名（problem_framing / reasoning_fallacy / knowledge_gap / superficial），需映射到 PRD 定义的 4 主类
  - [ ] 2.3: 为每个主类添加 2 个子类标签（如 conceptual_confusion 的子类：`synonym_confusion` / `scope_confusion`）
  - [ ] 2.4: 分类结果含 `confidence` 字段，< 0.6 自动标记 `AMBIGUOUS`
  - [ ] 2.5: 分类使用 LiteLLM 调用 LLM（与现有 error_classifier.py 一致）

- [ ] Task 3: 补救策略关联 (AC: #3)
  - [ ] 3.1: 在 `backend/app/graphiti/entity_types.py` 中确认或扩展 `ERROR_TYPE_TO_REMEDY` 映射，对齐 PRD 的 4 主类
  - [ ] 3.2: 映射关系：`conceptual_confusion → [discrimination_exercise, comparison_practice]`，`procedural_error → [error_finding, counterexample_construction]`，`careless_slip → [isomorphic_practice]`，`metacognitive_error → [transfer_application, self_explanation]`
  - [ ] 3.3: 补救策略作为 `remedy_strategies: List[str]` 写入错误记录 metadata

- [ ] Task 4: 双写 — frontmatter + Graphiti (AC: #4, #6)
  - [ ] 4.1: 实现 `write_error_to_frontmatter(file_path: str, error: ClassifiedError)` — 追加到 `errors[]` 数组
  - [ ] 4.2: 实现 `write_error_to_graphiti(error: ClassifiedError, node_id: str)` — 调用 `record_error` MCP 工具
  - [ ] 4.3: Graphiti 写入使用 `asyncio.create_task`（fire-and-forget），设置 500ms 超时
  - [ ] 4.4: Graphiti 写入失败时 structlog warning + 自动重试（最多 3 次，间隔 1s）
  - [ ] 4.5: frontmatter 写入使用原子写入（临时文件 + rename）

- [ ] Task 5: Skill workflow 集成 (AC: #1)
  - [ ] 5.1: 在 `/chat_with_context` workflow 中，每轮 AI 回复后异步触发错误提取
  - [ ] 5.2: 提取和分类作为后台任务，不阻塞下一轮对话
  - [ ] 5.3: 使用 EventBus 发布 `error_detected` 事件，供其他服务订阅

- [ ] Task 6: 测试 (AC: #1~#6)
  - [ ] 6.1: 单元测试 `extract_errors_from_dialog`：含错误对话、无错误对话、边界情况
  - [ ] 6.2: 单元测试分类器：4 主类分类准确性、AMBIGUOUS 标记、子类标签
  - [ ] 6.3: 单元测试补救策略映射：每种错误类型关联正确策略
  - [ ] 6.4: 单元测试双写：frontmatter 写入成功 + Graphiti 失败降级
  - [ ] 6.5: 集成测试：完整对话 → 错误提取 → 分类 → 双写 → frontmatter 和 Graphiti 均有记录

## Dev Notes

- **已有 error_classifier.py**: `backend/app/services/error_classifier.py` 已实现 4 分类 LLM 调用，但使用了不同的分类名（problem_framing / reasoning_fallacy / knowledge_gap / superficial）。需要映射到 PRD 定义的 4 主类（conceptual_confusion / procedural_error / careless_slip / metacognitive_error），或扩展现有分类器
- **已有 entity_types.py**: `backend/app/graphiti/entity_types.py` 已定义 `ErrorType` 枚举和 `ERROR_TYPE_TO_REMEDY` 映射
- **Anchor PRD 引用**: §3.2 frontmatter errors[] schema (line 3387-3393)，§7.1 MCP 工具表 #14 record_error (line 6180)
- **record_error MCP**: 写入 frontmatter `errors[]` + Graphiti，是 PRD 定义的 14 个核心 MCP 工具之一
- **fire-and-forget 模式**: 参考 Story 36.9 的 `memory_service.py` 双写实现（AC-36.9.2: JSON 写入使用 fire-and-forget）

### Project Structure Notes

```
backend/app/services/
  error_extractor.py              # 新增：对话错误提取
  error_classifier.py             # 已有：扩展分类映射
backend/app/graphiti/
  entity_types.py                 # 已有：确认/扩展 ERROR_TYPE_TO_REMEDY
backend/tests/unit/
  test_error_extractor.py         # 新增
  test_error_classification_mapping.py  # 新增
```

### References

- Anchor PRD §3.2 errors[] schema: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3387-3393)
- Anchor PRD §7.1 record_error MCP: (line 6180)
- 已有 error_classifier.py: `backend/app/services/error_classifier.py`
- 已有 entity_types.py: `backend/app/graphiti/entity_types.py`
- Story 36.9 双写模式: `backend/app/services/memory_service.py` (AC-36.9.1~36.9.5)

## UAT Script

> 1. 打开 `wiki/concepts/admissibility.md`，启动 AI 对话
> 2. 故意说一个错误："admissibility 就是 consistent 吧？它们是一样的"
> 3. 等待 AI 纠正回答
> 4. 回答完成后，等待 3-5 秒（后台错误提取）
> 5. 打开 `admissibility.md` 的 frontmatter，验证 `errors:` 数组中新增了一条记录，type 为 `conceptual_confusion`
> 6. 检查后端日志，验证 Graphiti 写入成功（或降级 warning）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 错误提取 | unit | `pytest tests/unit/test_error_extractor.py -x` | 全部通过 |
| 4 主类分类 | unit | `pytest tests/unit/test_error_classification_mapping.py -x` | 4 类映射正确 |
| 补救策略 | unit | `pytest tests/unit/test_error_classification_mapping.py::test_remedy_mapping -x` | 策略对应 |
| 双写降级 | unit | `pytest tests/unit/test_error_extractor.py::test_graphiti_fallback -x` | frontmatter 成功 |
| 端到端分类 | integration | `pytest tests/integration/test_error_extraction_e2e.py -x` | 双写均成功 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
