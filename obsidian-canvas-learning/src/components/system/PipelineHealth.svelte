<script lang="ts">
  /**
   * Canvas Learning System - Pipeline Health Panel
   * Story 7.4: Real-time pipeline health indicators with traffic-light status.
   *
   * Displays 7 health metrics as status lights (green/yellow/red) and
   * an error classification summary across 24h/7d/30d windows.
   *
   * [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
   * [Source: Story 7.4 Task 7]
   */

  import { onMount, onDestroy } from "svelte";

  // ─── Types ────────────────────────────────────────────────────────────

  interface HealthMetric {
    name: string;
    status: string; // "healthy" | "warning" | "critical"
    value: string;
    threshold: string;
    message: string | null;
  }

  interface ErrorCategoryCounts {
    llm_errors: number;
    network_errors: number;
    algorithm_errors: number;
    data_errors: number;
    uncategorized: number;
  }

  interface ErrorAggregation {
    last_24h: ErrorCategoryCounts;
    last_7d: ErrorCategoryCounts;
    last_30d: ErrorCategoryCounts;
  }

  interface PipelineHealthStatus {
    overall: string;
    metrics: HealthMetric[];
    last_updated: string;
    error_summary: ErrorAggregation;
  }

  // ─── Props ────────────────────────────────────────────────────────────

  const { apiBase = "", refreshInterval = 30000 }: { apiBase?: string; refreshInterval?: number } = $props();

  // ─── State ────────────────────────────────────────────────────────────

  let health: PipelineHealthStatus | null = null;
  let loading = false;
  let error: string | null = null;
  let timer: ReturnType<typeof setInterval> | null = null;

  const metricLabels: Record<string, string> = {
    search_channels: "Search Channels",
    config_propagation: "Config Propagation",
    index_consistency: "Index Consistency",
    reranker_status: "Reranker",
    crag_trigger_rate: "CRAG Trigger Rate",
    faithfulness_score: "Faithfulness Score",
    difficulty_match_rate: "Difficulty Match Rate",
  };

  const errorCategoryLabels: Record<string, string> = {
    llm_errors: "LLM",
    network_errors: "Network",
    algorithm_errors: "Algorithm",
    data_errors: "Data",
    uncategorized: "Other",
  };

  // ─── Data Fetching ────────────────────────────────────────────────────

  async function fetchHealth() {
    loading = true;
    error = null;
    try {
      const res = await fetch(`${apiBase}/api/v1/system/pipeline-health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      health = json.data;
    } catch (e: any) {
      error = e.message || "Failed to fetch pipeline health";
    } finally {
      loading = false;
    }
  }

  function getOverallClass(status: string): string {
    if (status === "healthy") return "cl-sys-pipeline-health__overall--healthy";
    if (status === "degraded") return "cl-sys-pipeline-health__overall--degraded";
    return "cl-sys-pipeline-health__overall--critical";
  }

  function getStatusClass(status: string): string {
    if (status === "healthy") return "cl-sys-pipeline-health__light--green";
    if (status === "warning") return "cl-sys-pipeline-health__light--yellow";
    return "cl-sys-pipeline-health__light--red";
  }

  function totalErrors(counts: ErrorCategoryCounts): number {
    return (
      counts.llm_errors +
      counts.network_errors +
      counts.algorithm_errors +
      counts.data_errors +
      counts.uncategorized
    );
  }

  onMount(() => {
    fetchHealth();
    timer = setInterval(fetchHealth, refreshInterval);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<div class="cl-sys-pipeline-health">
  <div class="cl-sys-pipeline-health__header">
    <h4 class="cl-sys-pipeline-health__title">Pipeline Health</h4>
    {#if health}
      <span class="cl-sys-pipeline-health__overall {getOverallClass(health.overall)}">
        {health.overall}
      </span>
    {/if}
  </div>

  {#if error}
    <div class="cl-sys-pipeline-health__error">{error}</div>
  {/if}

  {#if loading && !health}
    <div class="cl-sys-pipeline-health__loading">Loading health data...</div>
  {:else if health}
    <!-- Metrics Grid -->
    <div class="cl-sys-pipeline-health__metrics">
      {#each health.metrics as metric}
        <div class="cl-sys-pipeline-health__metric">
          <div class="cl-sys-pipeline-health__light {getStatusClass(metric.status)}"></div>
          <div class="cl-sys-pipeline-health__metric-info">
            <div class="cl-sys-pipeline-health__metric-name">
              {metricLabels[metric.name] || metric.name}
            </div>
            <div class="cl-sys-pipeline-health__metric-value">{metric.value}</div>
            {#if metric.message}
              <div class="cl-sys-pipeline-health__metric-message">{metric.message}</div>
            {/if}
            <div class="cl-sys-pipeline-health__metric-threshold">
              Threshold: {metric.threshold}
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Error Summary -->
    <div class="cl-sys-pipeline-health__errors">
      <h5 class="cl-sys-pipeline-health__errors-title">Error Summary</h5>
      <table class="cl-sys-pipeline-health__errors-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>24h</th>
            <th>7d</th>
            <th>30d</th>
          </tr>
        </thead>
        <tbody>
          {#each Object.entries(errorCategoryLabels) as [key, label]}
            <tr>
              <td>{label}</td>
              <td>{health.error_summary.last_24h[key] || 0}</td>
              <td>{health.error_summary.last_7d[key] || 0}</td>
              <td>{health.error_summary.last_30d[key] || 0}</td>
            </tr>
          {/each}
          <tr class="cl-sys-pipeline-health__errors-total">
            <td>Total</td>
            <td>{totalErrors(health.error_summary.last_24h)}</td>
            <td>{totalErrors(health.error_summary.last_7d)}</td>
            <td>{totalErrors(health.error_summary.last_30d)}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="cl-sys-pipeline-health__footer">
      Last updated: {new Date(health.last_updated).toLocaleTimeString()}
    </div>
  {/if}
</div>

<style>
  .cl-sys-pipeline-health {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    font-family: var(--font-text, sans-serif);
    color: var(--text-normal);
  }

  .cl-sys-pipeline-health__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cl-sys-pipeline-health__title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }

  .cl-sys-pipeline-health__overall {
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
  }

  .cl-sys-pipeline-health__overall--healthy {
    background: #c6f6d5;
    color: #22543d;
  }

  .cl-sys-pipeline-health__overall--degraded {
    background: #fefcbf;
    color: #744210;
  }

  .cl-sys-pipeline-health__overall--critical {
    background: #fed7d7;
    color: #742a2a;
  }

  .cl-sys-pipeline-health__error {
    padding: 8px 12px;
    border-radius: 4px;
    background: var(--background-modifier-error, #fde8e8);
    color: var(--text-error, #e53e3e);
    font-size: 13px;
  }

  .cl-sys-pipeline-health__loading {
    text-align: center;
    padding: 24px;
    opacity: 0.6;
  }

  /* Metrics Grid */
  .cl-sys-pipeline-health__metrics {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
  }

  .cl-sys-pipeline-health__metric {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px;
    border: 1px solid var(--background-modifier-border, #ddd);
    border-radius: 6px;
  }

  .cl-sys-pipeline-health__light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 3px;
  }

  .cl-sys-pipeline-health__light--green {
    background: #48bb78;
    box-shadow: 0 0 4px #48bb78;
  }

  .cl-sys-pipeline-health__light--yellow {
    background: #ecc94b;
    box-shadow: 0 0 4px #ecc94b;
  }

  .cl-sys-pipeline-health__light--red {
    background: #f56565;
    box-shadow: 0 0 4px #f56565;
  }

  .cl-sys-pipeline-health__metric-info {
    flex: 1;
    min-width: 0;
  }

  .cl-sys-pipeline-health__metric-name {
    font-weight: 600;
    font-size: 13px;
  }

  .cl-sys-pipeline-health__metric-value {
    font-size: 14px;
    margin-top: 2px;
  }

  .cl-sys-pipeline-health__metric-message {
    font-size: 11px;
    color: var(--text-error, #e53e3e);
    margin-top: 2px;
  }

  .cl-sys-pipeline-health__metric-threshold {
    font-size: 10px;
    opacity: 0.5;
    margin-top: 2px;
  }

  /* Error Summary Table */
  .cl-sys-pipeline-health__errors {
    margin-top: 4px;
  }

  .cl-sys-pipeline-health__errors-title {
    margin: 0 0 8px 0;
    font-size: 14px;
    font-weight: 600;
  }

  .cl-sys-pipeline-health__errors-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .cl-sys-pipeline-health__errors-table th,
  .cl-sys-pipeline-health__errors-table td {
    padding: 4px 8px;
    text-align: left;
    border-bottom: 1px solid var(--background-modifier-border, #eee);
  }

  .cl-sys-pipeline-health__errors-table th {
    font-weight: 600;
    opacity: 0.7;
    text-transform: uppercase;
    font-size: 10px;
  }

  .cl-sys-pipeline-health__errors-total td {
    font-weight: 600;
    border-top: 2px solid var(--background-modifier-border, #ccc);
  }

  .cl-sys-pipeline-health__footer {
    font-size: 10px;
    opacity: 0.5;
    text-align: right;
  }
</style>
