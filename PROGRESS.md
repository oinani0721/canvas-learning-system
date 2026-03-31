# Progress

## Previous: Epic 1 (Test PRD) — COMPLETE
- Feature 1.1: /api/v1/ping endpoint — COMPLETE (commit 981e3b1)

---
## Phase 3 Pipeline Repair — IN PROGRESS

### Epic 1: Profile Click-to-Jump Navigation — COMPLETE
- Feature 1.1: Frontend DTO schema augmentation — COMPLETE
  - Added sourceCanvasId/sourceNodeId to TipItem and WeaknessItem (api-client.ts + types.ts)
  - 6 vitest tests pass ✅
- Feature 1.2: Backend serialization of source IDs — COMPLETE
  - Added source_canvas_id/source_node_id to Pydantic models + Cypher queries (profile.py)
  - 15 pytest tests pass ✅
- Feature 1.3: Frontend click-to-jump handler — COMPLETE
  - Added onNavigateToSource callback prop to LearningProfile.tsx
  - Navigate button renders for items with source IDs
  - 6 vitest tests pass ✅

### Epic 2: Architectural Pruning — cross_canvas + RAG Cleanup — COMPLETE
- Feature 2.1: Delete cross_canvas_service.py — COMPLETE
  - Deleted cross_canvas_service.py (1368 lines) + cross_canvas.py endpoint (768 lines)
  - Removed from dependencies.py, context_enrichment_service.py, verification_service.py
  - grep "cross_canvas" backend/app/ = 0 results ✅
  - 7 verification tests pass ✅
- Feature 2.2: Remove textbook_retriever references — COMPLETE
  - Deleted textbook_context_service.py (659 lines) + textbook.py endpoint (231 lines)
  - Removed from dependencies.py, router.py, context_enrichment, verification, agents
  - RAG channels: 6→4 (LanceDB, Vault Notes, Graphiti, Multimodal) ✅
- Feature 2.3: Fix vault_notes dual-search bug — COMPLETE
  - Removed vault_notes from LanceDB DEFAULT_TABLES (was queried twice)
  - DEFAULT_TABLES now ["canvas_nodes"] only, vault_notes via dedicated retriever ✅

### Epic 3: Layer 3 ACP Prompt Externalization — COMPLETE
- Feature 3.1: Create layer3.md template — COMPLETE
  - Created backend/app/prompts/exam/layer3.md with 7 placeholders + optional_sections
  - Follows existing layer1/2/4/5 pattern ✅
- Feature 3.2: Refactor _format_acp_layer to load from file — COMPLETE
  - _format_acp_layer now loads template via _load_prompt_file("layer3.md")
  - Conditional sections (tips/errors/edges/conversation) built in Python, injected as {optional_sections}
  - Graceful fallback if template file missing
  - 11 pytest tests pass ✅

### Epic 5: Chinese Hybrid Search Activation — COMPLETE (already implemented)
- Feature 5.1: Default search mode is "hybrid" — ALREADY DONE ✅
  - config.py:172 and lancedb_client.py:2192 both default to "hybrid"
- Feature 5.2: Jieba tokenization wired into pipeline — ALREADY DONE ✅
  - Index-time: add_documents() calls _jieba_tokenize() → content_tokenized column
  - Query-time: _search_internal() hybrid branch calls _jieba_tokenize(query)
  - FTS index: _rebuild_fts_index() creates Tantivy index on content_tokenized
  - RRF fusion merges dense + FTS results (k=60)
  - 23 verification tests pass ✅

### Epic 4: Neo4j Fulltext Index + search_memories Completion — COMPLETE
- Feature 4.1: Auto-create episode_content fulltext index on startup — COMPLETE
  - Added ensure_fulltext_index() to MemoryService (IF NOT EXISTS for idempotency)
  - Called during FastAPI lifespan startup in main.py
  - Graceful degradation when Neo4j unavailable ✅
- Feature 4.2: Three-tier search with logging — COMPLETE
  - Tier 1→2→3 fallthrough with per-tier result count logging
  - Tests verify tier fallthrough behavior ✅
