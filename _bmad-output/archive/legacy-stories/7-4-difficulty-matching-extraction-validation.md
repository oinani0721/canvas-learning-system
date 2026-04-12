# Story 7.4: 出题难度匹配与提取质量验证

Status: ready-for-dev

## Story

As a 系统,
I want 评估出题难度与用户掌握度的匹配程度，结构化提取结果支持人工抽验，管道健康指标实时可查，
So that 考察质量持续优化，提取准确性可被验证，系统运行状况一目了然。

## Acceptance Criteria

1. **AC-1: 出题难度匹配率评估**
   - **Given** 检验白板考察过程中 Agent 出题
   - **When** 系统评估出题难度与用户掌握度的匹配程度
   - **Then** 难度匹配率 >= 70%（即 >= 70% 的题目难度落在用户当前掌握度的合理区间内）
   - **And** 匹配评估基于 BKT p_mastery + FSRS R 的 effective_proficiency 值与题目估计难度的比对
   - **And** 匹配结果记录到结构化日志（node_id / 掌握度 / 题目估计难度 / 是否匹配 / 时间戳）

2. **AC-2: 难度匹配监控与统计**
   - **Given** 系统累积了多次考察的出题记录
   - **When** 查询难度匹配统计
   - **Then** 提供滑动窗口统计（最近 50 题）的匹配率
   - **And** 匹配率 < 70% 时日志告警（NFR-OBS-03 错误自动分类聚合）
   - **And** 统计数据可通过 REST API 查询（`GET /api/v1/system/qa-metrics`）

3. **AC-3: 结构化提取结果人工抽验界面**
   - **Given** 对话归档管道提取了结构化数据（错误/Tips/关键问答）
   - **When** 用户/开发者访问抽验界面
   - **Then** 展示提取结果列表（原始对话片段 + 提取的结构化内容 + 提取分类）
   - **And** 每条提取结果支持标注"正确/错误/部分正确"
   - **And** 标注结果记录到日志用于后续提取管道优化

4. **AC-4: 提取质量统计**
   - **Given** 人工抽验产生了标注数据
   - **When** 查询提取质量统计
   - **Then** 展示提取准确率（正确 / 总抽验数）
   - **And** 按提取类型分类统计（错误提取准确率 / Tips 提取准确率 / 关键问答提取准确率）
   - **And** 准确率 < 80% 时日志告警

5. **AC-5: 管道健康指标实时可查**
   - **Given** 系统运行中
   - **When** 查询管道健康指标
   - **Then** 展示以下实时指标：
     - 搜索通道存活率（6/6 通道状态）
     - 配置参数传递状态（正确生效 / 断裂）
     - 索引一致性（无重复索引）
     - Reranker 生效状态
     - CRAG 触发率（健康区间 15-30%）
     - Faithfulness 平均分（>= 0.85）
     - 出题难度匹配率（>= 70%）
   - **And** 指标通过 `GET /api/v1/system/pipeline-health` 查询
   - **And** 任一指标异常时日志告警

6. **AC-6: 错误自动分类聚合**
   - **Given** 系统运行中产生各类错误
   - **When** 错误发生
   - **Then** 自动分类为 LLM 错误 / 网络错误 / 算法异常 / 数据异常四类
   - **And** 按类型聚合统计（最近 24h / 7d / 30d）
   - **And** 分类聚合结果可通过管道健康指标 API 查询

## Tasks / Subtasks

- [ ] Task 1: 出题难度匹配评估器实现 (AC: #1, #2)
  - [ ] 1.1 创建 `backend/app/services/difficulty_matcher.py` — 难度匹配评估服务
  - [ ] 1.2 实现难度区间计算：根据 effective_proficiency（0.0-1.0）划分合理难度区间（proficiency ± 0.2 浮动范围，边界 clamp 到 [0, 1]）
  - [ ] 1.3 实现题目难度估计器：Agent 出题后通过 LLM 对题目进行难度估计（0.0-1.0），使用 LiteLLM 统一调用层
  - [ ] 1.4 实现匹配判定逻辑：题目估计难度是否落在用户掌握度合理区间内
  - [ ] 1.5 实现滑动窗口统计：维护最近 50 题的匹配记录，计算匹配率
  - [ ] 1.6 匹配率 < 70% 时通过 logging 模块发出 WARNING 级别告警
  - [ ] 1.7 将 DifficultyMatcher 集成到 `services/question_generator.py` 出题流程中（出题后异步评估，不阻塞出题）

- [ ] Task 2: 结构化提取人工抽验后端 (AC: #3, #4)
  - [ ] 2.1 创建 `backend/app/services/extraction_validator.py` — 提取结果抽验服务
  - [ ] 2.2 定义抽验数据模型（`models/qa_models.py`）：ExtractionRecord（原始文本片段 + 提取结果 + 提取类型 + 来源 session_id + 时间戳）、ValidationAnnotation（record_id + 标注结果 + 标注者 + 时间戳）
  - [ ] 2.3 实现提取结果存储：对话归档管道（`conversation_archive.py`）提取时，同时将原始片段+提取结果写入 SQLite 抽验表
  - [ ] 2.4 实现抽验记录查询 API：分页获取待抽验记录，支持按提取类型过滤
  - [ ] 2.5 实现标注提交 API：记录人工标注结果（正确/错误/部分正确）
  - [ ] 2.6 实现提取质量统计：按类型计算准确率，准确率 < 80% 时日志告警

- [ ] Task 3: 管道健康指标聚合服务 (AC: #5, #6)
  - [ ] 3.1 扩展 `backend/app/services/health_monitor.py` — 新增管道健康指标聚合
  - [ ] 3.2 实现搜索通道存活率检测：检查 6 路搜索通道（Dense/Sparse/Graphiti/Vault/CLI/图片）是否返回真实数据
  - [ ] 3.3 实现配置参数传递状态检测：验证 adapter.py 的关键参数在管道中是否生效
  - [ ] 3.4 实现索引一致性检测：检查 LanceDB 中同一文件是否存在重复索引
  - [ ] 3.5 实现 Reranker 生效状态检测：验证 Reranker 是否返回重排序结果（非直接 pass-through）
  - [ ] 3.6 聚合 CRAG 触发率（从 agentic_rag 日志中统计）
  - [ ] 3.7 聚合 Faithfulness 平均分（从 Story 7.1 的检查日志中统计）
  - [ ] 3.8 聚合出题难度匹配率（从 Task 1 的滑动窗口统计中获取）

- [ ] Task 4: 错误自动分类聚合实现 (AC: #6)
  - [ ] 4.1 创建 `backend/app/services/error_aggregator.py` — 错误分类与聚合服务
  - [ ] 4.2 实现错误分类器：根据异常类型和上下文自动分类（LLM 错误 / 网络错误 / 算法异常 / 数据异常）
  - [ ] 4.3 实现时间窗口聚合统计（24h / 7d / 30d 滑动窗口）
  - [ ] 4.4 集成到现有 `middleware/logging_middleware.py`：捕获异常时自动分类并记录
  - [ ] 4.5 聚合结果纳入管道健康指标 API

- [ ] Task 5: REST API 端点实现 (AC: #2, #3, #4, #5)
  - [ ] 5.1 在 `backend/app/api/v1/system.py` 中新增 `GET /api/v1/system/qa-metrics` — 返回出题难度匹配率 + 提取质量统计
  - [ ] 5.2 在 `backend/app/api/v1/system.py` 中新增 `GET /api/v1/system/pipeline-health` — 返回全部管道健康指标
  - [ ] 5.3 在 `backend/app/api/v1/system.py` 中新增 `GET /api/v1/system/extraction-records` — 分页查询提取记录（支持 type 过滤）
  - [ ] 5.4 在 `backend/app/api/v1/system.py` 中新增 `POST /api/v1/system/extraction-records/{id}/annotate` — 提交人工标注
  - [ ] 5.5 在 `backend/app/api/v1/system.py` 中新增 `GET /api/v1/system/error-aggregation` — 返回错误分类聚合统计
  - [ ] 5.6 定义所有 API 的 Pydantic 请求/响应模型（`models/qa_models.py`）

- [ ] Task 6: 前端抽验界面组件 (AC: #3, #4)
  - [ ] 6.1 创建 `obsidian-canvas-learning/src/components/system/ExtractionValidator.svelte` — 提取结果人工抽验面板
  - [ ] 6.2 实现提取记录列表展示：左侧原始对话片段，右侧提取的结构化内容
  - [ ] 6.3 实现标注操作：每条记录可标注"正确/错误/部分正确"
  - [ ] 6.4 实现统计面板顶部展示：总抽验数 / 准确率 / 按类型分类准确率
  - [ ] 6.5 CSS 使用 `cl-sys-*` 前缀（F 组系统组件）

- [ ] Task 7: 管道健康指标前端展示 (AC: #5)
  - [ ] 7.1 创建 `obsidian-canvas-learning/src/components/system/PipelineHealth.svelte` — 管道健康面板
  - [ ] 7.2 展示各项指标状态灯（绿色正常 / 黄色告警 / 红色异常）
  - [ ] 7.3 集成到 Settings Tab 的系统健康面板区域（Story 1.3 的健康面板扩展）
  - [ ] 7.4 CSS 使用 `cl-sys-*` 前缀

- [ ] Task 8: 单元测试与集成测试 (AC: #1-#6)
  - [ ] 8.1 单元测试：`test_difficulty_matcher.py` — 难度区间计算、匹配判定、滑动窗口统计
  - [ ] 8.2 单元测试：`test_extraction_validator.py` — 提取记录存储、标注、统计
  - [ ] 8.3 单元测试：`test_error_aggregator.py` — 错误分类准确性、时间窗口聚合
  - [ ] 8.4 集成测试：`test_qa_pipeline_health.py` — 管道健康指标端到端聚合
  - [ ] 8.5 集成测试：出题→难度评估→匹配统计→API 查询的完整链路

## Dev Notes

### 出题难度匹配方案

**核心逻辑：**

出题难度匹配解决的问题是"AI 出的题目是否适合用户当前水平"。太难会挫败，太简单无学习效果。

**难度评估方法：**

1. **用户掌握度获取**：从 `mastery_engine.py` 获取节点的 `effective_proficiency = min(p_mastery, R)`，范围 [0.0, 1.0]
2. **合理难度区间**：以 effective_proficiency 为中心，± 0.2 浮动（clamp 到 [0, 1]），形成 [lower, upper] 区间
   - proficiency = 0.3 → 合理区间 [0.1, 0.5]
   - proficiency = 0.7 → 合理区间 [0.5, 0.9]
   - proficiency = 0.05 → 合理区间 [0.0, 0.25]（下界 clamp）
3. **题目难度估计**：出题后使用 LLM 对题目进行独立难度评估（few-shot prompt，输出 0.0-1.0）
4. **匹配判定**：估计难度落在合理区间内 → 匹配；否则 → 不匹配
5. **异步执行**：难度评估不阻塞出题流程，异步在后台完成

**匹配率统计：**

- 使用环形缓冲区（deque maxlen=50）维护最近 50 题的匹配记录
- 匹配率 = matched_count / total_count
- 告警阈值：匹配率 < 0.7 时 WARNING 日志

**与考察管道的集成位置：**

```
question_generator.py 生成题目
  → 返回题目给 Agent
  → 异步: difficulty_matcher.evaluate(node_id, question, proficiency)
  → 记录匹配结果到 SQLite qa_metrics 表
  → 更新滑动窗口统计
```

### 结构化提取人工抽验方案

**数据来源：**

对话归档管道（`conversation_archive.py`）在 Hot→Warm 归档时，使用 LLM 提取结构化数据：
- **错误提取**：4 类错误（破题错误/推理谬误/知识点缺失/似懂非懂）
- **Tips 提取**：用户标注的关键知识点
- **关键问答提取**：值得保留的精彩问答

**抽验数据模型：**

```python
class ExtractionRecord(BaseModel):
    id: str                       # UUID
    source_session_id: str        # 来源对话 session
    source_node_id: str           # 来源节点
    original_text: str            # 原始对话片段（提取依据）
    extracted_content: str        # 提取出的结构化内容
    extraction_type: str          # "error" | "tip" | "key_qa"
    extraction_subtype: str | None  # 错误子类型（破题/推理/知识点/似懂非懂）
    created_at: str               # ISO 8601
    annotation: str | None        # "correct" | "incorrect" | "partial" | None (未标注)
    annotated_at: str | None

class ExtractionStats(BaseModel):
    total_records: int
    annotated_count: int
    accuracy: float               # correct / annotated_count
    by_type: dict[str, TypeStats] # 按类型分类统计
```

**抽验界面设计（cl-sys-* CSS 前缀）：**

抽验面板作为 Settings Tab 的子面板或独立的 QA 工具面板：
- 顶部：统计概览（总数 / 已标注 / 准确率 / 按类型分类）
- 列表区域：每条记录显示原始片段（左）和提取内容（右），底部三个按钮（正确/错误/部分正确）
- 过滤器：按提取类型（错误/Tips/关键问答）过滤

### 管道健康指标方案

**指标体系（对应 PRD NFR-OBS-02）：**

| 指标 | 数据来源 | 健康标准 | 告警条件 |
|------|---------|---------|---------|
| 搜索通道存活率 | agentic_rag 各通道返回结果数 | 6/6 返回数据 | 任一通道返回空 |
| 配置参数传递 | adapter.py 参数校验 | 全部参数正确 | 任一参数无效 |
| 索引一致性 | LanceDB 同文件记录数 | 每文件 1 份 | 同文件 > 1 份 |
| Reranker 状态 | reranker 输出 vs 输入排序 | 排序发生变化 | 输出 = 输入（空壳） |
| CRAG 触发率 | CRAG 日志统计 | 15-30% | < 10% 或 > 50% |
| Faithfulness | faithfulness_check 日志 | 平均 >= 0.85 | 平均 < 0.85 |
| 难度匹配率 | difficulty_matcher 统计 | >= 70% | < 70% |

**健康状态判定：**

```python
class PipelineHealthStatus(BaseModel):
    overall: str                    # "healthy" | "degraded" | "critical"
    metrics: list[HealthMetric]     # 各指标详情
    last_updated: str               # ISO 8601
    error_summary: ErrorAggregation # 错误分类聚合

class HealthMetric(BaseModel):
    name: str
    status: str                     # "healthy" | "warning" | "critical"
    value: float | str
    threshold: str                  # 健康标准描述
    message: str | None             # 异常时的告警消息
```

### 错误自动分类规则

| 错误类型 | 分类依据 | 典型异常 |
|---------|---------|---------|
| LLM 错误 | LiteLLM 调用异常 | APIError, RateLimitError, AuthenticationError, Timeout |
| 网络错误 | 连接/通信异常 | ConnectionError, TimeoutError, HTTPError (5xx) |
| 算法异常 | 内部计算异常 | ValueError (BKT/FSRS), KeyError, IndexError in pipeline |
| 数据异常 | 存储读写异常 | Neo4j/SQLite/LanceDB 查询失败, 数据格式不匹配 |

分类通过异常类型层级匹配实现（不需要 LLM）：
- 匹配优先级：精确类名匹配 > 父类匹配 > 模块来源推断 > 默认"未分类"
- 每条错误记录：时间戳 + 错误类型 + 分类 + 来源模块 + 堆栈摘要

### 架构约束与注意事项

- **LiteLLM 统一调用**：题目难度估计的 LLM 调用必须通过 LiteLLM SDK
- **异步非阻塞**：难度匹配评估异步执行，不阻塞出题响应。使用 `asyncio.create_task()` 后台执行
- **EventBus 集成**：难度评估完成后发布 `DIFFICULTY_EVALUATED` 事件（Tier3 fire-and-forget），供日志和监控消费
- **SQLite 存储**：抽验记录和匹配统计存储在 SQLite 中（复用现有 aiosqlite 基础设施），表名 `qa_extraction_records` 和 `qa_difficulty_logs`
- **性能考量**：管道健康指标查询不应每次实时检测所有通道，使用缓存策略（30s TTL），后台定期刷新
- **API 响应格式**：遵循项目统一格式 `{"data": {...}, "meta": {"timestamp": "..."}}`

### Project Structure Notes

**新增文件（按架构目录规范）：**

| 文件 | 目录 | 说明 |
|------|------|------|
| `difficulty_matcher.py` | `backend/app/services/` | 出题难度匹配评估服务 |
| `extraction_validator.py` | `backend/app/services/` | 结构化提取抽验服务 |
| `error_aggregator.py` | `backend/app/services/` | 错误分类与聚合服务 |
| `qa_models.py` | `backend/app/models/` | QA 质量相关 Pydantic 模型 |
| `test_difficulty_matcher.py` | `backend/tests/unit/` | 难度匹配单元测试 |
| `test_extraction_validator.py` | `backend/tests/unit/` | 提取抽验单元测试 |
| `test_error_aggregator.py` | `backend/tests/unit/` | 错误聚合单元测试 |
| `test_qa_pipeline_health.py` | `backend/tests/integration/` | 管道健康集成测试 |
| `ExtractionValidator.svelte` | `obsidian-canvas-learning/src/components/system/` | 提取抽验前端组件 |
| `PipelineHealth.svelte` | `obsidian-canvas-learning/src/components/system/` | 管道健康前端组件 |

**修改文件：**

| 文件 | 修改内容 |
|------|---------|
| `backend/app/services/question_generator.py` | 出题后调用 DifficultyMatcher 异步评估 |
| `backend/app/services/conversation_archive.py` | 提取时同时写入抽验记录表 |
| `backend/app/services/health_monitor.py` | 扩展管道健康指标聚合 |
| `backend/app/api/v1/system.py` | 新增 5 个 QA 相关 API 端点 |
| `backend/app/models/canvas_events.py` | 追加 `DIFFICULTY_EVALUATED` 事件枚举 |
| `backend/app/middleware/logging_middleware.py` | 集成错误自动分类 |

**不触及的文件：**

- `agentic_rag/` 管道代码（仅读取其日志数据做统计）
- `mcp/` MCP 工具定义
- IndexedDB schema（前端组件通过 REST API 获取数据）
- `autoscore.py`（评分系统是上游，本 Story 仅消费其输出数据）

### References

- [Source: _bmad-output/planning-artifacts/prd.md#能力域9 — FR-QA-06 出题难度匹配率>=70%, FR-QA-07 结构化提取人工抽验]
- [Source: _bmad-output/planning-artifacts/prd.md#可观测性 — NFR-OBS-02 管道健康指标实时可查, NFR-OBS-03 错误自动分类聚合]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns — #4 算法管道完整性 AutoSCORE→BKT/FSRS, #7 错误处理与可观测性]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — services/health_monitor.py, middleware/logging_middleware.py, middleware/cost_tracker.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR能力域→文件映射 — 9.质量保证: middleware/* + audit/guardian + 结构化日志]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment — 监控: 100% LLM调用日志 + 管道健康指标 + 错误不静默]
- [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points — 考察启动流 question_generator→autoscore→EventBus→mastery_engine]
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns — 错误处理分层 + EventBus 事件定义规范]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.4 — AC 原始定义]

### 依赖关系说明

本 Story 无硬依赖，可与 Epic 7 其他 Story 并行开发：
- **Story 7.1**（Faithfulness）：本 Story 聚合其 Faithfulness 分数到管道健康指标，但不依赖其完成（缺失时指标显示"暂无数据"）
- **Story 7.2**（LLM 日志）：本 Story 的日志记录可独立于 7.2 的日志体系，后续统一
- **Story 6.3/6.4**（出题/评分）：本 Story 的 DifficultyMatcher 需要 `question_generator.py` 存在，但可先实现独立服务，后续集成
- **Story 3.8**（对话归档）：本 Story 的 ExtractionValidator 需要 `conversation_archive.py` 的提取输出，同理可先独立实现

## Dev Agent Record

### Agent Model Used

(To be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
