## Why

`backend/lib/agentic_rag/faithfulness_check.py` 在 `no_answer` 和 `no_claims` 两条路径上直接返回 `faithfulness_score=1.0`，而 `canvas_agentic_rag` 图通常不在图内生成 answer，导致几乎每次 RAG 调用都被记成"满分"，污染 `_faithfulness_stats` 与 `health_monitor` 的健康判定，把退化系统性显示为绿灯。`backend/app/services/scoring_faithfulness.py` 在 evidence/rubric 抽取失败时存在同款 vacuous-true 路径。同时 `fuse_results` / `rerank_results` 把融合质量信号（channel_status、断崖、RRF 参数、多源一致性）只写日志不写 state，外部调用方无法区分"低召回"与"融合差"，且 `route_after_quality_check` 缺少一次性"昂贵兜底"出口，A8 调研要求的可观测性与 CRAG 兜底全部缺位。

## What Changes

- **修复 P0 vacuous-true（faithfulness_check.py）**：`messages[-1].role != "assistant"` / 空 answer / 空 claims 三条路径返回 `faithfulness_score=None` 与 `status="not_applicable_*"`，并把 `last_role` 检查前置到 `extract_claims()` 调用之前以阻断无意义的 LLM 烧 token
- **修复 P0 vacuous-true（scoring_faithfulness.py）**：`EvidenceGroundingResult` / `ScoreConsistencyResult` 的 `total_count == 0` 路径返回 `score=None` 与 `status="not_applicable"`；`ScoringFaithfulnessChecker.run_full_check` 聚合时跳过 None 子分，结果新增 `not_applicable_checks: List[str]` 字段
- **新增 fusion 可观测性（state.py + nodes.py）**：`CanvasRAGState` 新增 `fusion_report` / `sharpness_report` / `deep_research_used` 三个字段，`fuse_results` 节点构造 fusion_report（含 `channel_status` / `coverage_score` / `avg_support_topk` / `support_ge_2_ratio` / `fusion_strategy` / `rrf_k`），`rerank_results` 节点构造 sharpness_report（含 `top_scores` / `max_gap` / `is_flat` / `cut`）
- **新增多源一致性元数据**：`_fuse_rrf_multi_source` 与 `_fuse_layered_rrf` 在 dedup 路径累积 `doc_sources: Dict[str, Set[str]]`，每个 fused result 的 `metadata` 写入 `support_sources: List[str]` 与 `support_count: int`
- **修复 strategy state-priority（nodes.py）**：`fuse_results` 与 `rerank_results` 两个节点显式 `state.get(...) or _safe_get_config(...)`，让 per-request override 优先于 runtime config
- **新增 CRAG 一次性兜底（state_graph.py + new deep_research.py）**：`route_after_quality_check` 增加 `deep_research_fallback` 第三出口（条件 `quality_grade=="low" and safe_degradation and not deep_research_used`），新建 `deep_research.py` 节点用 LLM JSON 输出生成 multi_queries + 启用 cross_subject 后回到 `fan_out_retrieval` 重检索一次，由 `deep_research_used: bool` 守卫保证一次性
- **新增 deep research 配置项（config.py）**：`deep_research_enabled` / `deep_research_model` / `deep_research_timeout_s` / `deep_research_max_queries` / `deep_research_max_tokens` 五个 config 项，含 prompt 注入硬约束防御
- **更新 known-gotchas.md**：新增一行 G-FAI-001 记录 not_applicable 语义契约
- **不动 FAITHFULNESS_ENABLED 默认值**（用户决策）

## Capabilities

### Modified Capabilities
- `algo-rag`: 新增三类契约——Faithfulness Not-Applicable Contract / Fusion-Reranking Observability Contract / One-Shot CRAG Fallback Contract

## Impact

**受影响代码**：
- `backend/lib/agentic_rag/faithfulness_check.py`（vacuous true 修复）
- `backend/app/services/scoring_faithfulness.py`（vacuous true 修复 + not_applicable 字段）
- `backend/lib/agentic_rag/state.py`（新增 3 个 state 字段）
- `backend/lib/agentic_rag/nodes.py`（fusion_report + sharpness_report + support_sources + state-priority）
- `backend/lib/agentic_rag/state_graph.py`（route_after_quality_check 第三出口 + deep_research_fallback 节点注册）
- `backend/lib/agentic_rag/deep_research.py`（**新文件**）
- `backend/lib/agentic_rag/config.py`（新增 5 个 deep_research_* 配置项）
- `docs/known-gotchas.md`（新增 G-FAI-001 一行）

**新增测试**：
- `backend/tests/unit/test_faithfulness_check_boundary.py`
- `backend/tests/unit/test_scoring_faithfulness_not_applicable.py`
- `backend/tests/unit/test_fusion_strategy_override.py`
- `backend/tests/unit/test_fusion_report.py`
- `backend/tests/unit/test_sharpness_report.py`
- `backend/tests/unit/test_deep_research_fallback.py`
- `backend/tests/integration/test_crag_route_one_shot.py`（需真实 Neo4j + LanceDB）

**严禁触碰**（属其他 active change 管辖）：
- `backend/app/services/verification_service.py:1832-1947`（属 `fix-rag-transform-and-episode-isolation`）
- `backend/app/services/sync_service.py` / `canvas_service.py`（属 `fix-fr-kg-04-schema-drift-and-sync-hardening`）
- `backend/app/api/v1/endpoints/sync.py`
- `frontend/src/services/sync-engine.ts`

**下游消费者契约变更**：所有依赖 `faithfulness_score >= 0.85` 的代码必须改为 `score is not None and score >= 0.85`。`llm_call_logger.record_faithfulness_score()` 已对 None early-return（line 571-572），天然兼容。

**协调顺序建议**：本 change 与 `fix-rag-transform-and-episode-isolation` / `fix-fr-kg-04-schema-drift-and-sync-hardening` 文件级零交叉，可并行开发；建议合并顺序为 sync 修复 → RAG transform → 本 change，但顺序不绝对。
