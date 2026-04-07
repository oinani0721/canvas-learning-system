## ADDED Requirements

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
