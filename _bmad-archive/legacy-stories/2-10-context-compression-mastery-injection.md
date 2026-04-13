# Story 2.10: Phase 2 — 上下文压缩与掌握度注入

Status: ready-for-dev

## Story

As a 用户,
I want AI 对话时自动检索相关上下文并精炼注入，Agent 知道我的掌握水平,
so that AI 回答既精准又不浪费 token，难度适配我的水平。

## Acceptance Criteria

1. **AC-1: 上下文压缩 15K→3K token**
   - **Given** 检索管道返回 15K+ token 的候选上下文（精排后的 top-k 文档）
   - **When** 上下文压缩管道执行
   - **Then** 压缩到 3K token 以内（句子级提取，保留最相关的句子）
   - **And** 公式块、代码块整块保护不被截断（原子保护）
   - **And** 表格整行保护不被截断
   - **And** 压缩算法：基于 query 相关度对每个句子打分，保留分数最高的句子直到达到 3K token 上限
   - **And** 压缩前后的 token 数记录日志

2. **AC-2: 掌握度信息注入 prompt 前端位置**
   - **Given** 用户对当前节点有掌握度数据（BKT p_mastery + FSRS 记忆稳定性）
   - **When** 构建 LLM prompt
   - **Then** 掌握度信息注入 prompt 最前端位置（第 1-2 行），利用 Lost in Middle 效应（LLM 更关注 prompt 首尾）
   - **And** 注入格式：`[学习者水平] 该知识点掌握度: {level}（{description}）。请据此调整解释深度和详细程度。`
   - **And** 掌握度级别映射：未学习(默认) / 学习中 / 薄弱 / 掌握 / 待复习
   - **And** 无掌握度数据时不注入（不影响 prompt 正常工作）

3. **AC-3: Graphiti 学习记忆增强**
   - **Given** 用户在该节点有学习记忆（Tips、错误记录、关键问答）
   - **When** 检索上下文构建
   - **Then** 从 Graphiti 检索相关学习记忆（通过 search_memories MCP 工具或直接 API）
   - **And** 学习记忆注入 prompt（在掌握度之后、笔记上下文之前）
   - **And** 注入格式区分类型：`[历史 Tips] ...`、`[历史错误] ...`、`[相关问答] ...`
   - **And** 学习记忆总量限制在 1K token 内（超出时按时间排序取最近的）

4. **AC-4: 回源文件验证（Staleness Check）**
   - **Given** 检索返回的文档片段可能已过期（源文件被修改但索引未更新）
   - **When** 上下文压缩前执行验证
   - **Then** 通过 content_hash 比对检测过期片段（片段的 content_hash 与当前文件 hash 不匹配）
   - **And** 过期片段标记为 stale，降低其在压缩中的优先级（但不完全丢弃）
   - **And** 对非 stale 的片段执行 Context Expansion：扩展到完整段落（前后各扩展 1-2 个句子）
   - **And** stale 检测不阻塞搜索流程（失败时跳过验证）

5. **AC-5: 查询改写——Multi-Query + Decomposition**
   - **Given** 用户提出复杂查询（包含多个子问题或隐含多个搜索意图）
   - **When** 查询进入检索管道
   - **Then** Multi-Query 改写：LLM 生成 2-3 个不同角度的等价查询，分别搜索后合并结果
   - **And** Decomposition 改写：复杂查询拆分为 2-3 个子问题，分别搜索后组合结果
   - **And** 改写策略根据查询复杂度自动选择（简单查询不改写、中等用 Multi-Query、复杂用 Decomposition）
   - **And** 改写通过 LiteLLM SDK 调用，model 从 config 读取
   - **And** 改写有超时保护（3 秒），超时 fallback 为原始查询直接搜索

## Tasks / Subtasks

- [ ] **Task 1: 上下文压缩实现** (AC: #1)
  - [ ] 1.1 新增 `src/agentic_rag/compression.py` 模块，实现 `compress_context(query: str, documents: List[SearchResult], max_tokens: int = 3000) -> str` 函数
  - [ ] 1.2 句子级提取算法：
    - 将每个文档拆分为句子（按中文句号/英文句号/换行符分割）
    - 保护原子块：识别 `` ```...``` ``（代码块）、`$...$` / `$$...$$`（公式块）、表格（`|...|`）为不可拆分单元
    - 使用 bge-m3 或 TF-IDF 计算每个句子与 query 的相关度分数
    - 按分数降序排列，依次添加直到达到 max_tokens
  - [ ] 1.3 token 计算：使用 `tiktoken`（GPT tokenizer）或简单字符/词估算（1 token ≈ 4 字符 EN / 1.5 字符 CN）
  - [ ] 1.4 添加日志：`[COMPRESS] {input_tokens} tokens → {output_tokens} tokens ({ratio:.0%} compression), {protected_blocks} blocks protected`
  - [ ] 1.5 在 LangGraph 管道中新增 `compress_context` 节点（在 `check_quality` 之后、最终输出之前）

- [ ] **Task 2: 掌握度注入** (AC: #2)
  - [ ] 2.1 新增 `_build_mastery_prefix(node_id: str) -> str` 函数：查询 BKT/FSRS 数据，构建掌握度描述
  - [ ] 2.2 掌握度级别映射逻辑：
    - p_mastery >= 0.8 且 R >= 0.8 → "掌握"
    - p_mastery >= 0.5 → "学习中"
    - p_mastery < 0.5 且有考察记录 → "薄弱"
    - FSRS 提示需复习 → "待复习"
    - 无数据 → 不注入
  - [ ] 2.3 在 prompt 构建时将掌握度信息放在最前端位置（`system_prompt` 的第 1-2 行）
  - [ ] 2.4 注入格式示例：`[学习者水平] 该知识点掌握度: 薄弱（建议从基础概念开始解释，多举例子）。`
  - [ ] 2.5 掌握度查询通过 MCP 工具（`query_mastery`）或直接后端 API 调用

- [ ] **Task 3: Graphiti 学习记忆注入** (AC: #3)
  - [ ] 3.1 新增 `_retrieve_learning_memories(node_id: str, max_tokens: int = 1000) -> str` 函数
  - [ ] 3.2 从 Graphiti 检索该节点相关的 Tips、错误记录、关键问答（使用 graphiti_core SDK `search` API）
  - [ ] 3.3 按类型格式化：
    - `[历史 Tips] 1. ... 2. ...`
    - `[历史错误] 类型: 知识点缺失 — 描述: ...`
    - `[相关问答] Q: ... A(摘要): ...`
  - [ ] 3.4 总量控制：超过 1K token 时按创建时间排序取最近的
  - [ ] 3.5 Graphiti 不可用时跳过记忆注入（降级为无记忆增强），记录 warning 日志

- [ ] **Task 4: 回源文件验证** (AC: #4)
  - [ ] 4.1 新增 `_staleness_check(results: List[SearchResult]) -> List[SearchResult]` 函数
  - [ ] 4.2 对每个结果的 `canvas_file`，读取当前文件的 content_hash（复用 Story 2.7 的 fingerprint 表）
  - [ ] 4.3 与索引时存储的 content_hash 比对：匹配 → fresh，不匹配 → stale
  - [ ] 4.4 stale 片段在 SearchResult 中标记 `stale: True`，压缩时降低优先级（分数乘以 0.5）
  - [ ] 4.5 fresh 片段执行 Context Expansion：根据 `line_start`/`line_end` 从源文件读取前后各 2 行，扩展上下文
  - [ ] 4.6 staleness_check 失败时（文件不存在/读取异常）跳过验证，不阻塞搜索

- [ ] **Task 5: Multi-Query + Decomposition 查询改写** (AC: #5)
  - [ ] 5.1 新增 `_multi_query_rewrite(query: str) -> List[str]` 函数：通过 LLM 生成 2-3 个等价查询
  - [ ] 5.2 新增 `_decompose_query(query: str) -> List[str]` 函数：通过 LLM 将复杂查询拆分为子问题
  - [ ] 5.3 查询复杂度判断：简单（< 20 字符 + 无连接词）→ 不改写，中等 → Multi-Query，复杂（含"和"/"以及"/"如何...同时..."）→ Decomposition
  - [ ] 5.4 改写后的多个查询分别执行搜索，结果合并去重（按 doc_id 去重，保留最高分）
  - [ ] 5.5 改写超时保护：`asyncio.wait_for(timeout=3.0)`，超时 fallback 原始查询
  - [ ] 5.6 在 LangGraph 管道中集成：在 `fan_out_retrieval` 之前执行改写

- [ ] **Task 6: 管道集成与 State 扩展** (AC: #1-#5)
  - [ ] 6.1 在 `src/agentic_rag/state.py` 的 `CanvasRAGState` 中新增字段：
    - `compressed_context: str` — 压缩后的上下文文本
    - `mastery_prefix: str` — 掌握度注入的文本
    - `learning_memories: str` — Graphiti 学习记忆文本
    - `stale_count: int` — 过期片段数量
    - `multi_queries: List[str]` — 改写后的查询列表
  - [ ] 6.2 更新 `src/agentic_rag/config.py`，新增配置：
    - `context_max_tokens: int`（默认 3000）
    - `mastery_injection_enabled: bool`（默认 True）
    - `learning_memory_max_tokens: int`（默认 1000）
    - `staleness_check_enabled: bool`（默认 True）
    - `multi_query_enabled: bool`（默认 True）
  - [ ] 6.3 确保所有新字段有合理默认值

- [ ] **Task 7: 端到端验证** (AC: #1-#5)
  - [ ] 7.1 准备测试场景：
    - 15K token 候选上下文 → 压缩到 3K → 公式/代码块完整保留
    - 有掌握度数据的节点 → prompt 前端出现掌握度描述
    - 无掌握度数据的节点 → prompt 无掌握度信息（不报错）
    - 有 Graphiti 记忆的节点 → prompt 中出现历史 Tips/错误
    - 复杂查询 → 自动拆分为子问题分别搜索
  - [ ] 7.2 staleness check 验证：修改文件后搜索旧索引内容，标记 stale
  - [ ] 7.3 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 7.4 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 7.5 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，上下文压缩和掌握度注入为全新功能模块。现有管道在精排后直接输出结果，不做压缩或掌握度注入。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/nodes.py` | 精排后直接输出，无压缩逻辑 | **新增 compress_context 节点调用** |
| `src/agentic_rag/state_graph.py` | LangGraph 图无压缩节点 | **新增压缩节点到图中（check_quality → compress → END）** |
| `src/agentic_rag/state.py` | 无压缩/掌握度相关字段 | **新增 compressed_context / mastery_prefix 等字段** |
| `src/agentic_rag/config.py` | 无压缩/掌握度配置 | **新增相关配置项** |
| 新建 `src/agentic_rag/compression.py` | 不存在 | **新建：上下文压缩模块** |
| 新建 `src/agentic_rag/mastery_injection.py` | 不存在 | **新建：掌握度注入模块** |

#### 上下文压缩设计（来自后端 PRD A2）

后端 PRD Phase 2 任务 2.7 确认：**上下文压缩 15K→3K**
- 句子级提取（非摘要生成），保证事实忠实度
- 公式/代码/表格整块保护（与分块策略一致的原子保护）
- Lost in Middle 效应缓解：掌握度注入 prompt 前端位置（Anthropic + Google 论文验证）

#### 查询改写设计（来自后端 PRD A2）

后端 PRD Phase 2 任务 2.9 确认：**Multi-Query + Decomposition**
- Multi-Query：同一意图多角度改写，提高召回率
- Decomposition：复杂查询拆分，避免单次搜索遗漏
- 两种策略根据查询复杂度自动选择（不需用户干预）

### 依赖关系

- **前置 Story 2.5**（精排与融合升级）：压缩基于精排后的结果
- **前置 Story 2.6**（CRAG 质量门控）：压缩在质量检查之后执行
- **前置 Story 2.7**（文件指纹增量索引）：staleness check 复用 fingerprint 表
- **依赖 Epic 5**（精通度系统）：掌握度注入需要 BKT/FSRS 数据源。如 Epic 5 未完成，掌握度注入降级为空操作
- **后续 Story 2.11**（参数可配置化）：压缩/注入参数纳入配置体系

### 技术决策

1. **句子级提取 vs 摘要生成**：使用句子级提取（非 LLM 摘要），保证事实忠实度，不引入额外幻觉风险。
2. **掌握度注入位置**：prompt 最前端（Lost in Middle 效应），而非末尾。
3. **Graphiti 记忆容量**：限制 1K token，防止记忆信息淹没笔记上下文。
4. **staleness check**：非阻塞（失败跳过），不影响搜索主流程。
5. **Multi-Query 时机**：在 fan_out_retrieval 之前，改写后的查询分别走完整的 6 路搜索。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| 精排节点（上游） | `src/agentic_rag/nodes.py`（`rerank_results`） |
| 质量检查（上游） | `src/agentic_rag/nodes.py`（`check_quality`） |
| 图构建 | `src/agentic_rag/state_graph.py`（`build_canvas_agentic_rag_graph`） |
| State 定义 | `src/agentic_rag/state.py`（`CanvasRAGState`） |
| 配置 | `src/agentic_rag/config.py`（`CanvasRAGConfig`） |
| 文件指纹表（staleness） | `src/agentic_rag/clients/lancedb_client.py`（fingerprint 表） |

### 不做的事项（防蔓延 DD-10）

- 不修改精排或融合逻辑（Story 2.5 已完成）
- 不修改 CRAG 质量门控（Story 2.6 已完成）
- 不实现前端掌握度展示（Epic 5 的范围）
- 不实现 Graphiti 记忆写入（Epic 3 的范围，本 Story 只做读取）
- 不实现 LLM 摘要压缩（只做句子级提取）
- 不修改 embedding 模型

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-RET-02 | AC-1, AC-3 | AI 对话时自动检索相关上下文 |
| FR-RET-03 | AC-3 | 利用 Graphiti 学习记忆增强回答质量 |
| FR-RET-06 | AC-4 | 回源文件验证（Staleness Check + Context Expansion） |
| FR-RET-12 | AC-1, AC-2 | 上下文压缩 + 掌握度注入 prompt 前端位置 |
| FR-QA-P-04 | AC-1 | 上下文压缩到 3K token |
| FR-QA-P-05 | AC-2 | 掌握度信息注入 prompt 前端 |

### Project Structure Notes

- 本 Story 新建 2 个模块（`compression.py`、`mastery_injection.py`），修改 4 个文件
- 新增 LangGraph 节点需要修改图构建逻辑（`state_graph.py`），注意保持图结构的向后兼容
- 掌握度数据源依赖 Epic 5 的后端 API，如未就绪需要降级处理
- Graphiti 数据源依赖 Neo4j 和 graphiti_core，连接失败时降级

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 2] — 任务 2.7/2.8/2.9 上下文压缩、掌握度注入、查询改写
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#能力域 3：质量保障] — FR-QA-P-04/05 定义
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.10] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — 上下文压缩 + Lost in Middle 效应 + Graphiti 个人记忆引擎
- [Source: _bmad-output/planning-artifacts/prd.md] — FR-RET-02/03/06/12 定义
- [Source: src/agentic_rag/nodes.py] — 精排和质量检查节点
- [Source: src/agentic_rag/state_graph.py] — LangGraph 图构建

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
