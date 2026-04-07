# algo-rag Specification

## Purpose
TBD - created by archiving change fix-rag-faithfulness-and-add-crag-quality-loop. Update Purpose after archive.
## Requirements
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

### Requirement: Verification RAG Context Field Completeness

The `_get_rag_context_for_concept(concept, canvas_name)` method in `verification_service.py` SHALL return a dict with three fields (`learning_history: str`, `related_concepts: List[str]`, `common_mistakes: str`), and each field SHALL be populated from a real data source whenever data is available. Static placeholder strings (e.g. `"无已知错误模式"`) SHALL only appear when the underlying data source is genuinely empty or unavailable, never as a substitute for unimplemented extraction logic.

#### Scenario: learning_history extracted from reranked content

- **GIVEN** RAG service produces `reranked_results` with at least 1 item containing non-empty `content`
- **WHEN** `_get_rag_context_for_concept()` is called
- **THEN** the resulting `learning_history` is the joined content of the top-3 results
- **AND** it is NOT equal to `"无历史记录"`

#### Scenario: common_mistakes extracted from BKT lapse history

- **GIVEN** the concept has BKT state with `fsrs_lapses=4` and `interaction_count=10` (lapse_rate=0.4)
- **WHEN** `_extract_common_mistakes_from_bkt(concept_id, canvas_name)` is called
- **THEN** the resulting string contains `"该概念历史遗忘率 40%（4/10）"`
- **AND** it is NOT equal to `"无已知错误模式"`

#### Scenario: common_mistakes extracted from Neo4j low-score history

- **GIVEN** the concept has 2 historical Episode records linked via `[:SCORED {score: 45}]` and `[:SCORED {score: 55}]`
- **WHEN** `_extract_common_mistakes_from_bkt()` is called
- **THEN** the resulting string contains text fragments from both low-score answers (truncated to 80 chars each)
- **AND** the format is `"得分 45: ...; 得分 55: ..."`

#### Scenario: common_mistakes falls back gracefully when no signal exists

- **GIVEN** BKT state has `lapse_rate < 0.3` AND no Episode with `score < 60` exists for the concept
- **WHEN** `_extract_common_mistakes_from_bkt()` is called
- **THEN** the resulting string equals `"无已知错误模式"` (acceptable fallback for genuinely empty data)
- **AND** a structured log entry `common_mistakes_extracted` with `lapse_rate=<value>, fragments_count=0` is emitted

#### Scenario: common_mistakes survives partial dependency failure

- **GIVEN** BKT mastery_store raises an exception (service unavailable)
- **AND** Neo4j produces 1 valid low-score Episode
- **WHEN** `_extract_common_mistakes_from_bkt()` is called
- **THEN** the resulting string contains the Neo4j fragment (BKT signal omitted)
- **AND** a WARNING log entry mentions the BKT failure

### Requirement: Related Concepts Path-Like String Guard

The `related_concepts` field produced by `_get_rag_context_for_concept()` SHALL NOT contain strings that match path-like patterns (file paths, URLs, or strings ending in common file extensions). Path-like detection SHALL match strings containing `/`, `\`, `http://`, `https://`, `file://`, or ending in `.md`, `.pdf`, `.txt`, `.html`, `.docx` (case-insensitive).

#### Scenario: metadata.concept is preferred when present and non-path

- **GIVEN** a SearchResult with `metadata = {"concept": "导数", "source": "/vault/notes/calculus.md"}`
- **WHEN** `_extract_concept_name(metadata)` is called
- **THEN** the resulting name is `"导数"`

#### Scenario: file path in metadata.source is replaced by stem

- **GIVEN** a SearchResult with `metadata = {"source": "/vault/notes/导数.md"}`
- **AND** `metadata.concept` is missing
- **WHEN** `_extract_concept_name(metadata)` is called
- **THEN** the resulting name is `"导数"` (extracted from the file stem, not the full path)

#### Scenario: URL in metadata.source is rejected entirely

- **GIVEN** a SearchResult with `metadata = {"source": "https://example.com/article"}`
- **WHEN** `_extract_concept_name(metadata)` is called
- **THEN** the resulting name is `""` (empty string, not added to related_concepts)

#### Scenario: empty metadata produces empty string

- **GIVEN** a SearchResult with `metadata = {}` or `metadata = None`
- **WHEN** `_extract_concept_name(metadata)` is called
- **THEN** the resulting name is `""`

#### Scenario: related_concepts list is fully de-duplicated and path-free

- **GIVEN** RAG produces 5 reranked_results with mixed metadata (3 valid concepts + 2 file paths)
- **WHEN** `_get_rag_context_for_concept()` is called
- **THEN** the resulting `related_concepts` list contains only the 3 valid concept names
- **AND** no element of the list contains `/`, `\`, or ends in `.md`/`.pdf`

### Requirement: RAG Transform Test Coverage

The test suite SHALL include unit tests that exercise `_get_rag_context_for_concept()` with mock RAG responses matching the **actual** RAG service shape (`reranked_results: List[SearchResult]`). Tests using legacy field names (`learning_history`, `related_concepts`, `common_mistakes` directly in the mock value) SHALL be marked deprecated and migrated.

#### Scenario: Modern mock fixture uses real RAG shape

- **GIVEN** the `mock_rag_service_modern` pytest fixture
- **WHEN** any test consumes this fixture
- **THEN** the mock's `query()` produces a dict containing `reranked_results: List[Dict]` with realistic SearchResult shape (doc_id, content, score, metadata)
- **AND** does NOT pre-populate `learning_history`, `related_concepts`, or `common_mistakes` directly

#### Scenario: Legacy mock is marked deprecated

- **GIVEN** the original `mock_rag_service` fixture (with old field names)
- **WHEN** new tests are written
- **THEN** the legacy fixture has a docstring `DEPRECATED: bypasses transform; use mock_rag_service_modern instead`
- **AND** new tests use `mock_rag_service_modern`

#### Scenario: Path guard test matrix is exhaustive

- **GIVEN** the test file `test_related_concepts_path_guard.py`
- **WHEN** running the full test
- **THEN** at least 6 distinct metadata input scenarios are covered (concept-only, source-with-stem, URL, empty, title-only, mixed)
- **AND** each scenario has an explicit assertion on the extracted name

