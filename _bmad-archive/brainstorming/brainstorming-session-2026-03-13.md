---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['brainstorming-session-2026-03-11.md']
session_topic: 'S6 Review Session — S2 Retriever 修复 Brainstorming 决策验证'
session_goals: '对 S2 全部 PENDING 决策进行独立对抗性审查，产出可执行的验收 checklist'
selected_approach: 'ai-recommended'
techniques_used: ['Adversarial Code Review', 'Community Validation', 'Acceptance Criteria Design']
ideas_generated: ['6维度审查报告 + 统一验收表']
context_file: ''
session_active: false
workflow_completed: true
---

# S2 Retriever 修复 — 验收档案

**Review Session:** S6
**审查对象:** S2 Brainstorming（brainstorming-session-2026-03-11.md）
**审查方法:** 独立 Agent 对抗性代码审查 × 6 维度 + 社区/论文验证
**日期:** 2026-03-13

---

## 一、审查摘要

S2 Brainstorming 产出 22 个任务（T1-T19 + 3 补充），6 个架构维度选型。本 Review Session 对每个维度启动独立 Agent 进行对抗性代码审查 + 社区验证，核心结论：

| 维度 | S2 决策 | 审查判定 | 关键发现 |
|------|---------|----------|----------|
| 1. 接口统一 | SearchResult TypedDict `{doc_id, content, score, metadata}` | ✅ 正确 | 与 Haystack/LlamaIndex 对齐；**multimodal_retriever 是唯一不符合的** |
| 2. 搜索策略 | Hybrid Search 激活（~28 行） | ⚠️ 方向正确，工作量低估 | 引擎 90% 但集成 0%；RRF score 压缩 bug；实际需 50-85 行 |
| 3. 可靠性 | Circuit Breaker + RetryPolicy | ⚠️ 方向正确，需设计决策 | RetryPolicy 100% 死代码（异常被 catch）；backend 已有 CB 实现可复用 |
| 4. 调度策略 | 规则分类器 MVP | ✅ 正确 | fan_out 天然支持条件 dispatch；rewrite_query prefix stacking bug 确认 |
| 5. 融合算法 | RRF + 修复 weighted/cascade/time_decay bug | ✅ 正确 | 3 个 bug 全部确认，修复量 ~23 行 |
| 6. 去重机制 | content-hash doc_id | ⚠️ 方向正确，方案需改进 | `content[:200]` 有前缀碰撞风险；8 位 hex 空间不足；建议全文 hash + 12 位 |

---

## 二、统一验收表

> **使用方式：** S2 执行完成后，逐条检验。每条标注 PASS / FAIL / PARTIAL。

### Wave 1：根因修复 — 让每个 Retriever 返回真实数据

| # | Task | 验收标准 | 验证方法 | 代码审查发现的风险 |
|---|------|----------|----------|-------------------|
| 1 | **T6** SearchResult 接口统一 | 所有 6 个 retriever 输出均包含 `doc_id, content, score, metadata` 且类型正确 | 单元测试：逐 retriever 调用 → assert 字段存在 + 类型匹配 | multimodal_retriever 返回 `{id, media_type, path, relevance_score}` — **唯一不符合的，必须修复** |
| 2 | **T6** fuse_results 无 KeyError | fuse_results 对任意 retriever 组合输出不产生 KeyError | 集成测试：6 源混合结果通过 RRF/weighted/cascade 三种 fusion | check_quality 用 `r["score"]` 直接访问（非 `.get()`），缺 key 会崩 |
| 3 | **T6** API 层映射正确 | API 响应格式与 SearchResult 一致 | E2E 测试：真实查询 → 检查 HTTP 响应 JSON 结构 | API 层对 multimodal 有单独映射逻辑，统一接口后需同步更新 |
| 4 | **T1** Graphiti retriever SDK 重写 | 对任意查询返回非空结果（前提：Neo4j 有数据） | 集成测试：写入测试数据 → 查询 → assert len(results) > 0 | 当前 MCP import 永远失败 → 100% 返回空；`add_memory`/`add_relationship` 即使"可用"也是 stub |
| 5 | **T2** Multimodal retriever 修复 | 调用 `lancedb.search(table="multimodal_content")` 返回 SearchResult 格式 | 集成测试：创建 multimodal_content 表 + 插入数据 → 查询 → assert 格式匹配 | 当前调用不存在的 API `client.search_multimodal()` + 返回格式不兼容 |
| 6 | **T3** Textbook retriever 修复 | 使用正确 db_path + textbooks 表存在且可查 | 集成测试：indexing 流程创建 textbooks 表 → 查询 → assert 非空 | 当前硬编码 `~/.lancedb`；`_get_associated_textbooks()` 是 TODO 返回 `[]` |
| 7 | **T4** Cross-canvas retriever 实现 | `find_related_canvases()` 返回非空的关联 canvas 列表 | 集成测试：创建多个 canvas 有交叉概念 → 查询 → assert 返回关联 canvas | 当前 `find_related_canvases()` 永远返回 `[]`，降级为全库搜索 |
| 8 | **T5** vault_notes 双重搜索消除 | vault_notes 不在 DEFAULT_TABLES 中 | 代码审查：assert `"vault_notes" not in DEFAULT_TABLES` | — |
| 9 | **T12** search() 默认表修复 | DEFAULT_TABLES 与实际存在的表对齐 | 启动测试：每个 DEFAULT_TABLE 在 LanceDB 中存在 | — |

### Wave 2：搜索质量 — 从"能用"到"好用"

| # | Task | 验收标准 | 验证方法 | 代码审查发现的风险 |
|---|------|----------|----------|-------------------|
| 10 | **T13** Hybrid search 激活 | `query_type="hybrid"` 从 fan_out_retrieval 到 `_search_internal` 全链路打通 | 集成测试：传入 hybrid → 日志确认进入 hybrid 分支 | `search_multiple_tables()` 不接受 `query_type` 参数 — **主管道阻断点** |
| 11 | **T13** Hybrid score 正常 | hybrid 结果 score 不被压缩到 0.5 附近 | 单元测试：hybrid search 结果 score 可通过 0.7 质量阈值 | RRF score 经 `1-score` → `1/(1+distance)` 双重转换被压到 0.500-0.508 — **必须修复** |
| 12 | **T13** 所有表有 FTS index | DEFAULT_TABLES 全部创建 FTS index | 启动测试：对每个表调用 `create_fts_index` 不报错 | 仅 vault_notes 有 FTS index，其他 3 表缺失 |
| 13 | **T13** 增量 index 后 FTS 可见 | 追加文档后 FTS 能搜到新内容 | 测试：追加文档 → FTS 查询 → assert 命中新内容 | Tantivy index 是静态的，追加数据后需 rebuild |
| 14 | **T14** 中文 FTS 有效 | 中文查询 FTS 分支返回有意义结果 | 真实测试：查询"逆否命题" → FTS 匹配到包含该词的文档 | Tantivy 默认 tokenizer 对中文按字符分，无法关键词匹配。**优先测试 Lance 原生 jieba tokenizer**（`base_tokenizer="jieba/default"`），失败则走 jieba 预分词方案 |
| 15 | **T14** 索引/查询分词一致 | 索引时和查询时使用相同分词方式 | 对比测试：同一文本索引后查询能命中 | 不一致会导致静默的检索失败 |
| 16 | **T15** content-hash doc_id | 同一内容在不同查询中返回相同 doc_id | 单元测试：同一文档两次搜索 → assert doc_id 相同 | S2 方案 `content[:200]` 有前缀碰撞风险，建议改为全文 hash + 12 位 hex |
| 17 | **T16** Weighted fusion 不归零 | 等分 source（score 全相同）的结果不被丢弃 | 单元测试：传入等分结果 → assert weighted_score > 0 | `min==max` 时 `normalized_score = 0.0` → 全部归零 |
| 18 | **T17** Time decay 使用真实时间 | time decay 计算使用文档创建时间而非查询时间 | 单元测试：传入 1 天前 vs 30 天前的文档 → assert decay 不同 | metadata `timestamp` 设为 `datetime.now()` 遮蔽 `created_at` |

### Wave 3：架构增强 — 系统级可靠性与智能调度

| # | Task | 验收标准 | 验证方法 | 代码审查发现的风险 |
|---|------|----------|----------|-------------------|
| 19 | **T7** Circuit Breaker | retriever 连续失败后自动跳过（OPEN 状态），恢复后自动重试（HALF_OPEN） | 集成测试：mock retriever 连续失败 → assert 被跳过 → 恢复 → assert 重新调用 | `backend/app/utils/circuit_breaker.py` 已有完整实现可复用；**需先决定 RetryPolicy vs catch-all 的兼容方案**（当前异常被 catch，RetryPolicy 100% 死代码） |
| 20 | **T8** RetryPolicy 生效 | 瞬态错误（网络超时等）触发自动重试 | 集成测试：注入瞬态异常 → 日志确认重试 N 次 | 当前所有 retriever 的 try/except 吞掉异常 → RetryPolicy 永远不触发。需改为：可重试异常向上抛、不可重试异常 catch 并降级 |
| 21 | **T9** 规则分类器 MVP | 不同类型查询 dispatch 不同 retriever 组合 | 集成测试：概念查询 vs 笔记查询 vs 跨 canvas 查询 → assert Send 列表不同 | fan_out_retrieval 天然支持条件 dispatch（List[Send] 过滤）；strategy_selector.py 有概念设计但执行函数只处理 2 源（死代码） |
| 22 | **T10** rewrite_query 无 prefix stacking | 多次重写不叠加前缀 | 单元测试：重写 3 次 → assert 不包含重复前缀 | 确认 bug：读 `messages[-1]`（含前次重写结果）而非 `original_query`。`original_query` 字段存在但从未被填充 |
| 23 | **T11** Cascade fusion 含 vault_notes | cascade 策略不丢弃 vault_notes 结果 | 单元测试：vault_notes 有结果 → cascade fusion → assert vault_notes 结果出现在输出中 | vault_notes 不在 Tier 1 或 Tier 2 硬编码列表中，100% 被丢弃 |

### Post-MVP

| # | Task | 验收标准 | 验证方法 | 备注 |
|---|------|----------|----------|------|
| 24 | **T18** Reranker 真实实现 | rerank_results 返回与输入不同的排序 | 集成测试：输入乱序结果 → assert 输出顺序变化 | 当前 `_rerank_local` 和 `_rerank_cohere` 都是 `return results`（100% 占位符） |
| 25 | **T19** Reranker 本地 fallback | Cohere API 不可用时自动切换 cross-encoder | 集成测试：断开网络 → assert 仍返回 reranked 结果 | — |

---

## 三、对 S2 原始估计的修正

| S2 原始声明 | 审查判定 | 修正 |
|------------|----------|------|
| "Hybrid search 代码已 90% 实现" | **部分属实** | 引擎内核 90%，集成激活 0%。更准确表述："引擎 90%，集成 0%" |
| "只需 ~28 行激活" | **低估** | 仅打通 vault_notes 约 8 行；主管道 + score 修复需 35-45 行；含 jieba 需 50-85 行 |
| "graphiti-core SDK 零成本切换" | **需验证** | 参考实现存在，但 add_memory/add_relationship 也是 stub，需审查参考实现质量 |
| "Circuit Breaker 与 Send() 天然适配" | **正确** | fan_out_retrieval 返回 List[Send]，条件过滤直接可行 |
| "content-hash doc_id 避免碰撞" | **方案需改进** | `content[:200]` + 8 位 hex 有碰撞风险，建议全文 hash + 12 位 hex |

---

## 四、跨维度系统性问题

以下问题不属于单个任务，但影响多个维度：

| 问题 | 影响范围 | 严重度 |
|------|---------|--------|
| **RetryPolicy vs catch-all 冲突** | T7, T8, 所有 retriever | HIGH — 必须在实施 Circuit Breaker 前决定错误处理模型 |
| **`original_query` 从未被填充** | T10, rewrite 循环 | MEDIUM — rewrite_query 读 messages[-1] 导致 prefix stacking |
| **multimodal_retriever 格式不匹配** | T6, fusion 全部 | CRITICAL — 唯一不符合 SearchResult 的 retriever |
| **Graphiti client 完全是假实现** | T1, T4（依赖 Graphiti） | CRITICAL — MCP 永远不可用 + stub 函数 |
| **Reranking 是占位符** | Wave 2 质量目标 | HIGH — fusion 后无 rerank 等于少了一个质量层 |
| **strategy_selector.py 死代码** | T9 | LOW — 概念可参考但执行函数需重写 |
| **parallel_retrieval.py 死代码** | — | LOW — 只支持 2 路 dispatch，已被 state_graph.py 取代 |

---

## 五、实施前必须做的前置决策

| # | 决策项 | 选项 | 推荐 |
|---|--------|------|------|
| PD1 | 错误处理模型 | A: 保持 catch-all（RetryPolicy 无效）<br>B: 可重试异常向上抛 + 不可重试 catch<br>C: 三层模型（CB→Retry→Catch） | **C** — Circuit Breaker 在 fan_out 层跳过 OPEN，可重试异常触发 RetryPolicy，不可重试异常 catch 降级 |
| PD2 | 中文 FTS 方案 | A: Lance 原生 jieba tokenizer<br>B: jieba 预分词 + 空格拼接<br>C: ngram tokenizer | **先测 A，失败走 B** |
| PD3 | content-hash 规格 | A: `content[:200]` + 8 位 hex（S2 方案）<br>B: 全文 hash + 12 位 hex | **B** — 消除前缀碰撞 + 降低 birthday 碰撞 |
| PD4 | `source` 字段位置 | A: 保持在 metadata 内<br>B: 提升为 SearchResult 一等公民 | **B** — multi-retriever 场景高频过滤，避免深层访问 |

---

## 六、Deep Explore 补充发现（用户已确认）

### CRITICAL：Embedding 模型天花板

当前 embedding 模型 `all-MiniLM-L6-v2` 只支持英文，是中文搜索质量的硬上限。社区推荐 **BGE-M3**（北京智源，原生中文，100+ 语言）。此项**不在 S2 范围内**（需重建全部索引），建议作为独立高优先级任务与 S2 并行或紧随其后执行。

**时序风险：** S2 先用当前模型修好 hybrid search → 后换 BGE-M3 需重建索引。执行时需考虑。

### 新增验收标准（#26-#29）

| # | Task | 验收标准 | 验证方法 | 代码审查发现的风险 |
|---|------|----------|----------|-------------------|
| 26 | Per-retriever 耗时记录 | 每次搜索日志含各渠道耗时 + 总耗时 | 集成测试：真实查询 → 日志包含 `retriever={name} latency_ms={N}` | 当前无任何 per-retriever 延迟追踪 |
| 27 | 结构化日志 | 每次搜索日志含 `{retriever, status, result_count, latency_ms, error_type}` | 集成测试：成功 + 失败查询 → assert 日志包含结构化字段 | 当前错误被静默吞掉，无结构化记录 |
| 28 | 权重配置唯一 | `DEFAULT_SOURCE_WEIGHTS` 只有一份定义（消除 config.py vs nodes.py 冲突） | 代码审查：grep 全部 `DEFAULT_SOURCE_WEIGHTS` 定义，assert 只有一处 | config.py 是 5 源版本（无 vault_notes），nodes.py 是 6 源版本，数值也不同 |
| 29 | 初始 state 完整性 | `rag_service.query()` 构建的 initial_state 包含 `subject`、`original_query` 等全部必要字段 | 单元测试：assert initial_state 包含 CanvasRAGState 所有非 Optional 字段 | 当前缺 subject（学科隔离失效）、original_query（rewrite bug 根因之一） |

### S2 范围外但需记录的事项

| 事项 | 为什么不放 S2 | 建议时机 |
|------|-------------|---------|
| Embedding 模型换 BGE-M3 | 需重建全部索引，独立大任务 | 与 S2 并行或紧随其后（CRITICAL 优先级） |
| Contextual Retrieval | 索引层增强，不是检索层 | Embedding 升级后 |
| QualityChecker 半实现 | 不影响 S2 核心目标 | S3 pipeline 重建时 |
| fusion/ 1400 行死代码 | S1 死代码清理范围 | S1 执行时 |
| Retrieval-Verification 信息断层 | 跨系统问题 | 独立 session |

---

## 七、前置决策确认状态

| # | 决策项 | 选定方案 | 用户确认 |
|---|--------|---------|---------|
| PD1 | 错误处理模型 | 三层模型（CB→Retry→Catch） | ✅ 已确认 |
| PD2 | 中文 FTS 方案 | 先测 Lance 原生 jieba，失败走预分词 | ✅ 已确认 |
| PD3 | content-hash 规格 | 全文 hash + 12 位 hex | ✅ 已确认 |
| PD4 | source 字段位置 | 提升为 SearchResult 一等公民 | ✅ 已确认 |

---

## 八、Graphiti 记录汇总

本 session 共记录到 `canvas-dev` group：
- `[Session-Start]` S6 Review Session
- `[Code-Review]` × 4（6 维度对抗性审查 + 代码盲区审查）
- `[Acceptance-Criteria]` × 2（维度 1、维度 2 单独记录）
- `[Research]` Deep Explore 补充发现（Embedding 模型 + 4 条新增标准）
- `[Decision]` PD1-PD4 前置决策确认
- `[Session-End]` S6 Review Session 完成
