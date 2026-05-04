---
story_id: "2.9"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 10
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-01"
  - "FR-CONV-04"
  - "Story-2.1-Phase1-成熟度升级-2026-05-03.md (Phase 2 list)"
---

# Story 2.9: AI 对话 RAG Phase 2 — Rerank + Evidence + Path Trace

Status: ready-for-dev

> Story 2.1 Phase 1 (commit `dad9ed7`) 已 ship 并通过完整 UAT (3 轮 ChatGPT 对抗审查
> 4/10 → 7/10 → 8/10 + 用户实测 Claude 真推导 `Av=λv → det(A-λI)=0` + 防注入 PoC).
> 本 Story 承接 Phase 2 — 把"邻居装载"升级为"Query-aware + 可解释 + 多源融合".

## Story

As a 学习者,
I want AI 对话的邻居上下文按我当前问题相关性排序、显式标注关系来源、覆盖 backlink/heading/alias 多维度,
So that 在大 vault (>50 节点) 场景下 AI 不被高连接节点 (hub) 噪音垄断, 且能给出"基于哪条推理链"的可追溯回答.

## Acceptance Criteria

### AC #1 — Query-Aware Rerank (Phase 2.5, ~2h)

**Given** plugin 调用 `/api/v1/chat/enrich-context` 时传入非空 `user_question` (例如 "特征值和 PCA 关系")
**When** assembler 装载 N-hop 邻居
**Then** 邻居按 (a) 邻居 frontmatter type/relationships keyword overlap with user_question + (b) 邻居 body excerpt 与 user_question 的 BM25 / cosine similarity 排序
**And** rerank 后的邻居顺序在 trace.included 里反映 (rerank_score 字段记录)
**And** Phase 1 的 `mode="preload"` (无 user_question) 行为不变 (按 hop_distance + slug 字典序)
**And** 单元测试覆盖: 同 hop 不同 score 排序正确 / score 相同 fallback 字典序 / 空 user_question 走 Phase 1 路径

### AC #2 — Hub Penalty + Degree Scoring (Phase 2.1, ~2h)

**Given** wikilink graph 中某节点 degree (出+入边总数) > P95 阈值 (从 graph stats 实测计算)
**When** BFS N-hop 遍历
**Then** 该 hub 节点被加上 `hub_penalty = log(degree / median_degree + 1)` 惩罚分
**And** rerank 时 score -= hub_penalty
**And** 防止 "Index" / "MOC" / "Hub" 类节点垄断邻居列表
**And** trace.omitted 记录被 hub penalty 排到 budget 之外的节点 (reason="hub_penalty_too_high")

### AC #3 — Path Trace (Phase 2.2, ~1h)

**Given** 一个 2-hop 邻居 X 通过路径 `seed → A → X` 到达
**When** 装载到 prompt
**Then** neighbor metadata 段加新字段 `via="A"` 显示中间跳点
**And** trace.included 的 TraceItem 加 `path_trace: list[str]` 字段记录 BFS 路径
**And** 单元测试: 1-hop 邻居 path_trace=[seed, neighbor] 长度 2; 2-hop path_trace 长度 3

### AC #4 — Backlink + Heading + Alias 扩展 (Phase 2.3, ~3h)

**Given** 节点 X 在另一节点 Y 的正文里被 `[[X]]` 引用 (backlink, 反向)
**When** seed = X 触发 enrich
**Then** Y 也作为 1-hop 邻居返回 (与 outgoing wikilink 等价)
**And** `[[X#Heading]]` 引用形式触发后, 邻居只装载 X 中该 heading 段落 (而非整个 X)
**And** `[[X|Alias]]` 引用形式触发后, slug 字段使用 alias 而非 X
**And** 单元测试: backlink-only / heading-only / alias-only 三种纯净场景

### AC #5 — Relationship Evidence (Phase 2.4, ~1.5h)

**Given** frontmatter 声明 `relationships: [{type: prerequisite, target: X, evidence: "see eq. 3.2 in Strang"}]`
**When** enrich 装载该邻居
**Then** trace.included 的 TraceItem 加 `evidence: str | None` 字段
**And** neighbor metadata 段渲染 `- 引证: see eq. 3.2 in Strang` 行 (escape)
**And** plugin 在 Notice 显示 "包含 N 条引证" 字样 (可选)

### AC #6 — Plugin Timeout + 错误降级 (Phase 2.6, ~0.5h)

**Given** backend `/api/v1/chat/enrich-context` 响应慢于 plugin timeout (默认 3000ms)
**When** plugin 等待超时
**Then** plugin 显示 Notice "backend 超时, 用 plugin 端 1-hop 本地降级"
**And** plugin 降级到 `node-chat` 路径 (Cmd+Shift+C 等价行为) 用 Obsidian metadataCache.resolvedLinks 取 5 个邻居装载
**And** 降级路径的 prompt 顶部写 `Degradations: backend_timeout / fallback=local_metadata`
**And** 用户视角无功能损失 (只是邻居数量从 N-hop 降到 1-hop)

## Tasks

### Task 1: Query-Aware Rerank Engine (Phase 2.5, ~2h)

- [ ] backend/app/services/rerank_service.py 新增 (BM25 lexical + 可选 cosine vector)
- [ ] wikilink_context_service.py: enrich_from_wikilink_graph 接受 user_question, mode="answer" 时调 rerank
- [ ] TraceItem 加 rerank_score 字段
- [ ] chat.py endpoint 把 user_question + mode 传到 enrich
- [ ] 测试: test_rerank_service.py + test_wikilink_context_service.py 加 rerank fixture

### Task 2: Hub Penalty + Degree Scoring (Phase 2.1, ~2h)

- [ ] wikilink_graph_service.py: 新增 get_degree_stats() 返回 P50/P95/median degree
- [ ] enrich loop: 对每个邻居计算 hub_penalty = log(degree/median + 1)
- [ ] 应用到 rerank score
- [ ] trace.omitted 记录 hub-penalized 节点
- [ ] 测试: 模拟 hub vault (1 个节点 N degree, 其他 1 degree) 验证 penalty 排序

### Task 3: Path Trace (Phase 2.2, ~1h)

- [ ] NeighborNote 加 path_trace: list[str] 字段
- [ ] wikilink_graph_service.get_neighbors BFS 时记录 path
- [ ] WikilinkNeighborContext + TraceItem 加 path_trace
- [ ] _format_neighbor_metadata 加 via="A" 属性 (escape)
- [ ] 测试: 1-hop / 2-hop path_trace 内容验证

### Task 4: Backlink + Heading + Alias (Phase 2.3, ~3h)

- [ ] wikilink_graph_service.py: obsidiantools backlinks API 接入 (or 自建反向边 map)
- [ ] heading 解析 (markdown-it / 自实现 regex 提取 ## section)
- [ ] alias 提取 ([[X|Y]] 解析 Y 作为 slug)
- [ ] WikilinkNeighborContext 加 backlink: bool / heading_anchor: str | None / alias: str | None 字段
- [ ] 测试: 单独场景 + 组合场景

### Task 5: Relationship Evidence (Phase 2.4, ~1.5h)

- [ ] TraceItem.evidence: str | None (escape)
- [ ] _extract_relationship_type 拓展返回 (type, evidence) tuple
- [ ] _format_neighbor_metadata 渲染 "- 引证: ..." 行 (xml_text_escape)
- [ ] plugin Notice 显示引证数 (可选)
- [ ] 测试: frontmatter 含 evidence vs 不含的对比

### Task 6: Plugin Timeout + 降级 (Phase 2.6, ~0.5h)

- [ ] frontend/obsidian-plugin/src/main.ts: handleChatWithContext 加 AbortController + timeout 3000ms
- [ ] 超时降级到 collectNodeNeighbors (1-hop local) 路径
- [ ] manifest 段加 Degradations: backend_timeout 标记
- [ ] plugin 测试: mock fetch timeout 验证降级触发 + Notice 文案

## Pitfalls (从 Phase 1 学到)

- BM25 / cosine 引入新依赖 (sklearn/rank_bm25), 注意 backend deps 增量
- hub_penalty 阈值要从真实 vault 实测 (canvas-vault 30 节点目前 degree 分布是 P95≤3, hub penalty 几乎不触发, 但未来 1000+ 节点 vault 必要)
- backlinks API 对 obsidiantools 版本敏感, 需 pin 版本
- heading 解析要兼容 CRLF / BOM (Phase 1.7+ FRONTMATTER_PATTERN 已修同样问题)
- alias 嵌套 ([[X|Y|Z]]) 是无效 Obsidian 语法, 要 deny

## Dev Agent Record

待 dev-story 实施时填充.

## File List

待实施时填充.

## Change Log

- 2026-05-03 创建 (Story 2.1 Phase 1 ship 后承接 Phase 2 spec)

## Validation Notes

- AC 引用验收单 `_bmad-output/验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md` 第 5 段 Phase 2 list (Phase 2.1 ~ 2.6 工作量估算)
- ChatGPT 三轮审查接受作为 Phase 2 follow-up: timeout / multi-worker race / unsupported callout / build_timestamp 精度等不在本 story 范围
