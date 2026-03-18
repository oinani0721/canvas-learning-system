<script lang="ts">
  /**
   * Canvas Learning System - ExamLauncher Component
   * Story 5.4: FSRS Review Dashboard (AC-4) — original scaffold
   * Story 6.1: Exam Board Generation (AC-1) — real exam creation
   * Story 6.2: Exam Mode Selection (AC-1, AC-2, AC-3, AC-4) — smart recommendation
   *
   * Exam launch entry point. Renders a modal with exam mode options.
   * Calls backend /api/v1/exam/analyze-canvas for smart mode recommendation,
   * then creates exam session via exam-state store.
   *
   * CSS: cl-dash-launcher-* prefix, Obsidian CSS variables, scoped.
   */

  import { examState, type ExamMode, type ContentAnalysis } from '../../stores/exam-state.svelte';

  interface Props {
    boardId: string;
    boardName: string;
    nodeCount: number;
    isOpen: boolean;
    onclose: () => void;
    onexamcreated?: (examId: string) => void;
  }

  let { boardId = '', boardName, nodeCount, isOpen, onclose, onexamcreated }: Props = $props();

  let selectedMode = $state<ExamMode | null>(null);
  let isCreating = $state(false);
  let analysis = $state<ContentAnalysis | null>(null);
  let analysisLoading = $state(false);
  let createError = $state('');

  const examModes: Array<{ id: ExamMode; name: string; description: string }> = [
    {
      id: 'point_to_point',
      name: '\u70B9\u5BF9\u70B9\u8003\u5BDF',
      description: '\u9010\u4E2A\u8282\u70B9\u6DF1\u5165\u8003\u5BDF\uFF0C\u9002\u5408\u7CBE\u786E\u68C0\u9A8C\u6BCF\u4E2A\u77E5\u8BC6\u70B9',
    },
    {
      id: 'comprehensive',
      name: '\u7EFC\u5408\u9898\u8003\u5BDF',
      description: '\u8DE8\u8282\u70B9\u7EFC\u5408\u51FA\u9898\uFF0C\u68C0\u9A8C\u77E5\u8BC6\u95F4\u7684\u8054\u7CFB\u548C\u5E94\u7528',
    },
    {
      id: 'mixed',
      name: '\u6DF7\u5408\u8003\u5BDF',
      description: '\u7ED3\u5408\u4E24\u79CD\u6A21\u5F0F\uFF0C\u5168\u9762\u8BC4\u4F30\u638C\u63E1\u7A0B\u5EA6',
    },
  ];

  // Analyze canvas when modal opens
  $effect(() => {
    if (isOpen && boardId) {
      loadAnalysis();
    }
  });

  async function loadAnalysis() {
    analysisLoading = true;
    analysis = await examState.analyzeCanvas(boardId);
    analysisLoading = false;

    // Pre-select recommended mode
    if (analysis && !selectedMode) {
      selectedMode = analysis.recommendedMode;
    }
  }

  function selectMode(modeId: ExamMode) {
    selectedMode = modeId;
    createError = '';
  }

  async function startExam() {
    if (!selectedMode || !boardId) return;

    isCreating = true;
    createError = '';

    const examId = await examState.createExam(boardId, selectedMode);

    if (examId) {
      onexamcreated?.(examId);
      handleClose();
    } else {
      createError = examState.errorMessage || '\u521B\u5EFA\u8003\u5BDF\u5931\u8D25';
    }

    isCreating = false;
  }

  function handleClose() {
    selectedMode = null;
    analysis = null;
    createError = '';
    isCreating = false;
    onclose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains('cl-dash-launcher-overlay')) {
      handleClose();
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleClose();
    }
  }

  function isRecommended(modeId: ExamMode): boolean {
    return analysis?.recommendedMode === modeId;
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="cl-dash-launcher-overlay"
    onclick={handleBackdropClick}
    onkeydown={handleKeyDown}
    role="dialog"
    aria-modal="true"
    aria-label="\u9009\u62E9\u8003\u5BDF\u6A21\u5F0F"
  >
    <div class="cl-dash-launcher-modal">
      <div class="cl-dash-launcher-header">
        <h3 class="cl-dash-launcher-title">\u5F00\u59CB\u8003\u5BDF</h3>
        <button class="cl-dash-launcher-close" onclick={handleClose} aria-label="\u5173\u95ED">
          \u2715
        </button>
      </div>

      <div class="cl-dash-launcher-info">
        <span class="cl-dash-launcher-board">{boardName}</span>
        <span class="cl-dash-launcher-count">{nodeCount} \u4E2A\u77E5\u8BC6\u8282\u70B9</span>
      </div>

      {#if createError}
        <div class="cl-dash-launcher-error">{createError}</div>
      {/if}

      <div class="cl-dash-launcher-modes">
        {#each examModes as mode}
          <button
            class="cl-dash-launcher-mode"
            class:cl-dash-launcher-mode--selected={selectedMode === mode.id}
            onclick={() => selectMode(mode.id)}
            disabled={isCreating}
          >
            <div class="cl-dash-launcher-mode-header">
              <span class="cl-dash-launcher-mode-name">{mode.name}</span>
              {#if isRecommended(mode.id)}
                <span class="cl-dash-launcher-mode-badge">\u63A8\u8350</span>
              {/if}
            </div>
            <span class="cl-dash-launcher-mode-desc">{mode.description}</span>
          </button>
        {/each}
      </div>

      <div class="cl-dash-launcher-actions">
        <button
          class="cl-dash-launcher-start-btn"
          onclick={startExam}
          disabled={!selectedMode || isCreating}
        >
          {#if isCreating}
            \u521B\u5EFA\u4E2D...
          {:else}
            \u5F00\u59CB\u8003\u5BDF
          {/if}
        </button>
        <button class="cl-dash-launcher-cancel-btn" onclick={handleClose}>
          \u53D6\u6D88
        </button>
      </div>

      {#if analysisLoading}
        <div class="cl-dash-launcher-tip">\u5206\u6790\u4E2D...</div>
      {:else if analysis}
        <div class="cl-dash-launcher-tip">
          \u5185\u5BB9\u7C7B\u578B\uFF1A{analysis.contentType === 'knowledge' ? '\u77E5\u8BC6\u70B9\u4E3A\u4E3B' : analysis.contentType === 'problem' ? '\u9898\u76EE\u4E3A\u4E3B' : '\u6DF7\u5408\u5185\u5BB9'}
          \u00B7 \u7F6E\u4FE1\u5EA6 {Math.round(analysis.confidence * 100)}%
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .cl-dash-launcher-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .cl-dash-launcher-modal {
    background: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 8px;
    width: 360px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }

  .cl-dash-launcher-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-dash-launcher-title {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-dash-launcher-close {
    background: none;
    border: none;
    font-size: 16px;
    color: var(--text-muted);
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 3px;
    transition: background 0.15s ease;
  }

  .cl-dash-launcher-close:hover {
    background: var(--background-modifier-hover);
    color: var(--text-normal);
  }

  .cl-dash-launcher-info {
    display: flex;
    justify-content: space-between;
    padding: 10px 16px;
    font-size: 12px;
    color: var(--text-muted);
    background: var(--background-secondary);
  }

  .cl-dash-launcher-board {
    font-weight: 500;
    color: var(--text-normal);
  }

  .cl-dash-launcher-error {
    padding: 8px 16px;
    font-size: 12px;
    color: var(--text-error, #dc3545);
    background: rgba(220, 53, 69, 0.08);
  }

  .cl-dash-launcher-modes {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .cl-dash-launcher-mode {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    background: var(--background-secondary);
    border: 2px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .cl-dash-launcher-mode:hover:not(:disabled) {
    border-color: var(--interactive-accent);
    background: var(--background-modifier-hover);
  }

  .cl-dash-launcher-mode--selected {
    border-color: var(--interactive-accent);
    background: rgba(var(--interactive-accent-rgb, 79, 70, 229), 0.08);
  }

  .cl-dash-launcher-mode:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .cl-dash-launcher-mode-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .cl-dash-launcher-mode-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-dash-launcher-mode-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }

  .cl-dash-launcher-mode-desc {
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .cl-dash-launcher-actions {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid var(--background-modifier-border);
  }

  .cl-dash-launcher-start-btn {
    flex: 1;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: background 0.15s ease, opacity 0.15s ease;
  }

  .cl-dash-launcher-start-btn:hover:not(:disabled) {
    background: var(--interactive-accent-hover);
  }

  .cl-dash-launcher-start-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .cl-dash-launcher-cancel-btn {
    padding: 8px 12px;
    font-size: 12px;
    background: none;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    color: var(--text-muted);
    cursor: pointer;
  }

  .cl-dash-launcher-cancel-btn:hover {
    background: var(--background-modifier-hover);
    color: var(--text-normal);
  }

  .cl-dash-launcher-tip {
    padding: 8px 16px;
    font-size: 11px;
    color: var(--text-faint);
    text-align: center;
    border-top: 1px solid var(--background-modifier-border);
  }
</style>
