# PRD — Canvas Learning System Phase 3 Pipeline Repair

> Based on: Gemini Deep Research validation (2026-03-30) + 24 Graphiti decision records + S27 GDA 10 decisions
> Path A: Phase1 COMPLETE, Phase2 COMPLETE, **Phase3 = this PRD**, Phase4 = separate PRD

---

## Epic 1: Profile Click-to-Jump Navigation (P0 — GDA-6)

> User confirmed P0 highest priority: "click tip/error to jump to original context"

### Feature 1.1: Frontend DTO schema augmentation
- Add `sourceCanvasId?: string` and `sourceNodeId?: string` to `TipItem` interface in `frontend/src/services/api-client.ts`
- Add `sourceCanvasId?: string` and `sourceNodeId?: string` to `WeaknessItem` interface in `frontend/src/services/api-client.ts`
- Acceptance Criteria:
  - TypeScript compiles without errors after adding fields
  - Fields are optional (backward compatible with existing data)

### Feature 1.2: Backend serialization of source IDs
- Update the FastAPI Pydantic response model for `/api/v1/profile/{nodeId}/summary` to include `source_canvas_id` and `source_node_id` fields
- Extract these fields from Neo4j/Graphiti metadata when building the response
- Acceptance Criteria:
  - GET `/api/v1/profile/{nodeId}/summary` response includes `source_canvas_id` and `source_node_id` for each tip and weakness item
  - Fields are null when source data is unavailable (graceful degradation)

### Feature 1.3: Frontend click-to-jump handler
- In `LearningProfile.tsx` or `ReviewItem.tsx`, implement onClick handler that calls `goToCanvas(item.sourceCanvasId)` then `setSelectedNodeId(item.sourceNodeId)`
- Acceptance Criteria:
  - Clicking a tip/error item with valid sourceCanvasId navigates to the correct canvas
  - The target node is selected/highlighted after navigation
  - Items without sourceCanvasId show no navigation action (no crash)

---

## Epic 2: Architectural Pruning — cross_canvas + RAG Cleanup (P0 — GDA-2)

> GDA-2: cancel textbook + cross-canvas search. RAG 6 channels to 4 channels.

### Feature 2.1: Delete cross_canvas_service.py
- Remove `backend/app/services/cross_canvas_service.py`
- Remove all imports and dependency injection bindings referencing CrossCanvasService
- Acceptance Criteria:
  - File does not exist after change
  - `grep -r "cross_canvas" backend/app/` returns zero results (excluding tests and docs)
  - Backend starts successfully without errors

### Feature 2.2: Remove textbook_retriever references
- Remove any `textbook_retriever` channel from RAG pipeline configuration
- Verify only 4 channels remain: LanceDB, Vault Notes, Graphiti, Multimodal
- Acceptance Criteria:
  - `grep -r "textbook_retriever" backend/app/` returns zero results
  - RAG pipeline configuration lists exactly 4 channels
  - Backend starts and `/api/v1/health` returns 200

### Feature 2.3: Fix vault_notes dual-search bug
- Remove `vault_notes` from DEFAULT_TABLES array if it appears alongside a dedicated vault_notes retrieval node
- Acceptance Criteria:
  - `vault_notes` is not queried twice in a single search request
  - Hybrid search returns results without duplicates

---

## Epic 3: Layer 3 ACP Prompt Externalization (P1 — GDA-4)

> GDA-4: prompts must be in external files, not inline Python strings

### Feature 3.1: Create layer3.md template
- Create `backend/app/prompts/exam/layer3.md` with a template that accepts: node_content, node_type, effective_proficiency, mastery_label, student_tips, error_history, edge_reasons, conversation_summary
- Acceptance Criteria:
  - File `backend/app/prompts/exam/layer3.md` exists
  - Template contains placeholders for all 8 context variables
  - Template is valid Markdown

### Feature 3.2: Refactor _format_acp_layer to load from file
- Modify `question_generator.py` `_format_acp_layer` method to read `layer3.md` and inject variables via `.format()` instead of inline Python f-strings
- Acceptance Criteria:
  - `_format_acp_layer` calls `_load_prompt_file("layer3.md")`
  - No inline prompt strings remain in the method (only variable injection)
  - Unit test verifies the formatted output contains all context data
  - `generate_question` tool still produces valid exam questions

---

## Epic 4: Neo4j Fulltext Index + search_memories Completion (P1)

> Tier 2 search silently returns empty because fulltext index is not provisioned

### Feature 4.1: Auto-create Neo4j fulltext index on startup
- Add initialization routine to create `episode_content` fulltext index during FastAPI lifespan startup
- Use: `CREATE FULLTEXT INDEX episode_content IF NOT EXISTS FOR (n:EpisodicNode) ON EACH [n.content]`
- Acceptance Criteria:
  - After backend startup, Neo4j contains the `episode_content` fulltext index
  - `SHOW INDEXES` in Neo4j includes `episode_content`
  - Tier 2 search returns results for known keywords

### Feature 4.2: Verify three-tier search end-to-end
- Ensure `search_memories` in `memory_service.py` correctly falls through Tier 1 then Tier 2 then Tier 3
- Add logging to indicate which tier produced results
- Acceptance Criteria:
  - When Graphiti is available: Tier 1 returns semantic results
  - When Graphiti times out: Tier 2 returns keyword results from fulltext index
  - When both fail: Tier 3 returns in-memory cache results
  - Total latency < 2 seconds

---

## Epic 5: Chinese Hybrid Search Activation (P1 — MVP #10 #11)

> jieba tokenizer code exists but hybrid search is not activated

### Feature 5.1: Switch default search mode to hybrid
- Change default `query_type` from `"vector"` to `"hybrid"` in LanceDB search configuration
- Acceptance Criteria:
  - Default search mode is `"hybrid"` (not `"vector"`)
  - Search queries use both dense vectors and FTS scoring

### Feature 5.2: Wire jieba tokenization into search pipeline
- Ensure `_jieba_tokenize()` is called on both index-time text and query-time input
- Acceptance Criteria:
  - Chinese query "Bayes theorem in Chinese" returns relevant notes
  - English queries still work correctly
  - Unit test with Chinese text confirms tokenization and retrieval

---

## Epic 6: group_id Dynamic Binding (P1 — GDA-3)

> GDA-3: group_id = canvas name. Currently a static default value for all canvases.

### Feature 6.1: Pass canvas name as group_id from frontend
- Frontend must send the active canvas name when calling memory/search APIs
- Backend must use this as the `group_id` parameter for Graphiti operations instead of a static default
- Acceptance Criteria:
  - `record_learning_memory` uses the canvas name as group_id
  - `search_memories` filters by the active canvas group_id
  - Different canvases produce isolated memory namespaces
  - No static group_id strings remain in backend/app/ (excluding tests/config defaults)

### Feature 6.2: Normalize canvas name to group_id format
- Convert canvas name to lowercase, strip special characters (e.g., "CS 188" becomes "cs188")
- Acceptance Criteria:
  - Canvas named "CS 188" produces group_id "cs188"
  - Canvas named "Linear Algebra" produces group_id "linearalgebra" or "linear-algebra"
  - Normalization is consistent between frontend and backend
