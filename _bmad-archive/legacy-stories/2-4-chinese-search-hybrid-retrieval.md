# Story 2.4: Phase 1 — 中文搜索与混合检索

Status: ready-for-dev

## Story

As a 用户,
I want 中文笔记搜索和英文笔记搜索效果相当，支持按课程/标签过滤，
so that 我的中文学习笔记不再搜不到。

## Acceptance Criteria

1. **AC-1: jieba 中文预分词——索引阶段**
   - **Given** 用户的 vault 中有中文 Markdown 笔记
   - **When** 索引管道处理这些笔记（Story 2.3 bge-m3 迁移完成后）
   - **Then** 中文内容在存入 LanceDB FTS 索引前经过 jieba 分词处理（空格分隔）
   - **And** 分词后的文本存入 `content_tokenized` 字段（或覆盖 `content` 的 FTS 索引内容）
   - **And** 英文内容不受 jieba 影响（jieba 对英文直接放行）
   - **And** 索引创建使用 `jieba_tokenizer` 或等效的中文分词器配置
   - **And** jieba 版本 >= 0.42（NFR-RET-COMPAT-04）

2. **AC-2: jieba 中文预分词——查询阶段**
   - **Given** 用户输入中文查询（如"贝叶斯定理的先验概率"）
   - **When** 查询进入 Sparse/FTS 搜索通道
   - **Then** 查询文本同样经过 jieba 分词处理（与索引阶段一致的分词策略）
   - **And** 分词后的查询能正确匹配分词后的索引内容
   - **And** 中文关键词"贝叶斯""先验概率"能独立命中包含这些词的笔记

3. **AC-3: bge-m3 Sparse 向量搜索激活**
   - **Given** Story 2.3 已完成 bge-m3 迁移，Dense 1024d 向量已可用
   - **When** bge-m3 Sparse 向量功能激活
   - **Then** 索引阶段同时生成 Dense 向量和 Sparse 向量（bge-m3 `model.encode()` 的 `return_sparse=True`）
   - **And** Sparse 向量存入 LanceDB（使用 LanceDB 原生 sparse vector 支持）
   - **And** 搜索阶段 Sparse 通道使用 Sparse 向量检索（非 FTS 全文搜索替代，而是互补）
   - **And** Sparse 向量搜索对中文和英文均有效（bge-m3 原生支持多语言 Sparse）

4. **AC-4: Hybrid Search 激活（语义 + 关键词双路同时工作）**
   - **Given** Dense 向量搜索（语义）和 Sparse/FTS 搜索（关键词）两条通道均已就绪
   - **When** 用户执行搜索查询
   - **Then** `lancedb_client.py` 的 `search()` 方法在 `query_type="hybrid"` 模式下同时执行 Dense + Sparse/FTS 两路搜索
   - **And** 两路结果通过 RRF 融合（已有 `_rrf_fuse` 实现）
   - **And** Hybrid 模式为默认搜索模式（非仅 Dense）
   - **And** 单路故障时降级为另一路结果（不因一路失败导致全部失败）

5. **AC-5: 按课程/标签前置过滤搜索范围**
   - **Given** 笔记 Frontmatter 中有 `course`/`course_id` 和 `tags` 字段（Story 2.3 面包屑前缀已解析 Frontmatter 元数据）
   - **When** 搜索请求携带 `course_id` 或 `tags` 过滤参数
   - **Then** 搜索在执行前按 `course_id` 和/或 `tags` 预过滤 LanceDB 数据范围（`.where()` 条件）
   - **And** 过滤后的搜索范围缩小，提升精度和性能
   - **And** 无过滤参数时搜索全量数据（向后兼容）
   - **And** `tags` 过滤支持多标签 OR 匹配（包含任一标签即命中）

6. **AC-6: 20 个中文查询 A/B 测试验证效果达标**
   - **Given** 完成 AC-1 ~ AC-5 的全部实现
   - **When** 执行 20 个中文查询的 A/B 对比测试
   - **Then** 中文查询能正确匹配中文笔记内容（定性：搜得到、排在前面）
   - **And** 中文检索效果与英文检索效果相当（FR-RET-09）
   - **And** 测试覆盖多种查询类型：单词、短语、句子、专业术语、中英混合
   - **And** 记录 20 个测试的查询文本、返回结果数、top-3 结果内容、相关性评分
   - **And** 至少 15/20（75%）的查询 top-3 结果包含相关内容

## Tasks / Subtasks

- [ ] **Task 1: jieba 预分词集成——索引阶段** (AC: #1)
  - [ ] 1.1 在 `requirements.txt` / `pyproject.toml` 中确认 `jieba >= 0.42` 依赖已添加（或添加）
  - [ ] 1.2 在 `src/agentic_rag/clients/lancedb_client.py` 的索引方法中（`index_single_file` / `add_documents`），添加 jieba 分词预处理步骤
  - [ ] 1.3 实现 `_jieba_tokenize(text: str) -> str` 工具函数：输入原文，输出空格分隔的分词文本。使用 `jieba.cut(text, cut_all=False)` 精确模式
  - [ ] 1.4 对每个 document 的 `content` 字段进行 jieba 分词，结果存入 `content_tokenized` 字段（或直接用于 FTS 索引创建）
  - [ ] 1.5 FTS 索引创建时使用分词后的字段：`tbl.create_fts_index("content_tokenized", replace=True)` 或配置 Lance 原生 jieba tokenizer（如 LanceDB 版本支持）
  - [ ] 1.6 确保英文内容经过 jieba 不被错误拆分（jieba 对纯英文直接按空格切分，验证无副作用）

- [ ] **Task 2: jieba 预分词集成——查询阶段** (AC: #2)
  - [ ] 2.1 在 `lancedb_client.py` 的 `search()` 方法中，FTS 搜索分支执行前对查询文本进行 jieba 分词
  - [ ] 2.2 分词后的查询用于 FTS 搜索：`table.search(tokenized_query, query_type="fts")`
  - [ ] 2.3 确保查询端分词策略与索引端一致（同样使用 `jieba.cut(text, cut_all=False)` 精确模式）
  - [ ] 2.4 添加日志记录分词前后的查询文本，便于调试分词效果

- [ ] **Task 3: bge-m3 Sparse 向量激活** (AC: #3)
  - [ ] 3.1 确认 Story 2.3 的 bge-m3 编码方法已支持 `return_sparse=True`（FlagEmbedding API）
  - [ ] 3.2 修改索引管道：编码时同时获取 Dense + Sparse 向量，Sparse 向量存入 LanceDB 的独立列（如 `sparse_vector`）
  - [ ] 3.3 在 `lancedb_client.py` 的 `search()` 中添加 Sparse 向量搜索分支：使用 bge-m3 对查询编码获取 Sparse 查询向量，执行 Sparse 向量搜索
  - [ ] 3.4 Sparse 搜索与 FTS 搜索的关系确认：Sparse 向量搜索是 bge-m3 原生的稀疏检索（学习到的词权重），FTS 是 LanceDB Tantivy 全文搜索（jieba 分词后的 BM25 匹配）。两者互补，不替代
  - [ ] 3.5 如果 Sparse 向量维度/格式与 LanceDB 的 sparse vector 列不兼容，提供转换逻辑

- [ ] **Task 4: Hybrid Search 激活与默认化** (AC: #4)
  - [ ] 4.1 审查 `lancedb_client.py` 现有的 `search()` 方法中 `query_type="hybrid"` 分支（已有 Dense + FTS RRF 融合逻辑）
  - [ ] 4.2 扩展 hybrid 模式为三路融合：Dense（语义向量） + Sparse（bge-m3 稀疏向量） + FTS（jieba 分词 BM25）。如三路 RRF 融合复杂度过高，可简化为 Dense + FTS（jieba 增强）双路
  - [ ] 4.3 将搜索的默认 `query_type` 从 `"vector"` 改为 `"hybrid"`，确保所有调用方默认使用混合搜索
  - [ ] 4.4 在 `retrieve_lancedb` retriever 节点中，确认传入 `query_type="hybrid"` 参数
  - [ ] 4.5 添加降级逻辑：FTS 索引不存在时回退为纯 Dense 搜索（log warning），Sparse 不可用时回退为 Dense + FTS
  - [ ] 4.6 验证 `_rrf_fuse()` 在输入为空列表时能正常工作（不报错）

- [ ] **Task 5: 课程/标签前置过滤** (AC: #5)
  - [ ] 5.1 确认 LanceDB 表 schema 中包含 `course_id`（或 `course`/`subject`）和 `tags` 列（来自 Story 2.3 Frontmatter 元数据解析）
  - [ ] 5.2 在 `search()` 方法签名中添加 `course_id: Optional[str] = None` 和 `tags: Optional[List[str]] = None` 参数
  - [ ] 5.3 搜索执行前构建 `.where()` 过滤条件：
    - `course_id` 不为空时：`.where(f"course_id = '{course_id}'")`
    - `tags` 不为空时：构建 OR 条件匹配任一标签（LanceDB SQL where 语法）
  - [ ] 5.4 过滤条件同时应用于 Dense、Sparse、FTS 三路搜索分支
  - [ ] 5.5 确保现有的 `canvas_file` 和 `subject` 过滤逻辑与新的 `course_id`/`tags` 过滤兼容（不冲突，可叠加）
  - [ ] 5.6 无过滤参数时不添加 where 条件（向后兼容）

- [ ] **Task 6: retrieve_lancedb retriever 适配** (AC: #3, #4, #5)
  - [ ] 6.1 在 `src/agentic_rag/retrievers/` 中定位 LanceDB retriever 节点（或 `nodes.py` 中的 `retrieve_lancedb` 函数）
  - [ ] 6.2 修改 retriever 调用 `search()` 时传入 `query_type="hybrid"` + 从 state 中提取的 `course_id` / `tags`
  - [ ] 6.3 确认 `CanvasRAGState` 中有 `course_id` 和 `tags` 字段（如无，在 `state.py` 中添加 Optional 字段）
  - [ ] 6.4 确认上游 adapter / API 能将用户请求中的 `course_id`/`tags` 传入 state

- [ ] **Task 7: 20 个中文 A/B 测试** (AC: #6)
  - [ ] 7.1 准备 20 个中文测试查询，覆盖以下类别（每类至少 3-4 个）：
    - 单词查询（如"贝叶斯"）
    - 短语查询（如"梯度下降算法"）
    - 句子查询（如"如何理解马尔可夫链的平稳分布"）
    - 专业术语（如"反向传播"、"交叉熵损失"）
    - 中英混合（如"softmax 函数的导数"）
  - [ ] 7.2 对每个查询执行搜索，记录：查询文本、jieba 分词结果、返回结果数、top-3 结果内容摘要、top-3 分数
  - [ ] 7.3 人工评判 top-3 结果相关性（相关/部分相关/不相关）
  - [ ] 7.4 计算通过率：至少 15/20（75%）的查询 top-3 包含相关内容
  - [ ] 7.5 对比 Hybrid Search vs 纯 Dense Search 的效果差异（如可行，选 5 个查询做对比）
  - [ ] 7.6 将测试结果记录到 `_bmad-output/implementation-artifacts/tests/test-summary-2.4.md`

- [ ] **Task 8: 代码质量检查与 lint** (AC: #1-#6)
  - [ ] 8.1 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 8.2 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 8.3 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）
  - [ ] 8.4 确认 jieba 分词是真正调用而非 `return text`（防空壳）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**。中文搜索不工作是 HIGH 级缺陷 H1（FTS 不支持中文分词），本 Story 修复此问题并激活 Hybrid Search。

#### 关键文件清单

| 文件 | 当前状态 | 修复/修改内容 |
|------|---------|-------------|
| `src/agentic_rag/clients/lancedb_client.py` | FTS 索引已创建但中文分词不工作（Tantivy 默认分词不支持中文）(HIGH H1) | 添加 jieba 预分词 + Sparse 搜索 + 课程/标签过滤 |
| `src/agentic_rag/clients/lancedb_client.py` L925-962 | Hybrid Search 已有 Dense+FTS RRF 融合框架 | **可复用**——扩展支持 jieba FTS + bge-m3 Sparse |
| `src/agentic_rag/clients/lancedb_client.py` L538-546 | FTS 索引创建 `tbl.create_fts_index("content")` | 修改为使用 jieba 分词后的内容创建 FTS 索引 |
| `src/agentic_rag/nodes.py` | `retrieve_lancedb` 节点 | 修改搜索调用参数（hybrid + course_id + tags） |
| `src/agentic_rag/state.py` | `CanvasRAGState` TypedDict | 可能需添加 `course_id` / `tags` 字段 |
| `src/agentic_rag/config.py` | 搜索配置参数 | 确认 hybrid 为默认 search_type |

#### 当前中文搜索不工作的根因（HIGH H1）

LanceDB 的 FTS 索引底层使用 Tantivy 搜索引擎。Tantivy 默认使用英文分词器（whitespace + stemming），对中文文本无法正确切词。例如"贝叶斯定理"会被当作一个整体 token，搜索"贝叶斯"无法匹配。

**社区验证的解决方案**（LanceDB GitHub #2168/#2329）：
- 方案 A：索引前用 jieba 分词，空格分隔，Tantivy 按空格切词即可匹配
- 方案 B：LanceDB 原生支持 jieba tokenizer（如版本支持 `tokenizer_name="jieba"`）
- 推荐：先用方案 A（最成熟、社区验证最多），后续版本如 LanceDB 原生支持再迁移

### 依赖关系

- **前置 Story 2.3**（bge-m3 迁移 + 标题智能分块 + 面包屑前缀）**必须先完成**——本 Story 依赖 bge-m3 的 Sparse 向量输出和 Frontmatter 元数据解析
- **前置 Story 2.1/2.2**（死代码清理 + 搜索通道修复）已完成基础管道激活
- **后续 Story 2.5**（精排升级）会在本 Story 基础上升级 RRF 融合策略（3 组分层 RRF）
- **后续 Story 2.8**（元数据过滤与邻居扩展）会进一步扩展过滤能力（渐进范围搜索、Wiki-links 扩展）

### 技术决策

1. **jieba 分词策略**：使用 `jieba.cut(text, cut_all=False)` 精确模式（非全模式）。精确模式分词准确，全模式会产生大量冗余词导致 FTS 噪声。来源：jieba 官方文档 + LanceDB 社区验证。
2. **Sparse 向量 vs FTS**：两者互补而非替代。bge-m3 Sparse 是学习到的词权重（语义级），FTS 是 BM25 词频匹配（统计级）。Sparse 对语义同义词更好，FTS 对精确关键词更好。来源：bge-m3 论文 + RAG 社区实践。
3. **Hybrid 默认化**：将默认搜索模式从纯 Dense 改为 Hybrid（Dense + FTS），与 LanceDB 官方 SQuAD benchmark 验证的 11-16% 提升一致。
4. **课程/标签过滤在 Story 2.4 实现**：虽然 Story 2.8 有更完整的元数据过滤（渐进范围、Wiki-links），但 `course_id` 和 `tags` 的基础 where 过滤是 FR-RET-P-02 的核心要求，且实现简单（`.where()` 一行），放在本 Story 与中文搜索一起交付。

### 不做的事项（防蔓延 DD-10）

- 不实现渐进范围搜索（同课程→相关课程→全库）——Story 2.8 的范围
- 不实现 Wiki-links 邻居扩展——Story 2.8 的范围
- 不实现跨课程 Tag Jaccard 桥接——Story 2.8 的范围
- 不修改 RRF 融合策略（当前扁平 RRF 可工作，分层 RRF 在 Story 2.5）
- 不实现 Adaptive-k 动态截取——Story 2.5 的范围
- 不修改分块策略——Story 2.3 已完成
- 不修改前端代码——纯后端管道修改

### FR 映射

| FR ID | 需求 | 本 Story 实现 |
|-------|------|-------------|
| FR-IDX-05 | jieba 中文预分词 | AC-1, AC-2: jieba 索引+查询端分词 |
| FR-RET-01 | 语义+关键词混合检索 | AC-4: Hybrid Search 激活 |
| FR-RET-09 | 中文检索与英文检索效果相当 | AC-6: 20 个中文 A/B 测试验证 |
| FR-RET-P-02 | 按课程/标签过滤 | AC-5: course_id + tags where 过滤 |

### Project Structure Notes

- 修改范围限于 `src/agentic_rag/` 目录
- `lancedb_client.py` 是核心修改文件（索引 + 搜索两端均需修改）
- `state.py` 可能需添加 `course_id`/`tags` 字段到 `CanvasRAGState`
- 新增 `jieba` 依赖需确认 Docker 镜像中已安装
- jieba 首次加载字典约 1-2 秒，建议在应用启动时预加载（`jieba.initialize()`）

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 1] — 任务 1.4（bge-m3 Sparse + jieba）和 1.5（激活混合搜索）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#代码审查发现汇总] — HIGH H1: 中文 FTS 不工作
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — jieba 选型 + Hybrid Search 选型
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#检索与个性化] — 四层路由+六路物理通道 + jieba 中文预分词 + bge-m3 Sparse
- [Source: _bmad-output/planning-artifacts/architecture.md#Important Decisions] — 索引管道确认：bge-m3 Dense+Sparse(MVP) + jieba 中文
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#验收标准来源] — LanceDB SQuAD Hybrid 提升 11-16%, jieba 社区 workaround
- [Source: src/agentic_rag/clients/lancedb_client.py L538-546] — 当前 FTS 索引创建
- [Source: src/agentic_rag/clients/lancedb_client.py L925-962] — 当前 Hybrid Search 框架（Dense + FTS RRF）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
