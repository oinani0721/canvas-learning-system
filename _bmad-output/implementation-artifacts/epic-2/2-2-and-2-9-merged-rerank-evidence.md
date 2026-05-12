---
story_id: "2.2+2.9"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 40
estimate_days: "5-8"
depends_on: ["2.1"]
blocks: []
supersedes: ["2.2", "2.9"]
trace:
  - "FR-CONV-01"
  - "FR-CONV-03"
  - "FR-CONV-04"
  - "ChatGPT-Review-2026-05-11 P0-A Multi-Vault 全链路"
  - "ChatGPT-Review-2026-05-11 P0-C 修主检索链路 + 检索回归基准"
created: "2026-05-11"
merge_rationale: "ChatGPT Deep Research 揭示 Story 2.2 Phase B (精排+wikilink) 与 Story 2.9 6 AC 实质重叠;合并避免重复工作。"
---

# Story 2.2+2.9 Merged: Supplementary Rerank + Wikilink + Evidence (Phase 2)

Status: ready-for-dev

> **合并依据**: ChatGPT Deep Research 对抗性审查 (2026-05-11) 揭示 Story 2.2 Phase B (精排+wikilink 三精度) 与 Story 2.9 6 AC 实质重叠;且 ChatGPT P0-C 明确"现在 fallback 是救火方案,不应该成为常态——'搜索能跑'不等于'RAG 正常'",要求先修主检索链路+建立检索回归基准,再做精排。
>
> **Phase A 已 ship** (Story 2.2 Phase A MCP 集成+三档降级,验收单 2026-05-08)。本 spec 承接 Phase B+C,合并 Story 2.9 全部 6 AC。
>
> **替代关系**:
> - 原 `2-2-supplementary-material-search.md` → status: superseded
> - 原 `2-9-rag-rerank-and-evidence.md` → status: superseded

## Story

As a 学习者,
I want AI 对话邻居上下文按 (a) 我当前问题相关性 + (b) 节点类型权重 + (c) 防 hub 噪音排序,且通过精确 wikilink (file / heading / block / alias) 跳转,同时显式标注 evidence 来源,
So that 在大 vault (>50 节点) 场景下 AI 答案有可解释性、可追溯、不被 hub 节点噪音垄断,且检索链路质量有量化基准而非靠"感觉很快"。

## Acceptance Criteria

### AC #1 — 主检索链路修复 + 检索回归基准 (前置 P0)

**Given** plugin 调用 `/api/v1/chat/enrich-context` 并启用 supplementary_search
**When** 主检索链路执行
**Then** LangGraph `fan_out_retrieval` 的 5 路并发实际全部执行 (不再因 conditional_edges 缺 path_map 静默跳过)
**And** Ollama base_url 在 Docker 环境下解析为 `host.docker.internal:11434` (不再 fallback)
**And** `/index/vault?force_rebuild` endpoint 不再持有旧 fingerprints singleton (调用即新建实例)
**And** raw LanceDB fallback 触发率 ≤ 5% (从当前"经常触发"降到"应急救火")
**And** 基准指标可观测: Faithfulness ≥ 0.75 / Context Relevance ≥ 0.70 / 空结果率 ≤ 10% / MRR@10 ≥ 0.55
**And** 基准报告 ship 到 `_bmad-output/research/retrieval-baseline-2026-05-XX.md`

### AC #2 — Plugin Timeout + 错误降级 (速胜)

**Given** backend `/api/v1/chat/enrich-context` 响应慢于 plugin timeout (默认 3000ms)
**When** plugin 等待超时
**Then** plugin 显示 Notice "backend 超时,用 plugin 端 1-hop 本地降级"
**And** plugin 降级到 `node-chat` 路径用 Obsidian metadataCache.resolvedLinks 取 5 个邻居装载
**And** 降级路径的 prompt 顶部写 `Degradations: backend_timeout / fallback=local_metadata`
**And** 用户视角无功能损失 (只是邻居数量从 N-hop 降到 1-hop)

### AC #3 — Wikilink 四精度 + Backlink

**Given** 邻居装载触发 wikilink 解析
**When** 系统格式化输出
**Then** 支持 4 种精度:
  - `[[X]]` → 整文件
  - `[[X#Heading]]` → 只装载该 heading 段落 (markdown-it 或 regex 提取 ## section)
  - `[[X#^block_id]]` → 装载 block-id 锚定的段落
  - `[[X|Alias]]` → slug 字段使用 alias 而非 X
**And** Backlink 反向: 节点 Y 引用 `[[X]]` 时,seed=X 触发 enrich 也把 Y 作为 1-hop 邻居返回 (与 outgoing 等价)
**And** 单元测试: 4 种精度 + backlink-only / heading-only / alias-only 三种纯净场景
**And** 嵌套 alias (`[[X|Y|Z]]`) 显式 deny (无效 Obsidian 语法)

### AC #4 — 合并 Rerank Engine (Type 权重 + Query-Aware + Hub Penalty)

**Given** 邻居/补充材料候选 N 条
**When** rerank engine 执行
**Then** 最终分数 = `relevance_score * type_weight - hub_penalty + query_overlap_score`

  - **Type 权重 (Story 2.2 AC #3)**: lecture_notes (1.0) > discussion (0.9) > exam_review (0.85) > wiki_concepts (0.8) > chat_session (0.7) > raw_notes (0.6)
  - **Query-aware (Story 2.9 AC #1)**: BM25 lexical + 可选 cosine vector, query = user_question; mode="preload" (无 user_question) 走 Phase 1 默认排序
  - **Hub Penalty (Story 2.9 AC #2)**: `hub_penalty = log(degree / median_degree + 1)`, 阈值从 graph stats 实测 (P95 + median)
  - 防 "Index" / "MOC" / "Hub" 类节点垄断

**And** trace.included 反映 `rerank_score / type_weight / hub_penalty / query_overlap` 各字段
**And** trace.omitted 记录被 hub penalty 排到 budget 之外的节点 (reason="hub_penalty_too_high")
**And** 过滤: `final_score < 0.70 * min_type_weight` 不显示
**And** 单元测试: 同 hop 不同 score / score 相同 fallback 字典序 / 空 user_question 走 default / hub vault 模拟

### AC #5 — Path Trace

**Given** 一个 2-hop 邻居 X 通过路径 `seed → A → X` 到达
**When** 装载到 prompt
**Then** neighbor metadata 段加新字段 `via="A"` 显示中间跳点
**And** TraceItem 加 `path_trace: list[str]` 字段记录 BFS 路径
**And** 单元测试: 1-hop path_trace 长度 2 / 2-hop 长度 3

### AC #6 — Relationship Evidence

**Given** frontmatter 声明 `relationships: [{type: prerequisite, target: X, evidence: "see eq. 3.2 in Strang"}]`
**When** enrich 装载该邻居
**Then** TraceItem 加 `evidence: str | None` 字段 (xml_text_escape)
**And** neighbor metadata 段渲染 `- 引证: see eq. 3.2 in Strang` 行
**And** plugin Notice 显示 "包含 N 条引证" 字样 (可选)

### AC #7 — 性能 + 增量索引 + 空结果降级 (从 Story 2.2 AC #4 #5 继承)

**Given** LanceDB 索引文件变更
**When** 单文件保存触发增量索引
**Then** 增量索引耗时 < 500ms/file (NFR-PERF)

**Given** LanceDB 服务不可用或索引为空
**When** 学习者启动对话
**Then** AI 正常回答,补充材料区域显示"暂无补充材料",不影响主对话流程

## Tasks

### Task 0: 修主检索链路 + 检索回归基准 (前置 P0, 3-5d)

- [ ] **T0.1** 修 LangGraph `fan_out_retrieval` conditional_edges path_map bug
  - 文件: `backend/lib/agentic_rag/workflow.py` (或对应位置)
  - 验证: 5 路并发实际触发 + 各通道返回非空
- [ ] **T0.2** 修 Ollama base_url
  - 文件: `backend/app/core/config.py` + `docker-compose.yml`
  - Docker 环境下 `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- [ ] **T0.3** 修 `/index/vault?force_rebuild` endpoint singleton
  - 文件: `backend/app/api/v1/endpoints/metadata.py` (或对应位置)
  - 调用即新建实例,不持有 fingerprints 旧状态
- [ ] **T0.4** 建立 Faithfulness 基准 (RAGAs/ARES 框架)
  - 新文件: `backend/tests/evaluation/test_faithfulness_baseline.py`
  - 数据: canvas-vault CS61B 30 节点 + 20 真实 query
  - 目标: ≥ 0.75
- [ ] **T0.5** 建立 Context Relevance 基准
  - 同上文件 + 目标 ≥ 0.70
- [ ] **T0.6** 建立 raw fallback 触发率监控
  - 文件: `backend/app/services/supplementary_search_service.py` 加 metric
  - Prometheus / structlog: `supplementary_fallback_triggered_total`
  - 目标: ≤ 5%
- [ ] **T0.7** 建立 MRR@10 / nDCG@10 基线
  - 同 T0.4 文件 + 目标 MRR ≥ 0.55 / nDCG ≥ 0.60
- [ ] **T0.8** ship 基准报告
  - 路径: `_bmad-output/research/retrieval-baseline-2026-05-XX.md`
  - 含: 6 维度数字 + 改进前后对比 + 验收单挂钩

### Task 1: Plugin Timeout + 降级 (速胜, 0.5h)

- [ ] **T1.1** frontend/obsidian-plugin/src/main.ts: handleChatWithContext 加 AbortController + timeout 3000ms
- [ ] **T1.2** 超时降级到 collectNodeNeighbors (1-hop local) 路径
- [ ] **T1.3** manifest 段加 `Degradations: backend_timeout` 标记
- [ ] **T1.4** plugin 测试: mock fetch timeout 验证降级触发 + Notice 文案

### Task 2: 合并 Wikilink Service (4h)

- [ ] **T2.1** backend/app/services/wikilink_graph_service.py: 加 backlinks API (obsidiantools 或自建反向边 map)
- [ ] **T2.2** heading 解析 (markdown-it 或自实现 regex 提取 ## section)
- [ ] **T2.3** alias 提取 (`[[X|Y]]` 解析 Y 作为 slug); 嵌套 `[[X|Y|Z]]` deny
- [ ] **T2.4** block_id 解析 (`[[X#^block_id]]`)
- [ ] **T2.5** WikilinkNeighborContext 加 `backlink: bool / heading_anchor: str | None / alias: str | None / block_id: str | None` 字段
- [ ] **T2.6** skill workflow Step 7: 格式化输出
  - 有 heading → `[[file#heading]]`
  - 有 block_id → `[[file#^block_id]]`
  - 有 alias → `[[file|alias]]`
  - 无 → `[[file]]`
- [ ] **T2.7** 输出格式: `1. 《标题》\n   "摘要片段..."\n   📄 source_file (相关度 X.XX)\n   🔗 [[wikilink]]`
- [ ] **T2.8** 主 LLM 回答与补充材料用 `---` 分隔
- [ ] **T2.9** 测试: 4 种精度 + backlink-only / heading-only / alias-only / 嵌套 alias deny / 组合场景

### Task 3: 合并 Rerank Engine (4h)

- [x] **T3.1** backend/app/services/supplementary_reranker.py 新增 (合并 Story 2.2 Task 2 + Story 2.9 Task 1+2)
- [x] **T3.2** Type 权重函数 (PRD §4.1.1):
  ```python
  TYPE_WEIGHTS = {
      "lecture_notes": 1.0, "discussion": 0.9, "exam_review": 0.85,
      "wiki_concepts": 0.8, "chat_session": 0.7, "raw_notes": 0.6
  }
  ```
- [x] **T3.3** Query-aware: 自实现 BM25 Okapi (jieba 中英分词) + 可选 cosine vector (Phase B+ 启用)
- [x] **T3.4** Hub Penalty: `hub_penalty = log(degree / median_degree + 1)`, degree 从 wikilink_graph_service.get_degree_stats() 取
- [x] **T3.5** wikilink_graph_service.py: 新增 `get_degree_stats() -> dict` 返回 P50/P95/median + `get_degree(note_key) -> int`
- [x] **T3.6** 综合: `final_score = relevance * type_weight - hub_penalty + query_overlap * 0.3`
- [x] **T3.7** chat.py endpoint 把 user_question + mode 传到 enrich (signature 已有,wire rerank 完成)
- [x] **T3.8** TraceItem 加 `rerank_score / type_weight / hub_penalty / query_overlap / evidence` 字段 (optional, supplementary 已通过 XML attribute 透出;neighbor 流向 wired 留待下 phase)
- [x] **T3.9** 过滤: final_score < 0.70 * min_type_weight 不显示 (`get_filter_threshold()` = 0.42)
- [x] **T3.10** Top 5 返回 (rerank() `top_k=5`)
- [x] **T3.11** 测试: 同 hop 不同 score / score 相同 fallback 字典序 / 空 user_question 走 default / hub vault 模拟 / type 权重单元 (42+ unit tests)

### Task 4: Path Trace (1h)

- [ ] **T4.1** NeighborNote 加 `path_trace: list[str]` 字段
- [ ] **T4.2** wikilink_graph_service.get_neighbors BFS 时记录 path
- [ ] **T4.3** WikilinkNeighborContext + TraceItem 加 path_trace
- [ ] **T4.4** _format_neighbor_metadata 加 `via="A"` 属性 (xml_text_escape)
- [ ] **T4.5** 测试: 1-hop path_trace 内容 / 2-hop 内容

### Task 5: Relationship Evidence (1.5h)

- [x] **T5.1** TraceItem.evidence: `str | None` (xml_text_escape) + WikilinkNeighborContext.evidence + TraceItemModel.evidence (API 透出)
- [x] **T5.2** _extract_relationship_info() 返回 `(type, evidence)` tuple; _extract_relationship_type() 保留为 backward-compat shim
- [x] **T5.3** _format_neighbor_metadata 渲染 `- 引证: ...` 行 (xml_text_escape + 截断 200 字)
- [ ] **T5.4** plugin Notice 显示引证数 (可选, defer to plugin iteration)
- [x] **T5.5** 测试: 含 evidence vs 不含 / xml 转义 / 截断 / shim 兼容

### Task 6: 集成测试 + 性能 + 验收单 (2-3h)

- [ ] **T6.1** 集成测试: 完整 enrich → rerank → wikilink → trace 流程
- [ ] **T6.2** 性能测试: 单文件增量索引 < 500ms
- [ ] **T6.3** 性能测试: 完整 enrich-context P95 < 1500ms (含 rerank)
- [ ] **T6.4** 验收单 ship: `_bmad-output/验收单/Story-2.2+2.9-merged-rerank-evidence-2026-05-XX.md`
- [ ] **T6.5** 验收单符合 DoD-3 双段铁律 (D3-A ~ D3-E 5 铁律 + Phase A/B 方法论分层)
- [ ] **T6.6** sprint-status.yaml 更新: 2-2-and-2-9-merged-rerank-evidence → review

## Dev Notes

### 关键依赖

- **BM25**: `rank_bm25` (pip install)
- **Cosine similarity**: `sentence-transformers` (已有 bge-m3)
- **Heading 解析**: `markdown-it-py` (Python) 或自实现 regex; obsidiantools backlinks
- **xml_text_escape**: 已有 helper, 防 prompt injection
- **基准框架**: `ragas` (推荐) 或 `ares-rag` (https://github.com/stanford-futuredata/ARES)

### 来源对照

| 本 Spec Task | Story 2.2 来源 | Story 2.9 来源 | ChatGPT 来源 |
|---|---|---|---|
| T0 | — | — | P0-C 修主检索链路+回归基准 |
| T1 | — | AC #6 / Task 6 | — |
| T2 | Task 3 wikilink 三精度 | AC #4 / Task 4 backlink+heading+alias | — |
| T3 | Task 2 精排 (type 权重) | AC #1+#2 / Task 1+2 (query-aware + hub penalty) | — |
| T4 | — | AC #3 / Task 3 | — |
| T5 | — | AC #5 / Task 5 | — |
| T6 | Task 5 测试 | (各 Task 测试) | — |

### Project Structure Notes

```
backend/app/services/
  supplementary_reranker.py       # 新增 (T3)
  wikilink_graph_service.py       # 扩展 (T2, T3.5, T4)
  rerank_service.py               # 新增 BM25+cosine (T3.3)
backend/app/api/v1/endpoints/
  chat.py                         # 修改: user_question + mode 传 enrich (T3.7)
  metadata.py                     # 修改: /index/vault?force_rebuild singleton 修复 (T0.3)
backend/lib/agentic_rag/
  workflow.py                     # 修改: fan_out_retrieval path_map (T0.1)
backend/tests/evaluation/
  test_faithfulness_baseline.py   # 新增 (T0.4-T0.7)
backend/tests/unit/
  test_supplementary_reranker.py  # 新增
  test_rerank_service.py          # 新增
  test_wikilink_graph_service.py  # 扩展
frontend/obsidian-plugin/src/
  main.ts                         # 修改: handleChatWithContext timeout (T1)
_bmad-output/research/
  retrieval-baseline-2026-05-XX.md  # 新增基准报告 (T0.8)
_bmad-output/验收单/
  Story-2.2+2.9-merged-rerank-evidence-2026-05-XX.md  # 新增 (T6.4)
```

### References

- PRD §4.1.1 补充学习材料 (line 3707-3877): type 权重 + wikilink 三级精度
- ChatGPT Review Response (2026-05-11): `_bmad-output/chatgpt-review-response-2026-05-11.md` (P0-A/B/C 完整建议)
- LanceDB hybrid: `backend/app/services/tool_executor.py` (line 60-124)
- search_vault_notes MCP: `backend/app/services/react_agent.py` (line 55-137)
- 学习科学: Elaborative Interrogation (Pressley 1987, d=0.80) + Interleaving (Rohrer 2015, d=0.40) + Spaced Retrieval (Karpicke 2012)
- Phase 1 Story 2.1 验收单: `_bmad-output/验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md`

## Pitfalls

- **BM25 / cosine 依赖增量**: `rank_bm25` 新增, 注意 backend requirements.txt; sentence-transformers 已有
- **Hub penalty 阈值**: canvas-vault 30 节点目前 degree P95 ≤ 3, hub penalty 几乎不触发; 但未来 1000+ 节点 vault 必要——保留实测 + 可配置
- **Backlinks API 版本**: obsidiantools 版本敏感, 需 pin
- **Heading 解析**: 兼容 CRLF / BOM (Phase 1.7+ FRONTMATTER_PATTERN 已修同样问题)
- **Alias 嵌套**: `[[X|Y|Z]]` 是无效 Obsidian 语法, 必须 deny
- **LangGraph fan_out 修复风险**: 修了 conditional_edges path_map 后, 5 路并发实际执行可能引入新问题 (并发死锁 / 资源竞争); 必须先 stress test
- **Ollama base_url 修复**: 修了 host.docker.internal 后, 本地非 Docker 启动 (uvicorn 直跑) 反而失败——需要 env-aware 配置
- **检索回归基准的"假阳性"**: Faithfulness 0.75 是行业可接受最低线, 但单一指标可能掩盖局部缺陷; 必须配合 Context Relevance + 空结果率多维度看

## Dev Agent Record

### Implementation Plan (Session 2026-05-11 续, T3+T5 ship)

**Phase 演进 (rerank 4 维度递增, 签名稳定)**:
1. T3b — 创建 `supplementary_reranker.py` + TYPE_WEIGHTS 表 + `rerank()` 基础排序
2. T3c — 新建 `rerank_service.py` 自实现 BM25 Okapi (避免引入未声明 `rank-bm25` 依赖)
3. T3d — wikilink_graph_service.py 加 `get_degree_stats()` + `get_degree()`; `compute_hub_penalty()` 加入 final_score
4. T3.7-T3.10 — chat.py wire rerank; XML attribute 透出 rerank 4 字段; `get_filter_threshold()` + `top_k=5`
5. T5 — TraceItem/WikilinkNeighborContext 加 evidence 字段; `_extract_relationship_info()` 返回 tuple; assembler `- 引证:` 行渲染

**关键设计决策**:
- **自实现 BM25 vs `rank-bm25` 包**: 候选集 N ≤ 30, BM25 < 1ms, 自实现 ~30 行 Okapi 公式可读, 避免依赖审计成本. jieba tokenizer 与 LanceDB hybrid 召回阶段对齐 (防 query 在 rerank 阶段丢 token)
- **DEFAULT_TYPE_WEIGHT=0.5 < min(canonical)=0.6**: 未知 source_type 应在 trace 中"可视暴露"而非冒充某 canonical 类型
- **median 而非 mean** 作 hub_penalty 基线: median 是 robust statistic, hub 节点不会拉高自身基线
- **filter 阈值 = 0.70 × min(TYPE_WEIGHTS.values()) = 0.42**: 用 canonical 最低 (raw_notes=0.6), DEFAULT_TYPE_WEIGHT 不参与阈值计算
- **pipeline 顺序: score → sort → filter → truncate**: 高质量 #6 不会被低质量 #5 挤掉

**Scope 边界 (本 iteration 完成,后续 phase 接入)**:
- ✅ supplementary 材料完整走 rerank pipeline
- ⏳ wikilink 邻居走 rerank: TraceItem.rerank_score / type_weight / hub_penalty / query_overlap 已加为 optional, 但 ChatContextAssembler 尚未回填. 留 T6+ phase 或独立 follow-up
- ⏳ cosine vector (sentence-transformers): rerank_service.py 文档预留, T3c 仅 BM25
- ⏳ T0 主检索链路修复 + RAGAs Faithfulness/Context Relevance/MRR@10 基准: 3-5d 独立 session

### Completion Notes
- 全 rerank pipeline 单元测试覆盖 (T3b 18 + T3c BM25 18 + T3d 11 + T3.9 5 + XML rendering 3 + Evidence 6+4 = 65+ new tests)
- 全后端 unit test 套零回归 (T3a/T2 前置覆盖维持 green)
- 编辑符合 wave 工作模式: red-green-refactor 每 task 闭环
- Pitfalls: hub_penalty 在 30-node vault scale 几乎不触发 (degree P95 ≤ 3), 1000+ node vault 后必要; LanceDB chunks/.../merged.md 派生路径已被 _resolve_chunks_to_source_file 回写, get_degree basename fallback 命中真实节点

## File List

**新增**:
- `backend/app/services/supplementary_reranker.py` — rerank engine (TYPE_WEIGHTS + compute_hub_penalty + rerank + get_filter_threshold)
- `backend/app/services/rerank_service.py` — BM25 Okapi primitives (tokenize / bm25_scores / normalize_to_unit)
- `backend/tests/unit/test_supplementary_reranker.py` — 42 unit tests
- `backend/tests/unit/test_rerank_service.py` — 18 BM25 + normalize unit tests

**修改**:
- `backend/app/services/wikilink_graph_service.py` — `get_degree_stats()` + `get_degree(note_key)` (T3.5)
- `backend/app/services/wikilink_context_service.py` — `_extract_relationship_info()` tuple return; WikilinkNeighborContext.evidence; TraceItem.evidence (T5.1 + T5.2)
- `backend/app/services/supplementary_search_service.py` — `format_supplementary_xml()` 透出 rerank 4 字段 attribute (T3.8)
- `backend/app/services/chat_context_assembler.py` — `_format_neighbor_metadata()` 渲染 `- 引证:` 行 (T5.3)
- `backend/app/api/v1/endpoints/chat.py` — wire rerank 进 supplementary 流程 (T3.7); TraceItemModel 加 5 optional 字段 (T3.8 + T5.1)
- `backend/tests/unit/test_wikilink_graph_service.py` — degree stats / get_degree 测试 (+8)
- `backend/tests/unit/test_supplementary_search_service.py` — XML rerank field 渲染测试 (+3)
- `backend/tests/unit/test_wikilink_context_service.py` — evidence extract + enrich 透传测试 (+6)
- `backend/tests/unit/test_chat_context_assembler.py` — `- 引证:` 渲染测试 (+4)

## Change Log

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-05-11 | v1.0 | 合并 Story 2.2 (5 AC) + Story 2.9 (6 AC) → 7 AC + 7 Tasks; ChatGPT P0-C 加入 T0 前置 |
| 2026-05-11 | v1.1 | T3 (T3.1-T3.11) + T5 (T5.1/T5.2/T5.3/T5.5) ship; 65+ new unit tests; rerank pipeline 在 chat.py supplementary 流程激活; PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17 |

## UAT Script (Phase A 已 ship,以下为 Phase B+C)

> **Phase A 已 ship**: `_bmad-output/验收单/Story-2.2-Phase-A-MCP-集成-2026-05-08.md` (review 待用户 UAT)
>
> **Phase B+C UAT 待 ship**:
>
> 1. 确保 Ollama 运行中, bge-m3 模型已加载, Docker compose 修过 host.docker.internal (T0.2)
> 2. 确保后端已完成 vault 初次索引 (POST /api/v1/metadata/index/vault)
> 3. 打开 `wiki/concepts/admissibility.md` 启动 AI 对话
> 4. 提问 "admissibility 的证明是怎么做的?"
> 5. 验证 AI 回答下方出现 `---` 分隔线和补充材料列表
> 6. 验证每条材料: 标题 / 摘要 / 相关度 / type 标记 / via="..."  (path_trace) / 引证 (如有)
> 7. 验证可点击 wikilink 跳转到对应笔记的正确位置 (含 heading / block 精度)
> 8. 故意 hub 节点测试: 提问触发 "Index" / "MOC" 类节点, 验证未垄断邻居
> 9. Plugin 超时模拟: 关 backend, 验证 plugin Notice + 1-hop local 降级
> 10. 验收单核对 7 AC + 6 维度基准指标
