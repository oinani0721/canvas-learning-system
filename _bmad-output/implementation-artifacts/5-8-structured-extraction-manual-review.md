# Story 5.8: 结构化提取人工抽验

Status: ready-for-dev

## Story

As a 用户,
I want 系统从对话中自动提取的错误/Tips/关键问答支持人工抽验，
So that 我能确认 AI 的提取结果是否准确，发现错误提取后可修正。

## Acceptance Criteria

**Given** 对话归档后 AI 自动提取了错误/Tips/关键问答
**When** 用户在学习档案面板中查看提取结果
**Then** 每条提取内容旁有"查看来源"按钮，跳转到原始对话上下文

**AC-1: 来源溯源**
- 每条提取记录展示 `original_text`（原始对话片段）和 `extracted_content`（提取结果）并排对比
- "查看来源"按钮可展开/折叠原始对话上下文
- 来源文本中高亮匹配的关键片段

**AC-2: 标注操作**
- 用户可标记每条提取为"提取正确"(correct)、"提取错误"(incorrect) 或"部分正确"(partial)
- 标注后显示标注状态徽章（绿色/红色/黄色）
- 已标注记录不可重复标注（需先撤销）

**AC-3: 准确率统计**
- 管道健康指标区域显示提取准确率（correct / annotated 比例）
- 按类型(error/tip/key_qa)分别展示准确率
- 准确率 < 80% 时显示警告图标

**AC-4: 修改/删除错误提取**
- 用户可手动编辑 `extracted_content` 字段修正提取内容
- 用户可删除错误提取记录
- 编辑/删除操作需二次确认

**AC-5: 筛选与分页**
- 按提取类型筛选：error / tip / key_qa / 全部
- 按标注状态筛选：已标注 / 未标注 / 全部
- 分页浏览（每页 20 条，支持翻页）

## Tasks / Subtasks

### Task 1: 后端 — 扩展 ExtractionValidator 支持编辑和删除 (BE)

**1.1** 在 `backend/app/services/extraction_validator.py` 中添加 `update_content()` 方法
- 接收 `record_id` 和 `new_content` 参数
- 更新 `extracted_content` 字段和 `updated_at` 时间戳
- 返回更新后的 `ExtractionRecord`

**1.2** 在 `backend/app/services/extraction_validator.py` 中添加 `delete_record()` 方法
- 软删除：设置 `deleted_at` 字段而非物理删除
- 查询时自动排除已删除记录

**1.3** 在 `backend/app/services/extraction_validator.py` 中添加 `reset_annotation()` 方法
- 清除 `annotation` 和 `annotated_at` 字段（支持撤销标注）

**1.4** 扩展 `_CREATE_TABLE` SQL 添加 `updated_at` 和 `deleted_at` 列
- 使用 `ALTER TABLE` 迁移脚本兼容已存在的表
- 添加相应索引

**1.5** 扩展 `get_records()` 方法支持按标注状态筛选
- 新增 `annotation_filter` 参数：`'annotated'` / `'unannotated'` / `None`
- WHERE 子句动态拼接

### Task 2: 后端 — 扩展 REST API 端点 (BE)

**2.1** 在 `backend/app/api/v1/system.py` 中添加 `PATCH /api/v1/system/extraction-records/{record_id}` 端点
- 请求体：`{ "extracted_content": "..." }`
- 调用 `ExtractionValidator.update_content()`
- 返回更新后的记录

**2.2** 在 `backend/app/api/v1/system.py` 中添加 `DELETE /api/v1/system/extraction-records/{record_id}` 端点
- 调用 `ExtractionValidator.delete_record()`
- 返回 204 No Content

**2.3** 在 `backend/app/api/v1/system.py` 中添加 `DELETE /api/v1/system/extraction-records/{record_id}/annotation` 端点
- 调用 `ExtractionValidator.reset_annotation()`
- 返回重置后的记录

**2.4** 扩展现有 `GET /api/v1/system/extraction-records` 端点
- 添加 `annotation_filter` 查询参数
- 传递给 `ExtractionValidator.get_records()`

**2.5** 添加请求体 Pydantic model `UpdateExtractionRequest`
- `extracted_content: str = Field(..., min_length=1)`

### Task 3: 前端 — ExtractionReviewPanel 组件 (FE)

**3.1** 创建 `frontend/src/components/extraction/ExtractionReviewPanel.tsx`
- 使用 shadcn/ui 的 Card、Table、Badge、Button 组件
- 展示提取记录列表：类型图标 + 提取内容摘要 + 标注状态徽章
- 响应式布局适配侧面板

**3.2** 创建 `frontend/src/components/extraction/ExtractionRecordRow.tsx`
- 单条提取记录行组件
- 左侧：提取类型图标（Error=红色、Tip=蓝色、KeyQA=绿色）
- 中间：`extracted_content` 文本（可折叠长文本）
- 右侧：标注操作按钮组

**3.3** 创建 `frontend/src/components/extraction/SourceViewer.tsx`
- "查看来源"展开面板
- 并排展示 `original_text`（左/上）和 `extracted_content`（右/下）
- `original_text` 中关键词高亮（简单文本匹配）

**3.4** 创建 `frontend/src/components/extraction/ExtractionStats.tsx`
- 展示总体准确率进度条
- 按类型分列准确率
- 准确率 < 80% 时 Badge 变红 + 警告图标

### Task 4: 前端 — 标注与编辑交互 (FE)

**4.1** 实现标注按钮组（三态切换）
- 正确(check icon, green) / 错误(x icon, red) / 部分正确(minus icon, yellow)
- 已标注状态显示徽章，点击可撤销（调用 reset_annotation API）
- 乐观更新 UI + 后端确认

**4.2** 实现编辑提取内容功能
- 点击"编辑"按钮切换为 textarea 内联编辑模式
- 保存调用 PATCH API，取消恢复原文
- shadcn/ui 的 Dialog 二次确认

**4.3** 实现删除提取记录功能
- 点击"删除"按钮弹出 shadcn/ui AlertDialog 二次确认
- 确认后调用 DELETE API，从列表移除

**4.4** 实现筛选栏
- 类型筛选：shadcn/ui Select（全部 / error / tip / key_qa）
- 标注状态筛选：shadcn/ui Select（全部 / 已标注 / 未标注）
- 筛选变化时重新请求后端

**4.5** 实现分页控件
- shadcn/ui Pagination 组件
- 显示总条目数和当前页
- 翻页时 GET 请求带 page 参数

### Task 5: 前端 — API Client 扩展 (FE)

**5.1** 在 `frontend/src/services/api-client.ts` 的 `ApiClient` 类中添加以下方法：
- `getExtractionRecords(type?, annotationFilter?, page?, pageSize?): Promise<ExtractionRecordPage>`
- `annotateExtraction(recordId, annotation): Promise<void>`
- `resetAnnotation(recordId): Promise<void>`
- `updateExtractionContent(recordId, content): Promise<ExtractionRecord>`
- `deleteExtractionRecord(recordId): Promise<void>`
- `getExtractionStats(): Promise<ExtractionStats>`

**5.2** 在 `frontend/src/services/api-client.ts` 中添加对应的 TypeScript 接口类型
- `ExtractionRecord`、`ExtractionRecordPage`、`ExtractionStats`、`TypeStats`

### Task 6: 前端 — 集成到学习档案面板 (FE)

**6.1** 在学习档案面板中添加"提取质量"Tab 或 Section
- 使用 shadcn/ui Tabs 组件
- Tab 标签显示未标注数量徽章

**6.2** 在管道健康面板或 Dashboard 中嵌入 ExtractionStats 摘要卡片
- 显示准确率数值 + 趋势指示
- 点击可跳转到完整的 ExtractionReviewPanel

### Task 7: 管道集成 — conversation_archive 提取时写入 ExtractionValidator (BE)

**7.1** 在 `backend/app/services/conversation_archive.py` 的 `_archive_to_warm()` 方法中，distillation 完成后调用 `ExtractionValidator.store_record()`
- 为每条 tip、error、key_qa 分别创建 ExtractionRecord
- 传入 `source_session_id`、`source_node_id`、`original_text`（对话片段）、`extracted_content`（提取结果）、`extraction_type`
- 使用 `conversation_distiller.py` 已有的 `DistillationResult` 数据

**7.2** 确保 `context_extract_v1.md` prompt 的输出格式中 `evidence` 字段（原文引用）被正确传递到 ExtractionRecord 的 `original_text` 字段

## Dev Notes

### 已有后端代码（可直接复用/扩展）

- **`backend/app/services/extraction_validator.py`** — ExtractionValidator 类已实现核心功能：
  - `store_record()` — 存储提取记录
  - `annotate()` — 提交标注（correct/incorrect/partial）
  - `get_records()` — 分页查询（支持 type 筛选）
  - `get_stats()` — 准确率统计（含 per-type breakdown + 80% 阈值告警）
  - 使用 SQLite (aiosqlite) 存储，表 `qa_extraction_records`
  - **需要扩展**：编辑、删除、标注重置、标注状态筛选

- **`backend/app/models/qa_models.py`** — 已有 Pydantic models：
  - `ExtractionRecord`、`ExtractionRecordPage`、`ExtractionStats`、`TypeStats`、`AnnotationRequest`
  - **需要扩展**：`UpdateExtractionRequest`

- **`backend/app/api/v1/system.py`** — 已有 API 端点：
  - `GET /api/v1/system/extraction-records` — 分页查询
  - `POST /api/v1/system/extraction-records/{record_id}/annotate` — 标注
  - `GET /api/v1/system/qa-metrics` — 含 extraction_quality 统计
  - **需要扩展**：PATCH（编辑）、DELETE（删除）、DELETE annotation（撤销标注）

- **`backend/app/services/conversation_distiller.py`** — 已实现 LLM 提取管道：
  - `distill()` / `distill_and_persist()` — 从对话中提取 errors/tips/qa_highlights
  - 输出 `DistillationResult`（含 `ExtractedTip`、`ExtractedError`、`ExtractedQA`）

- **`backend/app/services/conversation_archive.py`** — Hot->Warm 归档触发提取：
  - `_archive_to_warm()` 已调用 `distiller.distill_and_persist()`
  - **需要补充**：提取完成后调用 `ExtractionValidator.store_record()` 持久化

- **`backend/app/services/error_classifier.py`** — 4 类错误分类（LLM + heuristic fallback）

- **`backend/app/prompts/context_extract_v1.md`** — 提取 prompt 模板，含 `evidence` 字段

### 前端技术栈

- **React + TypeScript + shadcn/ui**（Tauri 桌面应用，非 Obsidian/Svelte）
- **API Client**: `frontend/src/services/api-client.ts` — 标准 fetch()，自动 snake_case/camelCase 转换
- **状态管理**: React hooks（useState/useEffect）+ Zustand（如需跨组件共享）
- **UI 组件**: shadcn/ui（Card, Table, Badge, Button, Dialog, AlertDialog, Select, Tabs, Pagination）

### Architecture Compliance

- **FR-QA-07**: 结构化提取结果支持人工抽验 — 本 Story 的核心功能
- **FR-TRACE-05**: 自动提取持久化 — Hot->Warm 归档管道已存在，需补齐 ExtractionValidator 集成
- **API Envelope**: 所有端点遵循 `{ data: {...}, meta: { timestamp: "..." } }` 格式
- **错误处理**: 前端所有 API 调用需 try/catch + 静默降级（NFR-REL-02）

### References

- [epics.md — Story 5.8 定义](../_bmad-output/planning-artifacts/epics.md) — Epic 5: 精通度追踪、学习档案与 Dashboard
- [architecture.md — FR-QA-07](../_bmad-output/planning-artifacts/architecture.md) — 结构化提取人工抽验
- [architecture.md — 能力域 8 学习档案](../_bmad-output/planning-artifacts/architecture.md) — Hot-Warm-Cold 自动提取归档管道
- `backend/app/services/extraction_validator.py` — 核心后端服务
- `backend/app/services/conversation_distiller.py` — LLM 提取管道
- `backend/app/services/conversation_archive.py` — 归档触发器
- `backend/app/api/v1/system.py` — 现有 API 端点
- `backend/app/models/qa_models.py` — 现有数据模型
- `backend/app/prompts/context_extract_v1.md` — 提取 prompt 模板
- `frontend/src/services/api-client.ts` — 前端 API 客户端

## Dev Agent Record

### Agent Model Used
(To be filled by dev agent)

### Debug Log References
(To be filled by dev agent)

### Completion Notes List
(To be filled by dev agent)

### File List
(To be filled by dev agent — list all created/modified files)
