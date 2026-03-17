# Story 2.9: Phase 2 — 图片检索管道

Status: ready-for-dev

## Story

As a 用户,
I want 粘贴的图片中的文字/公式/概念可以被搜索到,
so that 截图的课件内容也能在 AI 对话中被引用。

## Acceptance Criteria

1. **AC-1: Gemini OCR 结构化提取**
   - **Given** 用户粘贴了一张包含公式/文字的课件截图到白板
   - **When** 后台 OCR 提取管道执行
   - **Then** 通过 Gemini Vision API 提取图片中的：文字内容、内容类型分类（公式/文字/图表/代码）、摘要、核心概念
   - **And** 提取结果为结构化 JSON 格式（`text`, `content_type`, `summary`, `concepts: List[str]`）
   - **And** 单张图片 OCR 处理 < 10 秒（NFR-PERF-05）
   - **And** OCR 通过 LiteLLM SDK 调用（不锁定厂商，model 从 config 读取）

2. **AC-2: 图片内容走文本索引管道**
   - **Given** OCR 提取完成，产出结构化文本
   - **When** 索引管道处理图片内容
   - **Then** 提取的文本通过与笔记相同的索引管道（分块 → bge-m3 向量化 → LanceDB 写入）
   - **And** 图片内容在 LanceDB 中的 `source_type` 标记为 `"image_ocr"`
   - **And** 图片的原始文件路径和白板节点 ID 保留在元数据中
   - **And** 索引使用 delete-before-insert 模式（复用 Story 2.7 的 fingerprint 基础设施）

3. **AC-3: 向量维度统一为 1024（修复 HIGH H3）**
   - **Given** 当前多模态管道存在向量维度冲突（384/768/1024 三处不一致）
   - **When** 图片内容向量化
   - **Then** 统一使用 bge-m3 1024d 向量（与文本索引完全相同的模型和维度）
   - **And** 清理所有硬编码的 384/768 维度引用
   - **And** 图片向量与文本向量在同一个 LanceDB 表中共存，支持统一搜索

4. **AC-4: 图片管道依赖注入修复（HIGH H4）**
   - **Given** 当前 `multimodal_store.py` 依赖注入无参数（`client=None`），全部返回空
   - **When** 图片索引和检索调用
   - **Then** 正确注入 LanceDB client 和 Gemini client
   - **And** 图片存储和检索返回真实数据（非空列表）
   - **And** 依赖注入失败时有明确错误日志（而非静默返回空）

5. **AC-5: 检索结果附带来源信息**
   - **Given** 图片 OCR 内容已被索引
   - **When** 用户搜索时命中图片 OCR 内容
   - **Then** 搜索结果附带来源信息：文件路径 + heading 路径 + 起止行号
   - **And** 图片内容在搜索结果中标注来源为"图片 OCR"（`source_type: "image_ocr"`）
   - **And** 结果中包含图片节点 ID（可用于前端定位到白板上的图片节点）

## Tasks / Subtasks

- [ ] **Task 1: Gemini OCR 结构化提取升级** (AC: #1)
  - [ ] 1.1 修改 `src/agentic_rag/processors/gemini_vision.py` 或 `backend/app/clients/gemini_client.py`：升级 OCR prompt 为结构化提取
  - [ ] 1.2 设计 OCR 提取 prompt：要求 Gemini 返回 JSON 格式 `{"text": "...", "content_type": "formula|text|diagram|code", "summary": "...", "concepts": ["...", "..."]}`
  - [ ] 1.3 使用 LiteLLM SDK 调用 Gemini Vision（`litellm.acompletion` with `messages` 包含 image_url），model 从 config `ocr_model` 字段读取
  - [ ] 1.4 JSON 解析异常处理：LLM 返回非标准 JSON 时，fallback 为纯文本提取（整个响应作为 text）
  - [ ] 1.5 添加重试逻辑：Gemini API 429/500 时最多重试 2 次（指数退避）
  - [ ] 1.6 添加延迟日志：`[OCR] Extracted {len(text)} chars, type={content_type} in {duration}ms`

- [ ] **Task 2: 图片内容索引管道** (AC: #2)
  - [ ] 2.1 新增 `index_image_content(node_id: str, image_path: str, ocr_result: Dict, table_name: str, subject: str) -> int` 方法（在 `lancedb_client.py` 或新建 `image_indexer.py`）
  - [ ] 2.2 将 OCR 提取的 `text` + `summary` + `concepts` 组合为可索引文本
  - [ ] 2.3 使用 bge-m3 向量化（与笔记索引相同的 `_init_vectorizer` + `batch_vectorize`）
  - [ ] 2.4 写入 LanceDB 时设置 `source_type: "image_ocr"`、`node_id: node_id`、`canvas_file: image_path`
  - [ ] 2.5 索引前先执行 delete-before-insert（按 `node_id` 或 `canvas_file` 删除旧数据）

- [ ] **Task 3: 向量维度统一（HIGH H3 修复）** (AC: #3)
  - [ ] 3.1 搜索代码库中所有硬编码的 `384`、`768` 维度引用（特别是 `multimodal_store.py`、`multimodal_vectorizer.py`、`image_processor.py`）
  - [ ] 3.2 统一为 `1024`（bge-m3 Dense 维度），或改为从 config 读取 `embedding_dim`
  - [ ] 3.3 确保图片向量和文本向量使用同一个 LanceDB 表（或维度兼容的不同表）
  - [ ] 3.4 如果多模态搜索使用独立表（`multimodal` 表），确保其 vector 列维度为 1024

- [ ] **Task 4: 依赖注入修复（HIGH H4）** (AC: #4)
  - [ ] 4.1 修复 `src/agentic_rag/storage/multimodal_store.py`：在 `__init__` 中正确接收 LanceDB client 参数（非 `client=None`）
  - [ ] 4.2 修复 multimodal 检索器（`src/agentic_rag/retrievers/multimodal_retriever.py`）：正确注入依赖
  - [ ] 4.3 在 FastAPI 依赖注入层（`backend/app/dependencies.py`）正确构建 multimodal 组件实例
  - [ ] 4.4 验证：调用图片索引和检索 API 返回真实数据（非空列表/None）

- [ ] **Task 5: 搜索结果来源信息** (AC: #5)
  - [ ] 5.1 确保图片 OCR 内容索引时保留完整元数据：`source_type: "image_ocr"`, `node_id`, `canvas_file`, `content_type`（公式/文字等）
  - [ ] 5.2 在 `_convert_to_search_results` 中正确映射图片 OCR 结果的来源信息
  - [ ] 5.3 搜索结果 `SearchResult` 的 `metadata` 中包含 `source_type` 字段，供前端区分展示

- [ ] **Task 6: 图片搜索通道集成** (AC: #1-#5)
  - [ ] 6.1 确认图片搜索通道在 `fan_out_retrieval` 的 6 路搜索中正确激活
  - [ ] 6.2 图片搜索结果参与 RRF 融合（归入 Personal 组，参考 Story 2.5 分组）
  - [ ] 6.3 图片搜索通道故障时不影响其他通道（独立 try/except）

- [ ] **Task 7: 端到端验证** (AC: #1-#5)
  - [ ] 7.1 准备测试场景：
    - 上传含公式的课件截图 → OCR 提取结构化内容 → 索引到 LanceDB
    - 搜索公式关键词 → 命中图片 OCR 内容 → 结果标记 source_type: "image_ocr"
    - 向量维度一致性检查：图片向量维度 == 1024
    - 依赖注入验证：multimodal_store 和 retriever 返回真实数据
  - [ ] 7.2 OCR 性能验证：单张图片处理 < 10 秒
  - [ ] 7.3 `ruff check src/agentic_rag/ backend/app/` 全量 lint 通过
  - [ ] 7.4 `ruff format --check src/agentic_rag/ backend/app/` 格式检查通过
  - [ ] 7.5 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，图片处理管道框架已存在（`processors/`、`storage/`、`retrievers/` 三个目录），但存在两个 HIGH 级缺陷（H3 向量维度冲突、H4 依赖注入断裂）导致管道完全不工作。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/processors/gemini_vision.py` | Gemini OCR 基础实现，返回纯文本 | **升级为结构化提取（JSON 格式）** |
| `src/agentic_rag/processors/image_processor.py` | 图片处理流程 | **集成 LiteLLM + 结构化提取** |
| `src/agentic_rag/storage/multimodal_store.py` | `client=None` 依赖注入断裂（HIGH H4） | **修复依赖注入** |
| `src/agentic_rag/retrievers/multimodal_retriever.py` | 图片检索器框架 | **修复依赖 + 向量维度统一** |
| `src/agentic_rag/processors/multimodal_vectorizer.py` | 向量化器，可能硬编码 384/768 维度 | **统一为 1024** |
| `src/agentic_rag/clients/lancedb_client.py` | 索引和搜索入口 | **新增 index_image_content 方法** |
| `backend/app/clients/gemini_client.py` | 后端 Gemini 客户端 | **参考/集成 LiteLLM 调用** |
| `backend/app/dependencies.py` | 依赖注入配置 | **修复 multimodal 组件实例化** |

#### 已知 HIGH 级缺陷

- **H3**：`multimodal_store.py`、`multimodal_vectorizer.py`、`image_processor.py` 中向量维度分别硬编码 384/768/1024，导致维度不匹配 → LanceDB 写入或搜索报错
- **H4**：`multimodal_store.py` 的 `__init__` 参数 `client=None`，所有方法实际执行时 `self.client is None`，返回空列表

### 依赖关系

- **前置 Story 2.3**（bge-m3 迁移）：向量化使用 bge-m3 1024d 模型
- **前置 Story 2.7**（文件指纹增量索引）：图片索引复用 delete-before-insert 去重机制
- **前置 Story 2.5**（精排与融合升级）：图片搜索结果参与 Personal 组 RRF 融合
- **后续 Story 2.12**（验收测试）：图片搜索作为验收测试的一部分

### 技术决策

1. **OCR 方案**：增强 Gemini OCR（文字+分类+摘要+概念→文本管道），不使用 BGE-VL/ColPali 视觉嵌入（Phase 2+ 远期评估）。
2. **索引策略**：图片 OCR 文本走与笔记相同的文本索引管道（bge-m3），不单独建视觉向量表。
3. **LLM 调用层**：使用 LiteLLM SDK（与主 PRD 决策一致），不硬编码 Gemini SDK。
4. **表结构**：图片 OCR 内容与笔记内容在同一个 `vault_notes` 表中（`source_type` 区分），简化搜索逻辑。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| Gemini OCR | `src/agentic_rag/processors/gemini_vision.py` |
| 图片处理器 | `src/agentic_rag/processors/image_processor.py` |
| 多模态存储 | `src/agentic_rag/storage/multimodal_store.py` |
| 多模态检索器 | `src/agentic_rag/retrievers/multimodal_retriever.py` |
| 向量化器 | `src/agentic_rag/processors/multimodal_vectorizer.py` |
| 后端 Gemini 客户端 | `backend/app/clients/gemini_client.py` |
| 依赖注入 | `backend/app/dependencies.py` |

### 不做的事项（防蔓延 DD-10）

- 不实现 BGE-VL/ColPali 视觉嵌入（Phase 2+ 远期评估）
- 不实现视频/音频处理管道（当前只处理图片）
- 不修改前端图片节点 UI（Story 1.6 的范围）
- 不实现图片索引状态指示的前端展示（Epic 1 / Epic 3 的范围）
- 不修改 LangGraph 图结构
- 不实现 OCR 结果缓存（当前规模不需要）

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-IDX-06 | AC-1, AC-2 | 图片 Gemini OCR → 文本管道索引 |
| FR-RET-P-08 | AC-5 | 检索结果附带来源信息 |

### Project Structure Notes

- 本 Story 涉及 `src/agentic_rag/` 和 `backend/app/` 两个目录
- 修复 H3/H4 需要跨多个文件修改，注意依赖链
- Gemini Vision API 需要图片 base64 编码或 URL，确认前端→后端的图片传递方式
- LiteLLM 的 vision 支持需确认版本兼容性

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 2] — 任务 2.5/2.6 图片管道修复 + 增强 Gemini OCR
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#HIGH 级] — H3 向量维度冲突、H4 依赖注入断裂
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — 图片检索选型依据
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.9] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — 图片双层处理架构
- [Source: src/agentic_rag/processors/gemini_vision.py] — 当前 Gemini OCR 实现
- [Source: src/agentic_rag/storage/multimodal_store.py] — 依赖注入断裂的存储层
- [Source: src/agentic_rag/retrievers/multimodal_retriever.py] — 图片检索器

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
