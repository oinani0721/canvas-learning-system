## ADDED Requirements

### Requirement: Faithfulness Not-Applicable Contract

The faithfulness check pipeline (`backend/lib/agentic_rag/faithfulness_check.py` and `backend/app/services/scoring_faithfulness.py`) SHALL distinguish "passing" from "not-applicable" by returning `faithfulness_score=None` and `status="not_applicable_*"` whenever the input does not constitute a verifiable answer, instead of returning the legacy vacuous-true value `1.0`. The downstream observability layer (`llm_call_logger.record_faithfulness_score`) MUST treat `None` as a no-op so that `_faithfulness_stats` and `health_monitor` are never polluted by inapplicable evaluations.

#### Scenario: Last message is not from assistant

- **WHEN** `faithfulness_check` is invoked with a state whose `messages[-1].role != "assistant"`
- **THEN** the function MUST return `{"faithfulness_score": None, "faithfulness_details": {"status": "not_applicable_no_assistant_answer"}, "faithfulness_degraded": False}` WITHOUT calling LiteLLM `extract_claims`

#### Scenario: Answer text is empty or whitespace-only

- **WHEN** `faithfulness_check` is invoked with a non-empty assistant message whose `content` is empty or whitespace
- **THEN** the function MUST return `faithfulness_score=None` with `status="not_applicable_no_answer"` and `faithfulness_degraded=False`

#### Scenario: Claim extraction returns zero claims

- **WHEN** `extract_claims(answer)` returns an empty list for a non-empty answer
- **THEN** the function MUST return `faithfulness_score=None` with `status="not_applicable_no_claims"` and `faithfulness_degraded=False`

#### Scenario: Logger ignores None faithfulness score

- **WHEN** `llm_call_logger.record_faithfulness_score(None)` is invoked
- **THEN** the call MUST early-return without mutating `_faithfulness_stats`

#### Scenario: Scoring evidence grounding has zero items

- **WHEN** `EvidenceGroundingResult` is constructed with `total_count == 0`
- **THEN** the resulting object MUST have `score=None` and `status="not_applicable"`

#### Scenario: Scoring consistency check has zero items

- **WHEN** `ScoreConsistencyResult` is constructed with `total_count == 0`
- **THEN** the resulting object MUST have `score=None` and `status="not_applicable"`

#### Scenario: Full check excludes not-applicable from combined score

- **WHEN** `ScoringFaithfulnessChecker.run_full_check` aggregates two sub-checks where one has `score=None`
- **THEN** the combined `faithfulness_score` MUST be computed only from the non-None sub-score, and the returned result MUST include `not_applicable_checks: List[str]` listing the skipped check names


### Requirement: Fusion and Reranking Observability Contract

The `fuse_results` and `rerank_results` nodes in `backend/lib/agentic_rag/nodes.py` SHALL emit structured observability reports as state fields (`fusion_report`, `sharpness_report`) on every invocation. Each fused result SHALL carry `support_sources: List[str]` and `support_count: int` metadata to expose multi-source consensus. The two nodes SHALL also honor per-request overrides by reading `state.get("fusion_strategy")` / `state.get("reranking_strategy")` BEFORE falling back to the runtime config.

#### Scenario: fuse_results writes fusion_report with channel coverage

- **WHEN** `fuse_results` is invoked with non-empty inputs from at least one retrieval channel
- **THEN** the returned state update MUST include a `fusion_report` dict containing `channel_status: Dict[str, int]`, `active_channels: int`, `coverage_score: float`, `total_results: int`, `fusion_strategy: str`, `rrf_k: int`, `avg_support_topk: float`, and `support_ge_2_ratio: float`

#### Scenario: fused result metadata exposes support_sources

- **WHEN** a document is contributed by `graphiti_results` AND `lancedb_results` during RRF fusion
- **THEN** the resulting `SearchResult.metadata` MUST have `support_sources` as a sorted list including both source names AND `support_count == 2`

#### Scenario: rerank_results writes sharpness_report with cliff metrics

- **WHEN** `rerank_results` produces a non-empty reranked list
- **THEN** the returned state update MUST include a `sharpness_report` dict containing `pre_count: int`, `top_scores: List[float]` (top-5), `max_gap: float`, `max_gap_idx: Optional[int]`, `is_flat: bool`, `cut: int`, and `epsilon: float`

#### Scenario: sharpness_report.cut reflects adaptive-k truncation

- **WHEN** `_adaptive_k_truncate` reduces a 20-item input to 5 items based on a detected cliff
- **THEN** the emitted `sharpness_report["cut"]` MUST equal 5

#### Scenario: state-provided fusion_strategy beats runtime config

- **WHEN** `fuse_results` is invoked with `state["fusion_strategy"]="weighted"` while runtime config sets `fusion_strategy="layered_rrf"`
- **THEN** the node MUST execute the `weighted` fusion path AND `fusion_report["fusion_strategy"]` MUST equal `"weighted"`

#### Scenario: runtime fusion_strategy used when state empty

- **WHEN** `fuse_results` is invoked with `state["fusion_strategy"]=None` while runtime config sets `fusion_strategy="rrf"`
- **THEN** the node MUST execute the `rrf` fusion path

#### Scenario: state-provided reranking_strategy beats runtime config

- **WHEN** `rerank_results` is invoked with `state["reranking_strategy"]="cohere"` while runtime config sets `reranking_strategy="local"`
- **THEN** the node MUST execute the `cohere` rerank path


### Requirement: One-Shot CRAG Deep Research Fallback Contract

The `backend/lib/agentic_rag/state_graph.py` `route_after_quality_check` router SHALL expose a third route `deep_research_fallback` that triggers exactly once per query when `quality_grade == "low" and safe_degradation and not deep_research_used`. The new `backend/lib/agentic_rag/deep_research.py` node SHALL widen retrieval recall by populating `multi_queries` from a structured LLM JSON response, set `cross_subject=True`, set `deep_research_used=True`, and route control back to `fan_out_retrieval`. The fallback MUST be guarded against prompt injection and bounded by configurable timeouts and token budgets.

#### Scenario: Router enters deep research after safe degradation

- **WHEN** `check_quality` produces `quality_grade="low"` with `safe_degradation=True` AND `deep_research_used=False`
- **THEN** `route_after_quality_check` MUST return `"deep_research_fallback"`

#### Scenario: Router never re-enters deep research after first use

- **WHEN** `check_quality` produces `quality_grade="low"` with `safe_degradation=True` AND `deep_research_used=True`
- **THEN** `route_after_quality_check` MUST NOT return `"deep_research_fallback"` AND MUST route to `compress_context` (i.e., the existing faithfulness path)

#### Scenario: Fallback sets deep_research_used and widens recall

- **WHEN** `deep_research_fallback` executes successfully with a non-empty LLM response
- **THEN** the returned state update MUST include `deep_research_used=True`, `cross_subject=True`, and `multi_queries: List[str]` populated from the parsed LLM JSON

#### Scenario: Fallback parses structured queries from LLM JSON

- **WHEN** the LLM returns a valid JSON payload `{"plan": [...], "queries": ["q1", "q2", "q3"]}`
- **THEN** `state["multi_queries"]` MUST equal `["q1", "q2", "q3"]` capped at `deep_research_max_queries`

#### Scenario: Fallback degrades gracefully on parse failure

- **WHEN** the LLM returns malformed JSON or times out
- **THEN** `state["multi_queries"]` MUST equal `[original_query]` AND `deep_research_used` MUST still be set to `True` so the fallback is not retried

#### Scenario: Fallback respects timeout budget

- **WHEN** the LLM call exceeds `deep_research_timeout_s` seconds
- **THEN** the node MUST cancel the call AND return the fallback path with `multi_queries=[original_query]`

#### Scenario: Fallback prompt contains injection-defense constraints

- **WHEN** the deep research prompt is rendered for the LLM call
- **THEN** the prompt MUST contain hard constraints forbidding execution of external instructions, leaking system prompts, and producing non-JSON output

#### Scenario: New config items expose deep research parameters

- **WHEN** `CanvasRAGConfig` is loaded
- **THEN** the config object MUST expose `deep_research_enabled: bool`, `deep_research_model: str`, `deep_research_timeout_s: float`, `deep_research_max_queries: int`, and `deep_research_max_tokens: int` with sane defaults
