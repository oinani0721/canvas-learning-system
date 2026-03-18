# Story 3.12: Token 消耗追踪与成本统计

Status: ready-for-dev

## Story

As a 用户,
I want 查看 AI 使用统计——按任务分类的 Token 消耗和估算成本，
So that 我能了解系统的使用情况和成本分布。

## Acceptance Criteria

**Given** Story 1.10 的日志基础设施已就位
**When** 用户在应用设置或 Dashboard 中查看使用统计
**Then** 按任务类型（对话/评分/检索/提取/索引）分类统计 Token 消耗
**And** 显示估算成本（基于各模型定价）
**And** 支持按时间范围筛选（今天/本周/本月/全部）

## Tasks / Subtasks

### Task 1: Verify Backend Infrastructure (already complete)
- [x] 1.1 `CostTracker` class in `backend/app/middleware/cost_tracker.py` — SQLite persistence, aggregation queries (by period, by task, by day, errors), 90-day log rotation with daily compression
- [x] 1.2 `LLMCallLogger` class in `backend/app/middleware/llm_call_logger.py` — LiteLLM custom callback, batch buffer (10 entries / 5s flush), 5 task types (conversation/scoring/extraction/indexing/qa_check), error classification
- [x] 1.3 `GET /api/v1/system/llm-stats` endpoint in `backend/app/api/v1/system.py` — supports `period` (today/week/month/custom), `start_date`, `end_date`, `task_type` query params
- [x] 1.4 Lifespan initialization in `backend/app/main.py` — CostTracker singleton + LLMCallLogger started + LiteLLM callbacks registered at app startup, cleanup at shutdown
- [x] 1.5 Pydantic response models: LLMStatsResponse, LLMStatsData, LLMStatsSummary, TaskTypeStats, DayStats, ErrorStats, LLMStatsMeta

### Task 2: Add Frontend API Client Method
- [ ] 2.1 Add `getLlmStats(period, taskType?)` method to `ApiClient` in `obsidian-canvas-learning/src/services/api-client.ts`
  - Calls `GET /api/v1/system/llm-stats?period={period}&task_type={taskType}`
  - Typed result: `LlmStatsResponse` (camelCase version of backend response)
  - Graceful degradation: yields empty stats structure on network error (NFR-REL-02)
- [ ] 2.2 Add TypeScript interfaces for the response: LlmStatsSummary, TaskTypeStats, DayStats, ErrorStats, LlmStatsData, LlmStatsMeta, LlmStatsResponse

### Task 3: Build Cost Tracker UI Component (Obsidian native)
- [ ] 3.1 Create cost tracker view section in `obsidian-canvas-learning/src/canvas-learning-view.ts` (or a dedicated helper file)
  - Period selector: 4 buttons (Today / Week / Month / All) using Obsidian `createEl()` + CSS classes
  - Summary card: total calls, total tokens, total cost (USD), avg latency, success rate
  - Task breakdown table: per-task-type rows showing calls, tokens, cost
  - DD-06: all DOM via `createEl()`/`createDiv()`, styles in `styles.css`, CSS class prefix `canvas-learning-cost-*`
- [ ] 3.2 Wire period selector to re-fetch data on selection change
  - Use `this.registerDomEvent()` for click handlers (DD-06 memory safety)
  - Map "All" to `period=month` (30 days) or a custom range if full history is desired
- [ ] 3.3 Format cost display: `$0.0000` precision for USD, locale-formatted token counts
- [ ] 3.4 Loading state and error state handling (show "Loading..." / "Backend unreachable" messages)

### Task 4: Add CSS Styles
- [ ] 4.1 Add cost tracker styles to `obsidian-canvas-learning/styles.css`
  - All selectors prefixed with `.canvas-learning-cost-*`
  - Use Obsidian CSS variables: `var(--text-normal)`, `var(--text-muted)`, `var(--background-primary)`, `var(--background-secondary)`, `var(--interactive-accent)`
  - No fixed color values, no `!important`
  - Responsive layout for narrow side panel
  - Task type color indicators using CSS classes (not inline styles)

### Task 5: Integration and Placement
- [ ] 5.1 Add "Usage Statistics" section to the Settings tab or as a dedicated Dashboard tab/section
  - If Settings tab: add a collapsible section below existing settings in `settings.ts`
  - If Dashboard view: add as a section within the canvas learning view
- [ ] 5.2 Auto-refresh: optionally refresh stats when the view becomes visible
- [ ] 5.3 Test with real LLM call data (requires backend running with actual LLM calls logged)

## Dev Notes

### Existing Code Assets — Backend is COMPLETE

The backend infrastructure for this story is **fully implemented** across three files. No backend work is needed.

1. **`backend/app/middleware/cost_tracker.py`** (CostTracker class, ~556 lines)
   - SQLite persistence with two tables: `llm_call_logs` (detail) + `llm_call_logs_daily` (compressed)
   - Full aggregation: `get_stats_by_period()` provides summary, by_task, by_day, errors
   - 90-day log rotation with background task
   - Module-level singleton via `get_cost_tracker()`

2. **`backend/app/middleware/llm_call_logger.py`** (LLMCallLogger class, ~541 lines)
   - LiteLLM callback handler: `on_success()` / `on_failure()` auto-intercept all LLM calls
   - 5 task types: conversation, scoring, extraction, indexing, qa_check
   - 3 error categories: LLM_ERROR, NETWORK_ERROR, CONFIG_ERROR
   - Batch buffer (10 entries or 5s interval) for write optimization
   - API Key filtering (whitelist approach, NFR-SEC-02)

3. **`backend/app/api/v1/system.py`** (GET /api/v1/system/llm-stats endpoint, lines 150-364)
   - Full query parameter support: period (today/week/month/custom), start_date, end_date, task_type
   - Pydantic response models already defined
   - Standard API envelope format: data contains LLMStatsData, meta contains LLMStatsMeta

4. **`backend/app/main.py`** (lines 136-145, 266-270)
   - CostTracker initialized at app startup, LLMCallLogger started, LiteLLM callbacks registered
   - Cleanup on shutdown

**The entire scope of this story is frontend-only**: add an API client method and build the Obsidian UI to display the data the backend already provides.

### API Response Structure (from Pydantic models in system.py)

The `GET /api/v1/system/llm-stats` endpoint provides:
- `data.summary`: total_calls, total_tokens, total_input_tokens, total_output_tokens, total_cost_usd, avg_latency_ms, success_rate
- `data.by_task`: array of objects with task_type, calls, tokens, cost_usd — grouped by the 5 task types
- `data.by_day`: array of objects with date, calls, tokens, cost_usd — for daily breakdown
- `data.errors`: object with total count and by_type map of error categories to counts
- `meta`: period, start_date, end_date, timestamp

### Story 1.10 Dependency

Story 1.10 ("LLM 调用结构化日志基础设施") provides the logging infrastructure this story depends on. It was implemented as Story 7.2 in the codebase (the `cost_tracker.py` and `llm_call_logger.py` files). The dependency is satisfied — the backend is logging all LLM calls to SQLite via LiteLLM callbacks.

### Architecture Compliance

- **FR-QA-04**: Token consumption and cost tracking — this story provides the user-facing display
- **NFR-OBS-04**: Token consumption tracked by task type — already implemented in backend
- Architecture specifies `CostTracker.tsx` in `components/dashboard/` (see architecture.md line 542), but since the Obsidian plugin uses pure TypeScript (no React/Svelte), this will be implemented as a DOM-based component following DD-06 rules

### Obsidian Plugin Constraints (DD-06)

- No UI framework (pure TypeScript + Obsidian API)
- All DOM creation via `containerEl.createEl()` / `createDiv()` — never `document.createElement()`
- All event listeners via `this.registerDomEvent()` — never raw `addEventListener()`
- All styles in `styles.css` with `.canvas-learning-cost-*` prefix
- Colors via CSS variables only — never literal hex/rgb values
- Use the existing ApiClient pattern in `api-client.ts` (currently uses standard `fetch()`)

### Key Libraries

- Backend (already done): `aiosqlite` (SQLite async), `pydantic` (response models), `litellm` (callback system)
- Frontend: Obsidian API (`createEl`, `Setting`, `PluginSettingTab`), standard `fetch()` (via existing ApiClient pattern)

### References

- Backend implementation: `backend/app/middleware/cost_tracker.py`, `backend/app/middleware/llm_call_logger.py`
- API endpoint: `backend/app/api/v1/system.py` (lines 150-364)
- Initialization: `backend/app/main.py` (lines 136-145, 266-270)
- Architecture: `_bmad-output/planning-artifacts/architecture.md` (line 542: CostTracker.tsx)
- Epics: `_bmad-output/planning-artifacts/epics.md` (lines 962-974: Story 3.12 definition)
- Dependency: Story 1.10 / `1-10-llm-structured-logging-infra.md`
- Frontend API client: `obsidian-canvas-learning/src/services/api-client.ts`
- Frontend styles: `obsidian-canvas-learning/styles.css`
- Frontend settings: `obsidian-canvas-learning/src/settings.ts`

## Dev Agent Record

### Agent Model Used
pending

### Debug Log References
pending

### Completion Notes List
pending

### Change Log
pending

### File List
Expected files to modify or create:
- `obsidian-canvas-learning/src/services/api-client.ts` — add `getLlmStats()` method + response interfaces
- `obsidian-canvas-learning/src/canvas-learning-view.ts` (or new helper) — cost tracker UI component
- `obsidian-canvas-learning/styles.css` — `.canvas-learning-cost-*` styles
- `obsidian-canvas-learning/src/settings.ts` — optional: add usage stats section
