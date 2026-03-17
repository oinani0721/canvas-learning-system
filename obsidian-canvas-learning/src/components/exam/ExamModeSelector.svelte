<script lang="ts">
  /**
   * Canvas Learning System - ExamModeSelector Component
   * Story 6.2: Exam Mode Selection (AC-1, AC-4)
   *
   * Standalone modal for mode selection, reusable from:
   *   1. Dashboard CanvasCard -> ExamLauncher (full canvas exam)
   *   2. Learning Profile Panel -> single node exam (AC-6)
   *
   * Displays three mode cards with system recommendation badge.
   * CSS: cl-exam-mode-* prefix, Light/Dark theme adaptive.
   */

  import { examState, type ExamMode, type ContentAnalysis } from '../../stores/exam-state.svelte';

  interface Props {
    /** Whether the modal is visible. */
    isOpen: boolean;
    /** Source canvas board ID. */
    canvasId: string;
    /** Optional single-node target (Story 6.2 AC-6). */
    targetNodeId?: string;
    /** Close handler. */
    onclose: () => void;
    /** Callback when mode is confirmed. */
    onconfirm: (mode: ExamMode) => void;
  }

  let {
    isOpen,
    canvasId,
    targetNodeId,
    onclose,
    onconfirm,
  }: Props = $props();

  let selectedMode = $state<ExamMode | null>(null);
  let analysis = $state<ContentAnalysis | null>(null);
  let loading = $state(false);

  const modes: Array<{ id: ExamMode; name: string; desc: string }> = [
    {
      id: 'point_to_point',
      name: '\u70B9\u5BF9\u70B9\u7A81\u7834',
      desc: '\u9010\u77E5\u8BC6\u70B9\u8003\u5BDF\uFF0C\u68C0\u9A8C\u5355\u4E2A\u6982\u5FF5\u7684\u7406\u89E3\u6DF1\u5EA6',
    },
    {
      id: 'comprehensive',
      name: '\u7EFC\u5408\u9898\u8003\u5BDF',
      desc: '\u8DE8\u6982\u5FF5\u6574\u5408\u9898\uFF0C\u68C0\u9A8C\u77E5\u8BC6\u95F4\u7684\u8054\u7CFB\u548C\u5E94\u7528',
    },
    {
      id: 'mixed',
      name: '\u6DF7\u5408\u6A21\u5F0F',
      desc: '\u5148\u70B9\u5BF9\u70B9\u627E\u5F31\u70B9\uFF0C\u518D\u7EFC\u5408\u9898\u9A8C\u8BC1\u6574\u5408\u80FD\u529B',
    },
  ];

  $effect(() => {
    if (isOpen && canvasId) {
      loadAnalysis();
    }
  });

  async function loadAnalysis() {
    loading = true;
    analysis = await examState.analyzeCanvas(canvasId, targetNodeId);
    loading = false;

    if (analysis && !selectedMode) {
      selectedMode = analysis.recommendedMode;
    }
  }

  function handleConfirm() {
    if (selectedMode) {
      onconfirm(selectedMode);
    }
  }

  function handleBackdrop(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains('cl-exam-mode-overlay')) {
      onclose();
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="cl-exam-mode-overlay"
    onclick={handleBackdrop}
    onkeydown={handleKeyDown}
    role="dialog"
    aria-modal="true"
    aria-label="\u9009\u62E9\u8003\u5BDF\u6A21\u5F0F"
  >
    <div class="cl-exam-mode-modal">
      <h3 class="cl-exam-mode-title">\u9009\u62E9\u8003\u5BDF\u6A21\u5F0F</h3>

      <div class="cl-exam-mode-cards">
        {#each modes as mode}
          <button
            class="cl-exam-mode-card"
            class:cl-exam-mode-card--selected={selectedMode === mode.id}
            onclick={() => { selectedMode = mode.id; }}
          >
            <div class="cl-exam-mode-card-header">
              <span class="cl-exam-mode-card-name">{mode.name}</span>
              {#if analysis?.recommendedMode === mode.id}
                <span class="cl-exam-mode-recommend-badge">\u63A8\u8350</span>
              {/if}
            </div>
            <span class="cl-exam-mode-card-desc">{mode.desc}</span>
          </button>
        {/each}
      </div>

      <div class="cl-exam-mode-footer">
        <button
          class="cl-exam-mode-confirm"
          onclick={handleConfirm}
          disabled={!selectedMode}
        >
          \u5F00\u59CB\u8003\u5BDF
        </button>
        <button class="cl-exam-mode-cancel" onclick={onclose}>\u53D6\u6D88</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .cl-exam-mode-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .cl-exam-mode-modal {
    background: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 8px;
    width: 340px;
    max-width: 90vw;
    padding: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .cl-exam-mode-title {
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-exam-mode-cards {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .cl-exam-mode-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    background: var(--background-secondary);
    border: 2px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s ease;
  }

  .cl-exam-mode-card:hover {
    border-color: var(--interactive-accent);
  }

  .cl-exam-mode-card--selected {
    border-color: var(--interactive-accent);
    background: rgba(var(--interactive-accent-rgb, 79, 70, 229), 0.08);
  }

  .cl-exam-mode-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .cl-exam-mode-card-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-exam-mode-recommend-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }

  .cl-exam-mode-card-desc {
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .cl-exam-mode-footer {
    display: flex;
    gap: 8px;
    margin-top: 14px;
  }

  .cl-exam-mode-confirm {
    flex: 1;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
  }

  .cl-exam-mode-confirm:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .cl-exam-mode-cancel {
    padding: 8px 12px;
    font-size: 12px;
    background: none;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    color: var(--text-muted);
    cursor: pointer;
  }
</style>
