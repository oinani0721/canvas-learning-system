# Story 2.2: Phase 0 — 搜索通道修复与激活

Status: ready-for-dev

## Story

As a 用户,
I want 6 条搜索通道全部返回真实数据，精排和质量检查开始工作，
so that AI 对话能搜到我笔记中的相关内容。

## Acceptance Criteria

1. **AC-1: 6/6 搜索通道返回真实数据**
   - **Given** 后端管道启动（Story 2.1 已完成死代码清理和配置修复）
   - **When** 执行一次完整的搜索查询
   - **Then** 6 条搜索通道（Dense + Sparse + Graphiti + Vault + CLI + 图片）均返回数据（或因数据不存在返回空但通道本身可达）
   - **And** 每条通道的搜索结果格式统一为 `SearchResult`（doc_id + content + score + metadata）
   - **And** 单通道故障不影响其他通道（asyncio.gather return_exceptions=True）

2. **AC-2: Reranker 接入 bge-reranker（非空壳）**
   - **Given** 融合后的搜索结果列表
   - **When** rerank_results 节点执行
   - **Then** 调用 bge-reranker-v2-m3（或 bge-reranker-base 作为 Phase 0 起步选项）实际计算 Cross-Encoder 分数
   - **And** 返回结果的 `score` 字段为 reranker 真实分数（非原始 RRF 分数直传）
   - **And** 结果按 reranker 分数降序排列
   - **And** `_rerank_local` 不再是 `return results` 空壳

3. **AC-3: CRAG 健康触发率 15-30%（非 100% 误触发）**
   - **Given** reranker 返回带有真实分数的结果
   - **When** check_quality 节点执行质量评估
   - **Then** 使用 reranker 分数（范围约 0-1）进行质量判断，而非 RRF 分数（max 约 0.098）
   - **And** 质量阈值与分数域匹配（reranker 分数域下 threshold 合理，如 0.5-0.7）
   - **And** 在真实查询上，"low" 质量触发率在 15-30% 范围（非 100%）
   - **And** 重写循环最多 2 次后强制结束

4. **AC-4: 查询改写接入 LLM（非 f-string 占位）**
   - **Given** check_quality 判定为 "low" 触发查询改写
   - **When** rewrite_query 节点执行
   - **Then** 通过 LiteLLM 调用 LLM 进行真正的查询改写（非 `f"请详细解释:{query}"`）
   - **And** 改写后的查询语义有变化（不同角度/关键词提取/问题分解）
   - **And** 改写操作有超时保护（3s），超时则使用原始查询继续

5. **AC-5: SearchResult 格式统一，搜索结果不重复**
   - **Given** 6 条搜索通道返回各自结果
   - **When** 结果进入融合阶段
   - **Then** 所有通道的结果都严格遵循 `SearchResult` TypedDict 格式（doc_id, content, score, metadata）
   - **And** metadata 中必须包含 `source` 字段标注来源通道
   - **And** 融合时使用 doc_id 去重（同一文档多通道命中只保留最高分）
   - **And** Vault 笔记搜索结果不与 LanceDB Dense 结果重复

6. **AC-6: Graphiti 搜索通道使用 graphiti_core SDK（非 MCP import）**
   - **Given** Graphiti 搜索通道（retrieve_graphiti 节点）
   - **When** 执行搜索
   - **Then** 使用 graphiti_core SDK 直接调用（方案 C 内嵌 graphiti_core，见架构文档）
   - **And** 不再依赖 `from mcp__graphiti_memory__search_nodes import search_nodes`（该 import 在非 Claude Code 环境 100% 失败）
   - **And** 搜索通过 Neo4j 图遍历或 graphiti_core 的 search API 执行
   - **And** 结果转换为 SearchResult 格式

## Tasks / Subtasks

- [ ] **Task 1: Reranker 激活——替换 `_rerank_local` 空壳** (AC: #2)
  - [ ] 1.1 在 `src/agentic_rag/nodes.py` 的 `_rerank_local` 函数中，替换 `return results` 为实际调用 `reranking.py` 中已实现的 `LocalReranker.rerank_search_results()`
  - [ ] 1.2 提取查询文本：从 `state["messages"]` 获取最后一条用户消息作为 reranker 的 query 参数
  - [ ] 1.3 实例化 `LocalReranker`（bge-reranker-base 起步，Phase 1 Story 2.5 再升级为 bge-reranker-v2-m3 fp16）：使用懒加载单例模式，避免每次调用重新加载模型
  - [ ] 1.4 将 `reranking.py` 中的 `LocalReranker` 输出映射回 `SearchResult` 格式（已有 `rerank_search_results` 方法）
  - [ ] 1.5 添加降级保护：如果 `sentence-transformers` 未安装（`CROSS_ENCODER_AVAILABLE=False`），log warning 并 fallback 为原始排序
  - [ ] 1.6 同步修改 `_rerank_cohere` 占位函数：调用 `reranking.py` 中已实现的 `CohereReranker.rerank_search_results()`，添加同样的降级保护

- [ ] **Task 2: CRAG 质量评估修复——分数域匹配** (AC: #3)
  - [ ] 2.1 在 `src/agentic_rag/nodes.py` 的 `check_quality` 函数中，确认输入来自 `reranked_results`（reranker 真实分数，范围 0-1），而非 `fused_results`（RRF 分数，max ~0.098）
  - [ ] 2.2 验证 `quality_threshold` 配置值与 reranker 分数域匹配：默认 0.7 适用于 reranker 分数（0-1 范围），保持不变
  - [ ] 2.3 如果 reranker 降级（返回原始 RRF 分数），则动态调低阈值（如 0.05），避免 100% 误判
  - [ ] 2.4 添加日志：记录 top-3 分数值和最终 quality_grade，便于调试触发率
  - [ ] 2.5 在 `route_after_quality_check` 中添加 `medium` 质量时不触发重写（只有 `low` 才触发），确认当前逻辑正确

- [ ] **Task 3: 查询改写接入 LLM** (AC: #4)
  - [ ] 3.1 在 `src/agentic_rag/state_graph.py` 的 `rewrite_query` 函数中，替换 `f"请详细解释: {original_query}"` 为 LLM 调用
  - [ ] 3.2 使用 LiteLLM SDK 调用配置的 LLM（`litellm.acompletion()`），prompt 设计为：
    ```
    你是搜索查询优化专家。请将以下查询改写为更精确的搜索查询，以获得更相关的检索结果。
    原始查询：{original_query}
    请用不同的关键词和角度重写，直接返回改写后的查询，不要解释。
    ```
  - [ ] 3.3 添加 3 秒超时保护（`asyncio.wait_for`），超时则使用拼接策略作为 fallback：`f"{original_query} 关键概念 定义 解释"`
  - [ ] 3.4 LLM 不可用时的降级策略：使用关键词提取（jieba 分词 + 取 top-5 关键词拼接）或简单同义词扩展
  - [ ] 3.5 记录改写前后的查询到日志，便于后续分析改写质量

- [ ] **Task 4: Graphiti 搜索通道修复——替换 MCP import 为 graphiti_core SDK** (AC: #6)
  - [ ] 4.1 重写 `src/agentic_rag/clients/graphiti_client.py` 中的 `GraphitiClient._search_via_mcp` 方法，替换为 graphiti_core SDK 调用
  - [ ] 4.2 使用 `graphiti_core` 的 `Graphiti` 类初始化（连接 Neo4j `bolt://localhost:7689`），参考架构文档方案 C 内嵌 graphiti_core
  - [ ] 4.3 调用 `graphiti.search(query, ...)` 或等效 API 执行搜索，返回节点和事实
  - [ ] 4.4 保持 `_convert_to_search_results` 转换逻辑不变，确保输出为标准 `SearchResult` 格式
  - [ ] 4.5 如果 graphiti_core 不可用或 Neo4j 不可达，降级返回空结果（保持现有 `enable_fallback` 行为）
  - [ ] 4.6 删除所有 `from mcp__graphiti_memory__search_nodes import search_nodes` 等不可能成功的 MCP import 语句
  - [ ] 4.7 更新 `initialize()` 方法：检测 graphiti_core 可用性（而非 MCP 模块），设置 `_graphiti_available` 标志

- [ ] **Task 5: SearchResult 格式统一与去重** (AC: #5)
  - [ ] 5.1 审查所有 6 个 retriever 的输出格式，确保都返回标准 `SearchResult`（doc_id, content, score, metadata with source）：
    - `retrieve_graphiti` → metadata.source = "graphiti"
    - `retrieve_lancedb` → metadata.source = "lancedb_dense" 或 "lancedb_sparse"
    - `retrieve_multimodal` → metadata.source = "multimodal"
    - `retrieve_textbook` → metadata.source = "textbook"
    - `retrieve_cross_canvas` → metadata.source = "cross_canvas"
    - `retrieve_vault_notes` → metadata.source = "vault_notes"
  - [ ] 5.2 在 `fuse_results` 的 RRF 融合中增加基于 `doc_id` 的去重逻辑：同一文档多通道命中时，RRF 分数累加（已有）但确保不产生重复条目
  - [ ] 5.3 对 vault_notes 和 lancedb 通道的结果做 content 指纹去重（相同文件+相同分块内容 = 同一文档），防止同一笔记片段出现两次
  - [ ] 5.4 验证 `SearchResult` TypedDict 各字段在所有通道中均有值（doc_id 不为空、content 不为空、score 在合理范围）

- [ ] **Task 6: 搜索通道健康检查与容错** (AC: #1)
  - [ ] 6.1 确认 `fan_out_retrieval` 中的 6 个 Send 对象全部正确指向各自的 retriever 节点
  - [ ] 6.2 确认每个 retriever 节点都有 `try/except` 包装，异常时返回空结果而非抛出异常（已有，验证即可）
  - [ ] 6.3 确认 LangGraph 的 `RetryPolicy` 配置合理（max_attempts=2-3, backoff_factor=1.5-2.0）
  - [ ] 6.4 添加通道健康状态日志：每次搜索完成后，记录各通道返回结果数和延迟，便于诊断通道故障
  - [ ] 6.5 验证 `fuse_results` 在部分通道返回空列表时能正常工作（不报 KeyError/IndexError）

- [ ] **Task 7: 消除笔记重复搜索（S2-T5）** (AC: #5)
  - [ ] 7.1 定位 vault_notes_retriever 和 lancedb_client 的搜索范围是否存在重叠（两者都搜索 .md 文件内容）
  - [ ] 7.2 方案 A：vault_notes_retriever 使用 Obsidian CLI（file-level 搜索），lancedb 使用向量搜索（chunk-level 搜索），确保搜索粒度不同
  - [ ] 7.3 方案 B：如果两者搜索相同粒度内容，在 fuse_results 中用 `file_path + chunk_offset` 作为去重 key
  - [ ] 7.4 实施去重后验证：同一查询不再出现内容完全相同的两条结果

- [ ] **Task 8: 端到端验证** (AC: #1-#6)
  - [ ] 8.1 准备 5 个测试查询（含中英文），逐个执行管道，验证：
    - 6 通道均被调用（检查日志）
    - reranker 输出分数在 0-1 范围（非 0.01-0.09）
    - CRAG 不是 100% 触发 low（至少有 1 个查询为 medium/high）
    - 查询改写输出不是 `f"请详细解释:{query}"`
    - 无重复结果
  - [ ] 8.2 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 8.3 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 8.4 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，核心管道框架已存在但严重损坏。以下是各文件的当前状态和修复方案：

#### 关键文件清单

| 文件 | 当前状态 | 修复内容 |
|------|---------|---------|
| `src/agentic_rag/nodes.py` | `_rerank_local` / `_rerank_cohere` 均为空壳 `return results` (CRITICAL C2) | 接入 `reranking.py` 中已实现的 `LocalReranker` |
| `src/agentic_rag/nodes.py` | `check_quality` 使用 RRF 分数(max 0.098) vs 阈值 0.7 → 100% 误判 low (CRITICAL C3) | reranker 激活后分数域自动匹配 |
| `src/agentic_rag/state_graph.py` | `rewrite_query` = `f"请详细解释:{query}"` (CRITICAL C4) | 接入 LiteLLM 调用 LLM |
| `src/agentic_rag/clients/graphiti_client.py` | 100% 依赖 MCP import，非 Claude Code 环境全部失败 (CRITICAL C5) | 替换为 graphiti_core SDK |
| `src/agentic_rag/reranking.py` | `LocalReranker` / `CohereReranker` / `HybridReranker` 已完整实现，但 nodes.py 未调用 | **可直接复用**（质量评级：可复用） |
| `src/agentic_rag/state.py` | `SearchResult` TypedDict 和 `CanvasRAGState` 定义完整 | **无需修改** |
| `src/agentic_rag/state_graph.py` | LangGraph 图构建完整（6 路并行 + 融合 + rerank + 质量循环） | 图结构无需修改，只需修复节点实现 |

#### 六路搜索通道状态

| # | 通道 | 节点名 | 当前状态 | 本 Story 修复 |
|---|------|--------|---------|--------------|
| 1 | LanceDB Dense 向量搜索 | `retrieve_lancedb` | 可工作（依赖 LanceDB 连接） | 验证格式 |
| 2 | LanceDB Sparse 关键词搜索 | `retrieve_lancedb` | 待 Phase 1 jieba 激活 | 验证格式 |
| 3 | Graphiti 知识图谱搜索 | `retrieve_graphiti` | CRITICAL C5: MCP import 失败 | **重写为 graphiti_core SDK** |
| 4 | Vault 笔记搜索 | `retrieve_vault_notes` | 取决于 retriever 实现 | 验证格式，去重 |
| 5 | Obsidian CLI 图遍历 | `retrieve_cross_canvas` | 取决于 retriever 实现 | 验证格式 |
| 6 | 图片搜索 | `retrieve_multimodal` | 取决于 retriever 实现 | 验证格式 |

### 依赖关系

- **前置 Story 2.1**（已清理死代码、修复 config L195、删除 env_config.py、清理 cs188 硬编码）必须先完成
- **后续 Story 2.3**（bge-m3 迁移）会替换 embedding 模型，但不影响本 Story 的 reranker 接入
- **后续 Story 2.5**（精排升级）会将 bge-reranker-base 升级为 bge-reranker-v2-m3 fp16

### 技术决策

1. **Reranker 选型**：Phase 0 使用 bge-reranker-base（102M，已在 reranking.py 中实现），Phase 1 Story 2.5 再升级为 bge-reranker-v2-m3（568M，fp16）。理由：Phase 0 目标是"让管道工作"，不是"让管道最优"。
2. **Graphiti 客户端**：替换 MCP import 为 graphiti_core SDK 直接调用。架构文档确认使用方案 C（内嵌 graphiti_core），Neo4j 端点为 `bolt://localhost:7689`。
3. **查询改写**：使用 LiteLLM SDK 统一调用层（不锁定厂商），prompt 简洁聚焦于改写而非解释。
4. **CRAG 修复**：不修改阈值算法，而是通过激活 reranker 使分数域匹配阈值（根因修复而非症状修复）。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| Reranker 空壳 | `src/agentic_rag/nodes.py` L673-696（`_rerank_local` / `_rerank_cohere`） |
| Reranker 实现 | `src/agentic_rag/reranking.py`（`LocalReranker` / `CohereReranker` / `HybridReranker`） |
| CRAG 质量检查 | `src/agentic_rag/nodes.py` L703-754（`check_quality`） |
| 查询改写占位 | `src/agentic_rag/state_graph.py` L146-188（`rewrite_query`） |
| Graphiti MOCK 客户端 | `src/agentic_rag/clients/graphiti_client.py` L367-430（`_search_via_mcp`） |
| SearchResult 类型 | `src/agentic_rag/state.py` L43-51 |
| 图构建 | `src/agentic_rag/state_graph.py` L205-371（`build_canvas_agentic_rag_graph`） |
| Config | `src/agentic_rag/config.py` |
| Retrievers | `src/agentic_rag/retrievers/` |

### 不做的事项（防蔓延 DD-10）

- 不升级 embedding 模型（Story 2.3 的范围）
- 不修改分块策略（Story 2.3 的范围）
- 不实现分层 RRF 融合（Story 2.5 的范围，当前 RRF 可工作）
- 不实现 Adaptive-k 动态截取（Story 2.5 的范围）
- 不实现中文 jieba 分词（Story 2.4 的范围）
- 不实现上下文压缩（Story 2.10 的范围）
- 不实现文件指纹增量索引（Story 2.7 的范围）
- 不修改前端代码（纯后端管道修复）
- 不修改 LangGraph 图结构（只修复节点实现）

### Project Structure Notes

- 本 Story 修改范围限于 `src/agentic_rag/` 目录，不涉及 `backend/app/` 目录（后者的 GraphitiEdgeClient 是独立的 Edge 同步客户端，不是搜索通道）
- `src/agentic_rag/reranking.py` 已有完整的 reranker 实现，本 Story 的核心工作是把它接入 `nodes.py`
- `src/agentic_rag/state.py` 中的 `SearchResult` 是所有通道的统一格式，不需要修改
- 新增的 graphiti_core 依赖需要确认 `requirements.txt` 或 `pyproject.toml` 中已包含

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#代码审查发现汇总] — CRITICAL C2/C3/C4/C5 问题定义
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 0] — 任务 0.5-0.9 定义
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#六路物理通道] — 六路搜索通道架构
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Context Analysis] — graphiti_core 方案 C 内嵌
- [Source: src/agentic_rag/nodes.py] — 核心节点实现（含 reranker 空壳）
- [Source: src/agentic_rag/state_graph.py] — 图构建 + 查询改写占位
- [Source: src/agentic_rag/reranking.py] — 已实现的 reranker（可复用）
- [Source: src/agentic_rag/clients/graphiti_client.py] — Graphiti MOCK 客户端
- [Source: src/agentic_rag/state.py] — SearchResult TypedDict 定义

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
