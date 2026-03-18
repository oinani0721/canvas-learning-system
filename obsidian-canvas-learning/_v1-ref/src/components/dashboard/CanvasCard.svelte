<script lang="ts">
  /**
   * Canvas Learning System - Canvas Card Component
   * Story 1.4: Dashboard board card (AC-7)
   * Story 5.4: Upgraded with mastery overview + exam entry + exam history (AC-1, AC-4, AC-5)
   *
   * Displays board name, creation time, node count, mastery overview,
   * "Start Exam" button, and collapsible exam history list.
   */

  import type { CanvasBoard, ExamSession } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';
  import { dashboardState } from '../../stores/dashboard-state.svelte';
  import ExamLauncher from './ExamLauncher.svelte';

  interface Props {
    board: CanvasBoard;
    onselect: () => void;
    masteryStats?: { mastered: number; learning: number; weak: number };
    examHistory?: ExamSession[];
  }

  let {
    board,
    onselect,
    masteryStats,
    examHistory,
  }: Props = $props();

  // Node count — loaded asynchronously
  let nodeCount = $state(0);

  $effect(() => {
    canvasState.getNodeCount(board.id).then((count) => {
      nodeCount = count;
    });
  });

  // Exam launcher modal state
  let launcherOpen = $state(false);

  // Exam history collapse state
  let historyExpanded = $state(false);

  function formatDate(iso: string): string {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  function formatShortDate(iso: string): string {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  function handleClick() {
    onselect();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onselect();
    }
  }

  function openLauncher(e: MouseEvent) {
    e.stopPropagation();
    launcherOpen = true;
  }

  function closeLauncher() {
    launcherOpen = false;
  }

  function toggleHistory(e: MouseEvent) {
    e.stopPropagation();
    historyExpanded = !historyExpanded;
  }

  /** Whether the board has enough nodes for exam (AC-4: >= 3). */
  let canStartExam = $derived(nodeCount >= 3);

  /** Tooltip text for disabled exam button. */
  let examTooltip = $derived(
    canStartExam
      ? '开始考察'
      : '至少需要 3 个知识节点才能开始考察',
  );
</script>

<div class="cl-dash-card">
  <div
    class="cl-dash-card-main"
    onclick={handleClick}
    onkeydown={handleKeyDown}
    role="button"
    tabindex="0"
  >
    <div class="cl-dash-card-name">{board.name}</div>
    <div class="cl-dash-card-meta">
      <span class="cl-dash-card-date">{formatDate(board.createdAt)}</span>
      <span class="cl-dash-card-nodes">{nodeCount} 个节点</span>
    </div>

    <!-- Story 5.4: Mastery overview -->
    {#if masteryStats && (masteryStats.mastered > 0 || masteryStats.learning > 0 || masteryStats.weak > 0)}
      <div class="cl-dash-card-mastery">
        {#if masteryStats.mastered > 0}
          <span class="cl-dash-card-mastery-tag cl-dash-card-mastery-tag--mastered">
            {masteryStats.mastered} 掌握
          </span>
        {/if}
        {#if masteryStats.learning > 0}
          <span class="cl-dash-card-mastery-tag cl-dash-card-mastery-tag--learning">
            {masteryStats.learning} 学习中
          </span>
        {/if}
        {#if masteryStats.weak > 0}
          <span class="cl-dash-card-mastery-tag cl-dash-card-mastery-tag--weak">
            {masteryStats.weak} 薄弱
          </span>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Story 5.4: Action row -->
  <div class="cl-dash-card-actions">
    <button
      class="cl-dash-card-exam-btn"
      onclick={openLauncher}
      disabled={!canStartExam || dashboardState.backendOffline}
      title={dashboardState.backendOffline ? '后端服务不可用' : examTooltip}
    >
      开始考察
    </button>

    {#if examHistory && examHistory.length > 0}
      <button
        class="cl-dash-card-history-toggle"
        onclick={toggleHistory}
      >
        {historyExpanded ? '\u25B2' : '\u25BC'} {examHistory.length} 次考察记录
      </button>
    {/if}
  </div>

  <!-- Story 5.4: Collapsible exam history -->
  {#if historyExpanded && examHistory && examHistory.length > 0}
    <div class="cl-dash-card-history">
      {#each examHistory as session}
        <div class="cl-dash-card-history-item">
          <span class="cl-dash-card-history-time">{formatShortDate(session.createdAt)}</span>
          <span class="cl-dash-card-history-nodes">{session.nodesExamined} 节点</span>
          {#if session.masteryChangeSummary}
            <span class="cl-dash-card-history-change">{session.masteryChangeSummary}</span>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Exam launcher modal (Story 6.1: real exam creation) -->
<ExamLauncher
  boardId={board.id}
  boardName={board.name}
  {nodeCount}
  isOpen={launcherOpen}
  onclose={closeLauncher}
/>

<style>
  .cl-dash-card {
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    overflow: hidden;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .cl-dash-card:hover {
    border-color: var(--interactive-accent);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .cl-dash-card-main {
    padding: 12px 14px;
    cursor: pointer;
  }

  .cl-dash-card-main:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: -2px;
  }

  .cl-dash-card-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-normal);
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-dash-card-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--text-muted);
  }

  /* Mastery overview tags */
  .cl-dash-card-mastery {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  .cl-dash-card-mastery-tag {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 500;
  }

  .cl-dash-card-mastery-tag--mastered {
    background: rgba(25, 135, 84, 0.15);
    color: #198754;
  }

  .cl-dash-card-mastery-tag--learning {
    background: rgba(13, 110, 253, 0.15);
    color: #0d6efd;
  }

  .cl-dash-card-mastery-tag--weak {
    background: rgba(220, 53, 69, 0.15);
    color: #dc3545;
  }

  /* Action row */
  .cl-dash-card-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-top: 1px solid var(--background-modifier-border);
  }

  .cl-dash-card-exam-btn {
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: background 0.15s ease, opacity 0.15s ease;
  }

  .cl-dash-card-exam-btn:hover:not(:disabled) {
    background: var(--interactive-accent-hover);
  }

  .cl-dash-card-exam-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .cl-dash-card-history-toggle {
    font-size: 11px;
    color: var(--text-muted);
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 3px;
    transition: background 0.15s ease;
  }

  .cl-dash-card-history-toggle:hover {
    background: var(--background-modifier-hover);
  }

  /* Exam history list */
  .cl-dash-card-history {
    padding: 6px 14px 10px;
    border-top: 1px dotted var(--background-modifier-border);
  }

  .cl-dash-card-history-item {
    display: flex;
    gap: 8px;
    padding: 4px 0;
    font-size: 11px;
    color: var(--text-muted);
  }

  .cl-dash-card-history-time {
    flex-shrink: 0;
  }

  .cl-dash-card-history-nodes {
    flex-shrink: 0;
  }

  .cl-dash-card-history-change {
    flex: 1;
    text-align: right;
    color: var(--text-normal);
  }
</style>
