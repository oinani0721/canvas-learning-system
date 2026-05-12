# Canvas Learning System — ChatGPT 对抗审查 prompt (Q1+Q2+Q3 P0 修复)

> 用户复制本文档全文到 ChatGPT (推荐 o1 / GPT-5 thinking model) 作为对抗审查任务的输入。
> 目标:让 ChatGPT 找出 3 个 P0 hotfix 是否真实可用、是否还有未发现的暗病。
> 关联 commit:见正文末尾 "verifiable artifacts" 段
> 生成日期: 2026-05-12 (worktree: feature-obsidian-hybrid-dev)

---

## You are an adversarial reviewer

The user repeatedly reported 3 product-level pains over multiple iterations:
1. **Q1**: RAG returns whiteboard/MOC/index-style content that is irrelevant
2. **Q2**: The system runs across multiple Obsidian vaults but isolation may leak data
3. **Q3**: The user wants global search of teaching notes when stuck during problem-solving — but the plugin previously required an active note (`节点/<X>.md`) for all 3 hotkeys, blocking the actual "I don't know which note to open" scenario

3 sets of P0 fixes were just shipped to address these. Your job is to **adversarially verify whether each set actually works as claimed** — not by trust, but by reading the code / tests / wiring.

For each Q, return a verdict: **PASS** / **CONDITIONAL PASS** / **FAIL** + reasoning + remaining risk.

---

## Project context (minimal)

- Stack: FastAPI backend + Obsidian plugin (TypeScript) + LanceDB (vector store) + Neo4j (KG via Graphiti) + Ollama bge-m3 (embeddings)
- Plugin lives at `frontend/obsidian-plugin/src/main.ts` and registers commands like `canvas:chat-with-context` (Cmd+Shift+E), `canvas:study-question` (Cmd+P deep mode), `canvas:open-node-chat` (Cmd+Shift+C), and (new) `canvas:global-search`
- Backend endpoints under `backend/app/api/v1/endpoints/chat.py`:
  - `POST /api/v1/chat/enrich-context` — current-note + wikilink neighbors + supplementary materials
  - `POST /api/v1/chat/post-turn-extract` — post-conversation error extraction
  - `POST /api/v1/chat/global-search` (NEW) — vault-wide search without an active note
- ContextVar `current_subject_id` (from `app.core.subject_config`) carries the active vault identifier across the request
- LanceDB tables use vault_id-prefix (e.g. `cs_61b_vault_notes`) for cross-vault isolation

---

## Q1 — RAG precision: rerank engine no longer silently broken

### Claim
The rerank engine in `supplementary_reranker.py` (originally shipped 2026-05-11 commit `549d5f0`) had 5 P0 bugs that made it silently no-op. All 5 are now fixed. A bonus "chunk-type-aware filter" detects MOC/Index list-style chunks.

### What to verify

1. **P0-A**: TYPE_WEIGHTS table previously had PRD concept words (`lecture_notes / discussion / exam_review / wiki_concepts / chat_session / raw_notes`) but the indexer in `backend/app/services/lancedb_client.py` writes `source_type ∈ {note, video_transcript, image_ocr}`. **Verify** that the fix added `note: 0.7 / video_transcript: 0.9 / image_ocr: 0.6` to `TYPE_WEIGHTS` and that the PRD-original 6 entries are still there for forward compat
2. **P0-B**: `filter_threshold = 0.42` previously killed almost all candidates. **Verify** that `rerank()` now has a `min_keep` parameter (default 3) that triggers a "filter floor" — if filtering would leave fewer than `min_keep` or remove > 80% of candidates, the filter is bypassed and the unfiltered result is returned with `filter_floor_triggered=True` written to the first material
3. **P0-C**: chat.py used to read `_supp_lancedb_singleton` directly (cold-start race). **Verify** the call site now reads `await _get_supp_lancedb_client(init_timeout=5.0)` so the first request after boot triggers lazy init
4. **P0-D**: tier-2 legacy fallback used to set `degraded=True` per row but the outer result dict still said `degraded=False`. **Verify** that `search_supplementary()` now propagates `degraded=True, reason="tier2_legacy_unprefixed"` to the outer dict whenever any row has `is_legacy_fallback=True`
5. **P0-E**: `_classify_snippet_taint()` previously fail-open on any exception (`taint="clean"`). **Verify** the fix discriminates: `ImportError` still returns clean (dev environment) but `RuntimeError` returns `taint="review", risk_score=0.5` (fail-closed)
6. **Bonus**: `_is_link_list_chunk(content, threshold=0.6)` detects MOC/Index list-style chunks via `wikilink_count / non_link_token_count > 0.6` and writes `is_link_list_chunk=True` to material dict. XML output renders `is_link_list="true"` only when True

### Verifiable artifacts (read these to verify)

- `backend/app/services/supplementary_reranker.py` (TYPE_WEIGHTS table + rerank() with min_keep param)
- `backend/app/services/supplementary_search_service.py` (tier-2 degraded propagation + chunk filter + guard fail-closed)
- `backend/app/api/v1/endpoints/chat.py` (lazy await singleton)
- `backend/tests/unit/test_supplementary_reranker.py` (104 pass: TestTypeWeightsIndexerTransition / TestFilterFloor / 既有 retain)
- `backend/tests/unit/test_supplementary_search_service.py` (TestTopLevelDegradedFromLegacyFallback / TestClassifySnippetTaintFailClosed / TestIsLinkListChunk / TestFormatSupplementaryXmlLinkListAttr)
- `backend/tests/unit/test_chat_endpoint.py` (test_enrich_context_*_lazy_init)

### Adversarial questions to answer

- Does the new `note: 0.7` weight actually match what indexer writes? Look at where `source_type=` is set in `lancedb_client.py:~1444,~1644` (or wherever else)
- Does the `min_keep` floor logic interact badly with `top_k=5`? (If filter would leave 4 candidates and top_k=5, what happens?)
- Is the `_is_link_list_chunk` regex `\[\[[^\[\]]+\]\]` safe against pathological inputs (e.g., nested `[[...]]` or `[[ ]]`)?
- Are there code paths where tier-2 fallback `is_legacy_fallback` flag is set but later overwritten before reaching the outer dict propagation check?
- Does `chat.py` still have any OTHER call sites that read `_supp_lancedb_singleton` directly (bypassing the lazy getter)? Grep both files

---

## Q2 — Multi-vault isolation actually live

### Claim
Story 2.5.Y claimed 10/10 tasks done for multi-vault isolation, but the most recent audit found 2 P0 still leaking: (a) `WikilinkGraphService` is a singleton across vaults, and (b) `BackgroundTaskManager` loses ContextVar on `asyncio.create_task()`. Both are now fixed.

### What to verify

1. **WikilinkGraphService per-vault dict**: `_wikilink_graph_service: Optional[...]` was a global singleton. **Verify** it's now `_wikilink_graph_services: dict[str, WikilinkGraphService]` keyed by vault_id from ContextVar. Verify `get_wikilink_graph_service()` derives the key via `_resolve_vault_key()` which reads `get_current_subject_id()` and normalizes via `sanitize_subject_name`; falls back to `__default__` if no ContextVar set
2. **BackgroundTaskManager copy_context**: `asyncio.create_task(coro)` doesn't auto-propagate ContextVars to background tasks. **Verify** the fix uses `asyncio.create_task(coro, context=contextvars.copy_context())` (Python 3.11+ native param)

### Verifiable artifacts

- `backend/app/services/wikilink_graph_service.py:~317-411` (per-vault dict + `_resolve_vault_key` + helpers `clear_cache_for_vault / clear_all_caches / get_cache_stats`)
- `backend/app/services/background_task_manager.py:~200` (copy_context)
- `backend/tests/unit/test_wikilink_graph_service.py::TestMultiVaultIsolation` (3 new tests: test_per_vault_isolation / test_no_contextvar_uses_default_key / test_clear_cache_for_vault)
- `backend/tests/unit/test_background_task_manager.py` (3 new tests: test_create_task_inherits_contextvar / test_create_task_with_different_contextvars / test_default_contextvar_propagates)

### Adversarial questions

- Is `_resolve_vault_key()` robust against weird ContextVar values (None, empty string, special chars, very long strings)?
- What's the cache eviction policy if a vault is deleted? Is there an unbounded memory growth risk if many vaults are used over time?
- Are there OTHER singletons elsewhere in the codebase that have the same cross-vault leak pattern? Grep for `_*_service: Optional[...]` at module level
- Is `contextvars.copy_context()` guaranteed to propagate ALL relevant ContextVars, or just `current_subject_id`? Are there other ContextVars in the codebase that should follow?
- What if `BackgroundTaskManager.submit_task` is called from a context where ContextVar is not yet set (e.g., during startup)?

---

## Q3 — Skill global search: plugin entry without active note + multi-seed BFS

### Claim
Previously, all 3 plugin hotkeys (`Cmd+Shift+E`, `Cmd+P deep mode`, `Cmd+Shift+C`) required an active `节点/<X>.md` file via `isNodePath()` guard. User scenario "I'm on Dashboard / blank view and want to search the vault for a concept I don't know" had NO plugin entry. A new `canvas:global-search` command was added (no isNodePath guard) and a new `POST /api/v1/chat/global-search` endpoint. Also, `enrich_from_wikilink_graph` now supports `additional_seeds` for multi-seed BFS so that "node X solving with foreign concept Y" can pull in Y's neighborhood too.

### What to verify

1. **Frontend command registration**: `canvas:global-search` is registered with NO `isNodePath` check (callable from any view including non-`节点/` files). No default hotkey (user-bind only)
2. **Frontend handler**: `handleGlobalSearch()` reuses `UserQuestionModal` (existing modal from study-question handler), gets vault_id, POSTs to backend, writes `enriched_context` to clipboard with prefix `/chat-with-context\n\n...`, opens Claudian sidebar, shows Notice. Failure paths classified: `backend_timeout` (AbortError), `backend_unreachable` (TypeError), `backend_error` (!ok or empty enriched_context), `non_json_response`. AbortController 8s timeout
3. **Backend endpoint `POST /api/v1/chat/global-search`**: accepts `{user_question, vault_id, subject_id?, top_k_max?, hard_cap?}`. Calls `sanitize_vault_id + build_vault_group_id + set_current_subject_id` (ContextVar injection). Uses `await _get_supp_lancedb_client(init_timeout=5.0)` (avoids P0-C). Calls `search_supplementary + rerank(median_degree=0.0) + format_supplementary_xml`. Returns manifest + supplementary XML + degradation reason
4. **Multi-seed BFS**: `enrich_from_wikilink_graph` accepts new optional `additional_seeds: list[str] | None = None`. When provided, runs BFS from each seed, merges, dedups by slug, keeps min(hop_distance). `TraceItem.seed_origin: str | None` records which seed each item came from. Backward compat: None preserves single-seed behavior

### Verifiable artifacts

- `frontend/obsidian-plugin/src/global-search.ts` (NEW: pure helpers `buildGlobalSearchPayload / classifyFetchFailure / buildSuccessNoticeMessage / buildFailureNoticeMessage`)
- `frontend/obsidian-plugin/src/main.ts:~515-534` (command registration in cmds array, after `canvas:study-question`)
- `frontend/obsidian-plugin/src/main.ts:~919-1027` (handleGlobalSearch — full handler)
- `frontend/obsidian-plugin/tests/global-search.test.ts` (19 new tests: 5 describe blocks)
- `backend/app/services/wikilink_context_service.py:~371-615` (additional_seeds param + multi-seed merge + seed_origin)
- `backend/app/api/v1/endpoints/chat.py:~828-1020` (GlobalSearchRequest / GlobalSearchResponse / endpoint body)
- `backend/tests/unit/test_chat_endpoint.py` (test_global_search_endpoint_*)
- `backend/tests/unit/test_wikilink_context_service.py` (test_enrich_multi_seed_*)

### Adversarial questions

- The frontend uses `this.settings.backendUrl` (existing convention) — is the URL guaranteed configured before the new command fires? What if user just installed plugin and never opened settings?
- The new endpoint shares the same `chat_router` global `require_internal_api_key` dependency. Is the auth header propagated by the new frontend handler? Check `getInternalApiKey()` or equivalent in main.ts handler
- Multi-seed BFS: when seed_A's BFS hits seed_B's territory mid-traversal, what's the dedup precedence? Does `min(hop_distance)` correctly choose the lower hop? What if both hops are equal — which `seed_origin` wins?
- For `additional_seeds`, are non-existent seeds silently skipped (degraded best-effort) or do they raise? Check `degradations` list propagation
- The global-search endpoint returns just supplementary XML — no current_note section, no wikilink_neighbors. Is that the correct UX for "the user has no active note"? Could it be improved with a "query intent → infer 1-3 seed nodes" preprocess step?
- Plugin: `getVaultId` — does it sanitize or pass raw `app.vault.getName()`? Backend sanitizes again, but if raw name has chars that crash the modal or URL encoding...

---

## Cross-cutting concerns

1. **DD-12 scope boundary**: backend agent should only touch backend files, frontend agent only frontend. Verify the file lists match this rule
2. **DD-03 no mock**: verify no TODO(human) / mock data / stub functions were left in code
3. **DD-14 traceability**: each commit should carry `PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17` and the relevant Story trace
4. **DoD-3 UAT sheets**: 3 new UAT sheets shipped to `_bmad-output/验收单/Story-*-2026-05-12.md`. Each must have section "🤖 Claude 已代验" + "👤 你来验" (双段铁律). Section 👤 must have 0 tech jargon (no curl/docker/HTTP/JSON/.env/endpoint/...). Verify by grepping the new files

---

## Required output format

For each Q (Q1, Q2, Q3) emit:

```
### Q<N> verdict: <PASS | CONDITIONAL PASS | FAIL>

**What works**:
- [bullet list]

**Remaining risk / unverified claims**:
- [bullet list with file:line evidence]

**Suggested follow-ups** (sorted by severity):
1. P0/P1/P2 + 1-sentence description
2. ...
```

Plus a final section:

```
### Cross-cutting verdict
- DD-12 scope: [PASS/FAIL]
- DD-03 no mock: [PASS/FAIL]
- DD-14 traceability: [PASS/FAIL]
- DoD-3 UAT sheets: [PASS/FAIL]

### Top 3 risks to address before user UAT
1. ...
2. ...
3. ...
```

---

## Verifiable artifacts (cite these)

**Backend files modified**:
- `backend/app/services/supplementary_reranker.py`
- `backend/app/services/supplementary_search_service.py`
- `backend/app/services/wikilink_graph_service.py`
- `backend/app/services/wikilink_context_service.py`
- `backend/app/services/background_task_manager.py`
- `backend/app/api/v1/endpoints/chat.py`

**Backend tests** (245 pass total in scoped sweep):
- `backend/tests/unit/test_supplementary_reranker.py` (104)
- `backend/tests/unit/test_supplementary_search_service.py` (含 chunk filter + tier-2 degraded + guard fail-closed)
- `backend/tests/unit/test_chat_endpoint.py` (含 lazy_init + global-search endpoint)
- `backend/tests/unit/test_wikilink_graph_service.py` (含 TestMultiVaultIsolation)
- `backend/tests/unit/test_wikilink_context_service.py` (含 multi-seed BFS)
- `backend/tests/unit/test_background_task_manager.py` (新文件,3 测试)

**Frontend files modified**:
- `frontend/obsidian-plugin/src/global-search.ts` (NEW)
- `frontend/obsidian-plugin/src/main.ts`
- `frontend/obsidian-plugin/tests/global-search.test.ts` (NEW)
- `frontend/obsidian-plugin/package.json`

**Frontend tests**: 173 pass (154 baseline + 19 new)

**UAT sheets** (`_bmad-output/验收单/`):
- `Story-2.2+2.9-Q1-rerank-hotfix-2026-05-12.md`
- `Story-2.5.Y-Q2-multi-vault-hardening-2026-05-12.md`
- `Story-2.2+2.9-Q3-global-search-2026-05-12.md`

**Commit**: 见此 prompt 末尾 (用户复制时填入实际 SHA)
