# Story 2.3: Phase 1 — bge-m3 模型迁移与分块升级

Status: ready-for-dev

## Story

As a 用户,
I want 系统使用 bge-m3 中英双语模型和智能分块策略,
so that 中英文笔记都能被准确检索，代码/公式/表格不会被切断。

## Acceptance Criteria

1. **AC-1: bge-m3 1024d Dense 向量生效**
   - **Given** Story 2.1+2.2 已完成（死代码清理、配置修复、搜索通道激活）
   - **When** 系统对笔记文本执行 embedding
   - **Then** 使用 bge-m3 模型（`BAAI/bge-m3`）生成 1024 维 Dense 向量
   - **And** LanceDB schema `vector` 列维度从 384 升级到 1024
   - **And** `MultimodalVectorizer` 改用 `FlagEmbedding` 的 `BGEM3FlagModel` 加载 bge-m3
   - **And** 旧模型配置（`sentence-transformers/all-MiniLM-L6-v2` 384d、`paraphrase-multilingual-MiniLM-L12-v2` 384d）全部替换
   - **And** 所有 hardcoded 384/768 维度引用更新为 1024

2. **AC-2: 标题智能分块（512 token 上限 + 句子边界）**
   - **Given** 一个 Markdown 笔记文件被索引
   - **When** 分块算法执行
   - **Then** 第一级按 H1-H4 heading 切分（保留现有 `_split_md_by_heading()` 逻辑）
   - **And** 第二级按句子边界切分（句号、换行），不在句中/词中硬切
   - **And** 使用 tiktoken（`cl100k_base`）做 token 计数，上限 512 tokens
   - **And** 旧 `_chunk_text()` 的 500 字符硬切逻辑被完全替换

3. **AC-3: 原子保护（代码块/数学公式/表格不切断）**
   - **Given** 笔记中包含代码块（``` ... ```）、数学公式（`$$...$$`）、表格（`|...|`）
   - **When** 分块算法遇到这些原子单元
   - **Then** 整块保护不切断——即使超过 512 token 也作为独立 chunk 保留
   - **And** 原子单元前后的文本正常按句子边界切分

4. **AC-4: 面包屑路径前缀**
   - **Given** 笔记有多级标题结构（H1 > H2 > H3）
   - **When** 每个 chunk 生成时
   - **Then** chunk 内容前缀注入面包屑路径：`"文档：{filename} > {h1} > {h2} > {h3}\n\n{原始chunk}"`
   - **And** 面包屑路径在 embedding 时一起编码（提升 chunk 的上下文感知）
   - **And** `metadata_json` 中保留原始 `heading_path` 数组供检索结果展示

5. **AC-5: index_single_file 路径 bug 修复**
   - **Given** `lancedb_client.py:595` 的 `index_single_file` 方法
   - **When** 索引单个文件
   - **Then** `rel_path` 使用 `os.path.relpath(file_path, vault_path)` 而非 `os.path.basename(file_path)`
   - **And** 文件路径信息不再丢失目录结构

6. **AC-6: 全量重建索引后搜索质量可感知提升**
   - **Given** bge-m3 + 新分块策略全部生效
   - **When** 执行全量重建索引
   - **Then** LanceDB `vault_notes` 表使用新 schema（1024d 向量 + heading_path 元数据）
   - **And** 旧 384d 索引数据完全清除后重建
   - **And** 搜索结果中 chunk 内容可读性显著提升（不再出现切断的词/句）

7. **AC-7: 配置兼容性**
   - **Given** 环境变量和配置文件
   - **When** 系统启动
   - **Then** `LANCEDB_EMBEDDING_MODEL` 默认值更新为 `BAAI/bge-m3`
   - **And** `LANCEDB_EMBEDDING_DIM` 默认值更新为 `1024`
   - **And** `SUPPORTED_MODELS` / `EMBEDDING_MODELS` 字典包含 bge-m3 条目
   - **And** `ruff check` lint 通过，无新增错误

## Tasks / Subtasks

- [ ] Task 1: bge-m3 模型加载替换 (AC: #1, #7)
  - [ ] 1.1 `requirements.txt` / `pyproject.toml` 新增 `FlagEmbedding>=1.2` 依赖
  - [ ] 1.2 `src/agentic_rag/processors/multimodal_vectorizer.py` — 替换 `SentenceTransformer` 为 `BGEM3FlagModel`（`from FlagEmbedding import BGEM3FlagModel`），修改 `initialize()` 方法的模型加载逻辑
  - [ ] 1.3 `src/agentic_rag/processors/multimodal_vectorizer.py` — 修改 `_encode_text()` 方法，使用 `model.encode()` 返回的 `dense_vecs`（1024d）
  - [ ] 1.4 `src/agentic_rag/processors/multimodal_vectorizer.py` — 修改 `DEFAULT_EMBEDDING_DIM` 从 384 → 1024，`model_name` 默认值改为 `BAAI/bge-m3`
  - [ ] 1.5 `src/agentic_rag/config.py` — `EMBEDDING_MODELS` 字典新增 `"BAAI/bge-m3": 1024` 条目，移除或标注旧模型为 deprecated
  - [ ] 1.6 `src/agentic_rag/config.py` — `LANCEDB_CONFIG` 默认值更新：`embedding_model` → `"BAAI/bge-m3"`，`embedding_dim` → `1024`
  - [ ] 1.7 `src/agentic_rag/clients/lancedb_client.py` — `DEFAULT_EMBEDDING_DIM` 从 384 → 1024，`SUPPORTED_MODELS` 新增 bge-m3 条目，构造函数默认 `embedding_model` 改为 `"BAAI/bge-m3"`
  - [ ] 1.8 `src/agentic_rag/clients/lancedb_client.py` — `CANVAS_NODES_SCHEMA`（`config.py:58-70`）注释更新维度说明 384/768 → 1024
  - [ ] 1.9 清理所有 hardcoded 384/768 维度引用（docstring、注释、schema 说明）

- [ ] Task 2: 重写分块算法 — 句子边界 + token 计数 (AC: #2)
  - [ ] 2.1 `requirements.txt` / `pyproject.toml` 新增 `tiktoken>=0.5` 依赖
  - [ ] 2.2 `src/agentic_rag/clients/lancedb_client.py` — 重写 `_chunk_text()` 函数：
    - 使用 `tiktoken.get_encoding("cl100k_base")` 做 token 计数
    - 按句子边界切分（中文句号`。`/英文句号`.`/换行`\n`）
    - 目标 512 tokens 上限，超长句子在子句处（逗号/分号）二次切分
    - overlap 按 token 计算（约 50 tokens）
  - [ ] 2.3 `src/agentic_rag/clients/lancedb_client.py` — `index_vault_notes()` 和 `index_single_file()` 的 `chunk_size` 参数语义从"字符数"改为"token 数"，默认值 500→512
  - [ ] 2.4 验证：一段中英混合文本分块后，每个 chunk 不超过 512 tokens，切分点不在词/句中间

- [ ] Task 3: 原子保护实现 (AC: #3)
  - [ ] 3.1 `src/agentic_rag/clients/lancedb_client.py` — 在新 `_chunk_text()` 中实现原子单元检测：
    - 代码块：正则匹配 ` ```...``` `（含语言标记）
    - 数学公式：正则匹配 `$$...$$`（块级公式）
    - 表格：正则匹配连续 `|...|` 行
  - [ ] 3.2 原子单元在分块前被标记，切分时绕过这些区域
  - [ ] 3.3 超过 512 token 的原子单元作为独立 chunk 保留（不切断）
  - [ ] 3.4 验证：包含代码块的笔记分块后，代码块完整保留在单个 chunk 中

- [ ] Task 4: 面包屑路径前缀 (AC: #4)
  - [ ] 4.1 `src/agentic_rag/clients/lancedb_client.py` — 修改 `_split_md_by_heading()` 追踪 heading 层级栈（`heading_stack: List[str]`），每遇到 heading 按级别（`#` 数量）更新栈
  - [ ] 4.2 `_flush_section()` 输出的 chunk dict 新增 `heading_path` 字段（`List[str]`），包含从根到当前 heading 的完整路径
  - [ ] 4.3 chunk `content` 前缀注入面包屑：`"文档：{filename} > {h1} > {h2}\n\n{原始content}"`
  - [ ] 4.4 `index_vault_notes()` 和 `index_single_file()` 的 `metadata_json` 中存储 `heading_path` 数组
  - [ ] 4.5 验证：一个有 3 级标题的笔记索引后，chunk 内容包含正确的面包屑前缀

- [ ] Task 5: 修复 index_single_file 路径 bug (AC: #5)
  - [ ] 5.1 `src/agentic_rag/clients/lancedb_client.py:595` — `rel_path = os.path.basename(file_path)` 改为 `rel_path = os.path.relpath(file_path, vault_path)`
  - [ ] 5.2 `index_single_file()` 方法签名新增 `vault_path` 参数（必选），用于计算相对路径
  - [ ] 5.3 检查所有调用 `index_single_file()` 的地方，确保传入 `vault_path` 参数

- [ ] Task 6: LanceDB Schema 升级 + 全量重建 (AC: #1, #6)
  - [ ] 6.1 `src/agentic_rag/clients/lancedb_client.py` — `_ensure_table()` 或 schema 定义中 `vector` 列维度从 384 → 1024
  - [ ] 6.2 全量重建索引时（`index_vault_notes()`）先 drop 旧表再创建新表（384d 和 1024d 不兼容）
  - [ ] 6.3 `index_vault_notes()` 方法在检测到向量维度不匹配时自动触发 drop+recreate
  - [ ] 6.4 验证：全量重建后，LanceDB 表中所有向量为 1024 维

- [ ] Task 7: 代码质量检查 (AC: #7)
  - [ ] 7.1 运行 `ruff check src/agentic_rag/clients/lancedb_client.py` — lint 通过
  - [ ] 7.2 运行 `ruff check src/agentic_rag/processors/multimodal_vectorizer.py` — lint 通过
  - [ ] 7.3 运行 `ruff check src/agentic_rag/config.py` — lint 通过
  - [ ] 7.4 运行 `python -c "from agentic_rag.state_graph import build_canvas_agentic_rag_graph; build_canvas_agentic_rag_graph()"` — StateGraph 编译通过
  - [ ] 7.5 运行 `python -m compileall src/agentic_rag/ -q` — 字节码编译通过

## Dev Notes

### 关键架构约束

- **bge-m3 本地运行**：通过 `FlagEmbedding` 库直接加载 bge-m3 模型（非 Ollama 容器），CPU 可跑，模型约 2.2GB。MVP 阶段仅启用 Dense 向量（1024d），Sparse 向量留 Story 2.4（中文搜索），ColBERT 留 Phase 2 评估
- **分块策略分工**：`_split_md_by_heading()` 负责一级切分（heading 感知，已验证有效保留不动），新 `_chunk_text()` 负责二级切分（句子边界 + token 计数 + 原子保护）
- **向量维度迁移**：384d → 1024d 不兼容，全量重建是硬性要求。索引重建期间搜索暂不可用
- **面包屑前缀**：Anthropic 官方验证可降低 35% 检索失败。前缀参与 embedding 编码，提升 chunk 上下文感知
- **index_single_file 路径 bug（PRD C8）**：`basename` 丢失目录路径导致搜索结果无法追溯到文件位置。修复后需新增 `vault_path` 参数

### 本 Story 只做 Dense 向量迁移

bge-m3 支持 Dense+Sparse+ColBERT 三合一，但本 Story 只迁移 Dense 向量（1024d）。原因：
- **Sparse 向量** 需要 LanceDB schema 新增 `sparse_vector` 列 + hybrid search 改造，属于 Story 2.4（中文搜索与混合检索）
- **ColBERT** 属于 Phase 2 评估项，当前不实施
- 本 Story 聚焦：模型替换 + 分块升级 + 面包屑 + 路径修复

### Source Tree Components

| 组件 | 路径 | 操作 |
|------|------|------|
| 分块+索引核心 | `src/agentic_rag/clients/lancedb_client.py` | 重写 `_chunk_text()`，修改 `_split_md_by_heading()` 加面包屑，修复 `index_single_file` 路径 bug，更新 schema 维度 |
| 向量化引擎 | `src/agentic_rag/processors/multimodal_vectorizer.py` | 替换 SentenceTransformer → BGEM3FlagModel，更新维度和模型名 |
| RAG 配置 | `src/agentic_rag/config.py` | 更新 EMBEDDING_MODELS、LANCEDB_CONFIG 默认值 |
| 依赖清单 | `requirements.txt` / `pyproject.toml` | 新增 FlagEmbedding>=1.2、tiktoken>=0.5 |

### 不可动的文件（活跃管道核心）

以下文件本 Story 不修改：
- `src/agentic_rag/state_graph.py` — StateGraph 编排
- `src/agentic_rag/nodes.py` — 管道节点实现（reranker/CRAG 留 Story 2.5/2.6）
- `src/agentic_rag/state.py` — State 类型定义

### 对下游 Story 的影响

| 下游 Story | 影响 |
|------------|------|
| 2.4 中文搜索与混合检索 | 依赖本 Story 的 bge-m3 模型加载。2.4 启用 Sparse 向量 + jieba 预分词 |
| 2.5 精排与融合升级 | 依赖本 Story 的 1024d 向量。2.5 升级 reranker + 分层 RRF |
| 2.7 文件指纹增量索引 | 依赖本 Story 的新分块算法。2.7 加 delete-before-insert 去重 |
| 2.12 全量重建验收 | 依赖本 Story 的所有改动。最终验收 Golden Test Set |

### Project Structure Notes

- `src/agentic_rag/clients/lancedb_client.py` 是分块+索引的核心文件，同时包含 `_chunk_text()`（模块级函数）和 `_split_md_by_heading()`（LanceDBClient 静态方法），所有分块改动集中在此
- `src/agentic_rag/processors/multimodal_vectorizer.py` 是向量化引擎，封装了模型加载和 batch 编码，bge-m3 模型替换集中在此
- `src/agentic_rag/config.py` 定义 RAG 配置常量和 `CanvasRAGConfig` TypedDict，维度和模型名更新在此
- 依赖文件位于项目根目录（`requirements.txt`）或 `backend/` 目录下

### References

- [Source: _bmad-output/brainstorming/brainstorming-session-P0-chunking-pipeline-2026-03-11.md#主题1-分块策略] — 分块升级方案：heading split + 句子边界 + 原子保护 + 面包屑传播
- [Source: _bmad-output/brainstorming/brainstorming-session-P0-chunking-pipeline-2026-03-11.md#主题2-bge-m3] — bge-m3 三阶段迁移方案，本 Story 实施阶段 1（Dense 1024d）
- [Source: _bmad-output/brainstorming/brainstorming-session-P0-chunking-pipeline-2026-03-11.md#主题3-Contextual-Retrieval] — 面包屑前缀方案（Rule-based Heading Path Prefix，Phase 1 零 LLM 成本）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase-1] — Phase 1 任务 1.1-1.3（bge-m3 迁移、分块重写、面包屑前缀+索引路径修复）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#CRITICAL级] — C8 index_single_file 路径 bug（basename → relpath）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#HIGH级] — H2 500字符硬切不保护代码/公式
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.3] — Story 原始定义和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#已确定的技术基础] — bge-m3（Ollama 容器/FlagEmbedding，1024d Dense+Sparse MVP）
- [Source: Firecrawl 2026 Benchmark] — Recursive + 结构感知分块排名第一（69% 准确率，85-90% 召回率）
- [Source: Anthropic Contextual Retrieval 论文] — 检索失败减少 49%，+reranking 后 67%
- [Source: bge-m3 BAAI 官方 benchmark] — 中文 MIRACL nDCG@10=63.9

## Dev Agent Record

### Agent Model Used

(to be filled during implementation)

### Debug Log References

### Completion Notes List

### Change Statistics (Expected)

| 类别 | 行数 |
|------|------|
| 重写（_chunk_text 函数） | 约 80 行 |
| 修改（_split_md_by_heading 面包屑） | 约 20 行 |
| 修改（multimodal_vectorizer.py 模型替换） | 约 30 行 |
| 修改（config.py 配置更新） | 约 10 行 |
| 修改（lancedb_client.py schema+路径修复） | 约 20 行 |
| 新增依赖 | FlagEmbedding>=1.2, tiktoken>=0.5 |
| **净变化** | **约 +100 行（重写+新增），-80 行（旧代码替换）** |

### File List
