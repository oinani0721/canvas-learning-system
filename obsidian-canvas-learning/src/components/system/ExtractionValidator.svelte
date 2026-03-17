<script lang="ts">
  /**
   * Canvas Learning System - Extraction Validator Panel
   * Story 7.4: Human spot-check validation for structured extraction results.
   *
   * Displays extraction records (original text + extracted content) with
   * annotation buttons (correct / incorrect / partial) and per-type statistics.
   *
   * [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
   * [Source: Story 7.4 Task 6]
   */

  import { onMount } from "svelte";

  // ─── Types ────────────────────────────────────────────────────────────

  interface ExtractionRecord {
    id: string;
    source_session_id: string;
    source_node_id: string;
    original_text: string;
    extracted_content: string;
    extraction_type: string;
    extraction_subtype: string | null;
    created_at: string;
    annotation: string | null;
    annotated_at: string | null;
  }

  interface TypeStats {
    total: number;
    correct: number;
    accuracy: number;
  }

  interface ExtractionStats {
    total_records: number;
    annotated_count: number;
    accuracy: number;
    by_type: Record<string, TypeStats>;
  }

  // ─── Props ────────────────────────────────────────────────────────────

  const { apiBase = "" }: { apiBase?: string } = $props();

  // ─── State ────────────────────────────────────────────────────────────

  let records: ExtractionRecord[] = [];
  let stats: ExtractionStats | null = null;
  let totalRecords = 0;
  let currentPage = 1;
  let pageSize = 20;
  let filterType: string = "";
  let loading = false;
  let error: string | null = null;
  let annotatingId: string | null = null;

  const typeLabels: Record<string, string> = {
    error: "Error",
    tip: "Tip",
    key_qa: "Key Q&A",
  };

  // ─── Data Fetching ────────────────────────────────────────────────────

  async function fetchRecords() {
    loading = true;
    error = null;
    try {
      let url = `${apiBase}/api/v1/system/extraction-records?page=${currentPage}&page_size=${pageSize}`;
      if (filterType) {
        url += `&extraction_type=${filterType}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      records = json.data.records || [];
      totalRecords = json.data.total || 0;
    } catch (e: any) {
      error = e.message || "Failed to fetch records";
      records = [];
    } finally {
      loading = false;
    }
  }

  async function fetchStats() {
    try {
      const res = await fetch(`${apiBase}/api/v1/system/qa-metrics`);
      if (!res.ok) return;
      const json = await res.json();
      stats = json.data.extraction_quality || null;
    } catch {
      // Non-critical; stats panel just won't display
    }
  }

  async function submitAnnotation(recordId: string, annotation: string) {
    annotatingId = recordId;
    try {
      const res = await fetch(
        `${apiBase}/api/v1/system/extraction-records/${recordId}/annotate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ annotation }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Update local state
      const idx = records.findIndex((r) => r.id === recordId);
      if (idx >= 0) {
        records[idx] = {
          ...records[idx],
          annotation,
          annotated_at: new Date().toISOString(),
        };
        records = [...records]; // trigger reactivity
      }
      await fetchStats();
    } catch (e: any) {
      error = `Annotation failed: ${e.message}`;
    } finally {
      annotatingId = null;
    }
  }

  function setFilter(type: string) {
    filterType = type;
    currentPage = 1;
    fetchRecords();
  }

  function nextPage() {
    if (currentPage * pageSize < totalRecords) {
      currentPage++;
      fetchRecords();
    }
  }

  function prevPage() {
    if (currentPage > 1) {
      currentPage--;
      fetchRecords();
    }
  }

  onMount(() => {
    fetchRecords();
    fetchStats();
  });
</script>

<div class="cl-sys-extraction-validator">
  <!-- Stats Overview -->
  {#if stats}
    <div class="cl-sys-extraction-validator__stats">
      <div class="cl-sys-extraction-validator__stat-card">
        <span class="cl-sys-extraction-validator__stat-label">Total</span>
        <span class="cl-sys-extraction-validator__stat-value">{stats.total_records}</span>
      </div>
      <div class="cl-sys-extraction-validator__stat-card">
        <span class="cl-sys-extraction-validator__stat-label">Annotated</span>
        <span class="cl-sys-extraction-validator__stat-value">{stats.annotated_count}</span>
      </div>
      <div class="cl-sys-extraction-validator__stat-card">
        <span class="cl-sys-extraction-validator__stat-label">Accuracy</span>
        <span
          class="cl-sys-extraction-validator__stat-value"
          class:cl-sys-extraction-validator__stat-value--warning={stats.accuracy < 0.8}
        >
          {(stats.accuracy * 100).toFixed(1)}%
        </span>
      </div>
      {#each Object.entries(stats.by_type) as [type, typeStat]}
        <div class="cl-sys-extraction-validator__stat-card">
          <span class="cl-sys-extraction-validator__stat-label">{typeLabels[type] || type}</span>
          <span class="cl-sys-extraction-validator__stat-value">
            {(typeStat.accuracy * 100).toFixed(1)}%
          </span>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Filters -->
  <div class="cl-sys-extraction-validator__filters">
    <button
      class="cl-sys-extraction-validator__filter-btn"
      class:cl-sys-extraction-validator__filter-btn--active={filterType === ""}
      on:click={() => setFilter("")}
    >All</button>
    <button
      class="cl-sys-extraction-validator__filter-btn"
      class:cl-sys-extraction-validator__filter-btn--active={filterType === "error"}
      on:click={() => setFilter("error")}
    >Errors</button>
    <button
      class="cl-sys-extraction-validator__filter-btn"
      class:cl-sys-extraction-validator__filter-btn--active={filterType === "tip"}
      on:click={() => setFilter("tip")}
    >Tips</button>
    <button
      class="cl-sys-extraction-validator__filter-btn"
      class:cl-sys-extraction-validator__filter-btn--active={filterType === "key_qa"}
      on:click={() => setFilter("key_qa")}
    >Key Q&A</button>
  </div>

  <!-- Error Banner -->
  {#if error}
    <div class="cl-sys-extraction-validator__error">{error}</div>
  {/if}

  <!-- Loading -->
  {#if loading}
    <div class="cl-sys-extraction-validator__loading">Loading...</div>
  {:else if records.length === 0}
    <div class="cl-sys-extraction-validator__empty">No extraction records found.</div>
  {:else}
    <!-- Records List -->
    <div class="cl-sys-extraction-validator__list">
      {#each records as record (record.id)}
        <div class="cl-sys-extraction-validator__record">
          <div class="cl-sys-extraction-validator__record-header">
            <span class="cl-sys-extraction-validator__record-type">
              {typeLabels[record.extraction_type] || record.extraction_type}
              {#if record.extraction_subtype}
                <span class="cl-sys-extraction-validator__record-subtype">
                  ({record.extraction_subtype})
                </span>
              {/if}
            </span>
            <span class="cl-sys-extraction-validator__record-date">
              {new Date(record.created_at).toLocaleDateString()}
            </span>
          </div>

          <div class="cl-sys-extraction-validator__record-body">
            <div class="cl-sys-extraction-validator__record-original">
              <div class="cl-sys-extraction-validator__record-label">Original</div>
              <div class="cl-sys-extraction-validator__record-text">{record.original_text}</div>
            </div>
            <div class="cl-sys-extraction-validator__record-extracted">
              <div class="cl-sys-extraction-validator__record-label">Extracted</div>
              <div class="cl-sys-extraction-validator__record-text">{record.extracted_content}</div>
            </div>
          </div>

          <div class="cl-sys-extraction-validator__record-actions">
            {#if record.annotation}
              <span
                class="cl-sys-extraction-validator__annotation-badge"
                class:cl-sys-extraction-validator__annotation-badge--correct={record.annotation === "correct"}
                class:cl-sys-extraction-validator__annotation-badge--incorrect={record.annotation === "incorrect"}
                class:cl-sys-extraction-validator__annotation-badge--partial={record.annotation === "partial"}
              >
                {record.annotation}
              </span>
            {:else}
              <button
                class="cl-sys-extraction-validator__action-btn cl-sys-extraction-validator__action-btn--correct"
                disabled={annotatingId === record.id}
                on:click={() => submitAnnotation(record.id, "correct")}
              >Correct</button>
              <button
                class="cl-sys-extraction-validator__action-btn cl-sys-extraction-validator__action-btn--incorrect"
                disabled={annotatingId === record.id}
                on:click={() => submitAnnotation(record.id, "incorrect")}
              >Incorrect</button>
              <button
                class="cl-sys-extraction-validator__action-btn cl-sys-extraction-validator__action-btn--partial"
                disabled={annotatingId === record.id}
                on:click={() => submitAnnotation(record.id, "partial")}
              >Partial</button>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Pagination -->
    <div class="cl-sys-extraction-validator__pagination">
      <button
        class="cl-sys-extraction-validator__page-btn"
        disabled={currentPage <= 1}
        on:click={prevPage}
      >Prev</button>
      <span class="cl-sys-extraction-validator__page-info">
        Page {currentPage} / {Math.ceil(totalRecords / pageSize) || 1}
      </span>
      <button
        class="cl-sys-extraction-validator__page-btn"
        disabled={currentPage * pageSize >= totalRecords}
        on:click={nextPage}
      >Next</button>
    </div>
  {/if}
</div>

<style>
  .cl-sys-extraction-validator {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    font-family: var(--font-text, sans-serif);
    color: var(--text-normal);
  }

  /* Stats */
  .cl-sys-extraction-validator__stats {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .cl-sys-extraction-validator__stat-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 16px;
    border-radius: 6px;
    background: var(--background-secondary, #f5f5f5);
    min-width: 80px;
  }

  .cl-sys-extraction-validator__stat-label {
    font-size: 11px;
    opacity: 0.7;
    text-transform: uppercase;
  }

  .cl-sys-extraction-validator__stat-value {
    font-size: 18px;
    font-weight: 600;
  }

  .cl-sys-extraction-validator__stat-value--warning {
    color: var(--text-error, #e53e3e);
  }

  /* Filters */
  .cl-sys-extraction-validator__filters {
    display: flex;
    gap: 6px;
  }

  .cl-sys-extraction-validator__filter-btn {
    padding: 4px 12px;
    border: 1px solid var(--background-modifier-border, #ddd);
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 12px;
    color: var(--text-muted);
  }

  .cl-sys-extraction-validator__filter-btn--active {
    background: var(--interactive-accent, #7c3aed);
    color: var(--text-on-accent, #fff);
    border-color: var(--interactive-accent, #7c3aed);
  }

  /* Error */
  .cl-sys-extraction-validator__error {
    padding: 8px 12px;
    border-radius: 4px;
    background: var(--background-modifier-error, #fde8e8);
    color: var(--text-error, #e53e3e);
    font-size: 13px;
  }

  .cl-sys-extraction-validator__loading,
  .cl-sys-extraction-validator__empty {
    text-align: center;
    padding: 24px;
    opacity: 0.6;
  }

  /* Records List */
  .cl-sys-extraction-validator__list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .cl-sys-extraction-validator__record {
    border: 1px solid var(--background-modifier-border, #ddd);
    border-radius: 6px;
    padding: 12px;
  }

  .cl-sys-extraction-validator__record-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .cl-sys-extraction-validator__record-type {
    font-weight: 600;
    font-size: 13px;
  }

  .cl-sys-extraction-validator__record-subtype {
    font-weight: 400;
    opacity: 0.7;
  }

  .cl-sys-extraction-validator__record-date {
    font-size: 11px;
    opacity: 0.6;
  }

  .cl-sys-extraction-validator__record-body {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 8px;
  }

  .cl-sys-extraction-validator__record-label {
    font-size: 10px;
    text-transform: uppercase;
    opacity: 0.5;
    margin-bottom: 4px;
  }

  .cl-sys-extraction-validator__record-text {
    font-size: 13px;
    line-height: 1.4;
    white-space: pre-wrap;
    max-height: 120px;
    overflow-y: auto;
  }

  .cl-sys-extraction-validator__record-original {
    padding-right: 8px;
    border-right: 1px solid var(--background-modifier-border, #ddd);
  }

  /* Actions */
  .cl-sys-extraction-validator__record-actions {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .cl-sys-extraction-validator__action-btn {
    padding: 3px 10px;
    border: 1px solid var(--background-modifier-border, #ddd);
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 12px;
  }

  .cl-sys-extraction-validator__action-btn--correct {
    color: #38a169;
    border-color: #38a169;
  }

  .cl-sys-extraction-validator__action-btn--incorrect {
    color: #e53e3e;
    border-color: #e53e3e;
  }

  .cl-sys-extraction-validator__action-btn--partial {
    color: #d69e2e;
    border-color: #d69e2e;
  }

  .cl-sys-extraction-validator__action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .cl-sys-extraction-validator__annotation-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    text-transform: capitalize;
  }

  .cl-sys-extraction-validator__annotation-badge--correct {
    background: #c6f6d5;
    color: #22543d;
  }

  .cl-sys-extraction-validator__annotation-badge--incorrect {
    background: #fed7d7;
    color: #742a2a;
  }

  .cl-sys-extraction-validator__annotation-badge--partial {
    background: #fefcbf;
    color: #744210;
  }

  /* Pagination */
  .cl-sys-extraction-validator__pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding-top: 8px;
  }

  .cl-sys-extraction-validator__page-btn {
    padding: 4px 12px;
    border: 1px solid var(--background-modifier-border, #ddd);
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 12px;
  }

  .cl-sys-extraction-validator__page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .cl-sys-extraction-validator__page-info {
    font-size: 12px;
    opacity: 0.7;
  }
</style>
